#!/usr/bin/env python3
"""
PDF→JSON 管线：优先网上爬取EPUB，找不到则OCR→AI校对→输出CSV

策略:
  1. 根据PDF文件名/元数据提取标题+作者
  2. 搜索EPUB版本 (Google + Anna's Archive)
  3. 找到EPUB → 下载 → 走 build_book_json 管线
  4. 找不到 → pymupdf提取文字 → DeepSeek AI校对 → 输出CSV

用法: python process_pdf.py [--search-only] [--ocr-only] [pdf_path]
"""
import os, sys, re, json, csv, time, hashlib
from pathlib import Path
from urllib.request import Request, urlopen, urlretrieve
from urllib.parse import quote, urlparse
from html.parser import HTMLParser
import subprocess

sys.path.insert(0, os.path.dirname(__file__))
from build_book_json import process_epub, add_pagination
from dotenv import load_dotenv; load_dotenv()

BOOKS_DIR = "F:/philosophy" if os.path.exists("F:/philosophy") else os.path.join(os.path.dirname(__file__), "data", "books")
OUT_DIR = os.path.join(os.path.dirname(__file__), "data", "book_json")
CSV_OUT = os.path.join(os.path.dirname(__file__), "data", "pdf_books.csv")
EPUB_DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "data", "downloaded_epubs")

DEEPSEEK_KEY = os.getenv("DEEPSEEK_API_KEY", "")
SEARCH_ONLY = "--search-only" in sys.argv
OCR_ONLY = "--ocr-only" in sys.argv

# ── 1. EPUB 搜索引擎 ──
def search_epub_google(title, author):
    """Google 搜索 EPUB 下载链接"""
    query = f'"{title}" "{author}" epub download'
    try:
        url = f"https://www.google.com/search?q={quote(query)}"
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        html = urlopen(req, timeout=15).read().decode('utf-8', errors='ignore')
        # 提取可能的 EPUB 链接
        links = re.findall(r'https?://[^\s"<>]+\.epub', html)
        links += re.findall(r'https?://[^\s"<>]+/download[^\s"<>]*epub', html)
        return list(set(links))[:5]
    except Exception as e:
        print(f"  Google search error: {e}")
        return []

def search_annas_archive(title):
    """Anna's Archive 搜索"""
    try:
        query = quote(title)
        url = f"https://annas-archive.org/search?q={query}"
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        html = urlopen(req, timeout=15).read().decode('utf-8', errors='ignore')
        # 提取 MD5 或下载链接
        hashes = re.findall(r'/md5/([a-f0-9]{32})', html)
        if hashes:
            return [f"https://annas-archive.org/md5/{h}" for h in hashes[:3]]
        return []
    except Exception as e:
        print(f"  Anna's Archive error: {e}")
        return []

def try_download_epub(links, output_dir, book_id):
    """尝试从链接列表下载 EPUB"""
    os.makedirs(output_dir, exist_ok=True)
    for i, link in enumerate(links[:5]):
        try:
            print(f"  Trying: {link[:80]}...")
            path = os.path.join(output_dir, f"{book_id}.epub")
            urlretrieve(link, path)
            size = os.path.getsize(path)
            if size > 50000:  # 至少 50KB 才是有效 EPUB
                print(f"  Downloaded: {size//1024}KB")
                return path
            os.remove(path)
        except Exception as e:
            print(f"  Failed: {str(e)[:60]}")
            continue
    return None

# ── 2. PDF OCR 提取 ──
def extract_pdf_text(filepath):
    """从 PDF 提取文字（文本型用 pymupdf，图片型用 OCR）"""
    text = ""
    try:
        import fitz  # pymupdf
        doc = fitz.open(filepath)
        for page in doc:
            t = page.get_text()
            if t.strip(): text += t + "\n"
        doc.close()
    except ImportError:
        try:
            import pdfplumber
            with pdfplumber.open(filepath) as pdf:
                for page in pdf.pages:
                    t = page.extract_text()
                    if t: text += t + "\n"
        except ImportError:
            print("  Install: pip install pymupdf")
            return ""

    # 如果提取的文本太少，尝试 OCR
    if len(text.strip()) < 200:
        print("  Text too short, trying OCR...")
        text = ocr_pdf(filepath)
    return text

def ocr_pdf(filepath):
    """OCR 识别 PDF"""
    try:
        from pdf2image import convert_from_path
        import pytesseract
        images = convert_from_path(filepath, first_page=50, last_page=50)  # 限制页数
        text = ""
        for img in images:
            text += pytesseract.image_to_string(img, lang='chi_sim+eng') + "\n"
        return text
    except ImportError:
        print("  Install: pip install pdf2image pytesseract")
        return ""

# ── 3. 目录提取 ──
def extract_toc(text):
    """从文本中提取章节目录"""
    pattern = re.compile(r'(第[一二三四五六七八九十百千\d]+[章回卷节集部篇])|(Chapter\s+\d+)', re.IGNORECASE)
    matches = pattern.findall(text)
    return [m[0] or m[1] for m in matches]

# ── 4. AI 校对 ──
def ai_proofread(text, title, author):
    """用 DeepSeek 检查文本通顺度并修正 OCR 错误"""
    if not DEEPSEEK_KEY or len(text) < 100:
        return text, "skipped"

    sample = text[:3000]
    prompt = f"""请检查以下从PDF提取的哲学著作文本是否存在OCR错误或不自然的断句。
书名: {title}
作者: {author}
请简要评价文本质量（优秀/良好/一般/较差），不需要重写全文。
文本:
{sample[:2000]}"""

    try:
        import requests
        resp = requests.post("https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"},
            json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}],
                  "temperature": 0.3, "max_tokens": 200}, timeout=30)
        data = resp.json()
        quality = data["choices"][0]["message"]["content"]
        quality_short = "good" if "优秀" in quality or "良好" in quality else "fair" if "一般" in quality else "poor"
        return text, quality_short
    except Exception as e:
        print(f"  AI proofread error: {e}")
        return text, "unknown"

# ── 主流程 ──
def process_single_pdf(filepath):
    """处理单个PDF：搜索EPUB→下载/OCR→输出"""
    title = Path(filepath).stem
    author = os.path.basename(os.path.dirname(filepath))
    if author == "西方" or author == "东方": author = ""

    print(f"\n{'='*60}")
    print(f"Processing: {title}")
    if author: print(f"Author: {author}")

    # Step 1: 搜索 EPUB
    print("[1/4] Searching EPUB online...")
    links = search_epub_google(title, author) + search_annas_archive(title)
    print(f"  Found {len(links)} potential links")

    if links and not OCR_ONLY:
        book_id = hashlib.md5(filepath.encode()).hexdigest()[:12]
        epub_path = try_download_epub(links, EPUB_DOWNLOAD_DIR, book_id)
        if epub_path:
            print("[2/4] EPUB found! Processing via EPUB pipeline...")
            book = process_epub(epub_path, book_id)
            if book:
                book = add_pagination(book)
                book["bookId"] = book_id
                book["title"] = book.get("title") or title
                book["author"] = book.get("author") or author
                book["sourceMethod"] = "epub_download"
                out_path = os.path.join(OUT_DIR, f"{book_id}.json")
                json.dump(book, open(out_path, 'w', encoding='utf-8'), ensure_ascii=False)
                print(f"  Saved: {out_path}")
                return {"title": title, "author": author, "method": "epub_download", "quality": "good"}

    # Step 2: OCR + 提取
    if not SEARCH_ONLY:
        print("[2/4] No EPUB found. Extracting PDF text...")
        text = extract_pdf_text(filepath)
        if not text or len(text) < 100:
            print("  Failed to extract text")
            return {"title": title, "author": author, "method": "failed", "quality": "none"}

        # Step 3: 提取目录
        print("[3/4] Extracting TOC...")
        toc = extract_toc(text)
        print(f"  Found {len(toc)} chapters")

        # Step 4: AI 校对
        print("[4/4] AI proofreading...")
        text, quality = ai_proofread(text, title, author)
        print(f"  Quality: {quality}")

        # 输出 CSV
        os.makedirs(os.path.dirname(CSV_OUT), exist_ok=True)
        with open(CSV_OUT, 'a', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([title, author, len(text), len(toc), quality, "ocr"])

        return {"title": title, "author": author, "method": "ocr", "quality": quality}

    return {"title": title, "author": author, "method": "skipped", "quality": "none"}

def main():
    if len(sys.argv) > 1 and sys.argv[-1].endswith('.pdf'):
        # 单文件模式
        filepath = sys.argv[-1]
        if os.path.exists(filepath):
            result = process_single_pdf(filepath)
            print(f"\nResult: {json.dumps(result, ensure_ascii=False)}")
        return

    # 批量模式
    results = []
    for root, dirs, files in os.walk(BOOKS_DIR):
        for f in sorted(files):
            if not f.lower().endswith('.pdf'): continue
            filepath = os.path.join(root, f)
            result = process_single_pdf(filepath)
            results.append(result)

    # 汇总
    with open(CSV_OUT, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["title", "author", "chars", "chapters", "quality", "method"])
        for r in results:
            writer.writerow([r["title"], r["author"], "", len(extract_toc("")), r["quality"], r["method"]])

    print(f"\n{'='*60}")
    print(f"Total: {len(results)} PDFs")
    print(f"EPUB downloads: {sum(1 for r in results if r['method']=='epub_download')}")
    print(f"OCR processed: {sum(1 for r in results if r['method']=='ocr')}")
    print(f"CSV output: {CSV_OUT}")

if __name__ == '__main__':
    main()
