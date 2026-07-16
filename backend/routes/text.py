"""文本提取 API — 借鉴番茄小说：提取纯文本 + 章节索引 + 字符偏移"""
import os, json, re, zipfile
from pathlib import Path
from html.parser import HTMLParser
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import config

router = APIRouter()

CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "book_text")
TXT_BOOKS_DIR = os.path.join(config.KNOWLEDGE_DIR, "..", "books") if os.path.exists(config.KNOWLEDGE_DIR) else config.KNOWLEDGE_DIR

class TextExtractor(HTMLParser):
    """从 HTML 提取纯文本（跳过 script/style/nav）"""
    def __init__(self):
        super().__init__()
        self.text = []
        self.skip = False
    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'head', 'nav'): self.skip = True
    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'head', 'nav'): self.skip = False
    def handle_data(self, data):
        if not self.skip and data.strip(): self.text.append(data.strip())


def extract_epub_text(filepath):
    """从 EPUB 提取全文文本 + 章节索引"""
    chapters = []
    full_text = ""
    try:
        with zipfile.ZipFile(filepath) as z:
            # 读取 spine/container 获取阅读顺序
            content_files = [n for n in z.namelist() if n.endswith(('.xhtml', '.html', '.htm')) and '/nav' not in n.lower()]
            content_files.sort()
            for name in content_files:
                try:
                    html = z.read(name).decode('utf-8', errors='ignore')
                    parser = TextExtractor()
                    parser.feed(html)
                    text = ' '.join(parser.text)
                    if len(text) > 20:
                        # 尝试提取章节标题（第一个有效文本行）
                        title = Path(name).stem.replace('_', ' ').replace('-', ' ')
                        chapters.append({"title": title, "text": text})
                        full_text += text + '\n\n'
                except: pass
    except Exception as e:
        return None, str(e)
    return chapters, full_text


def extract_txt_text(filepath):
    """从 TXT 提取文本 + 正则分章"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
    except:
        try:
            with open(filepath, 'r', encoding='gbk', errors='ignore') as f:
                text = f.read()
        except Exception as e:
            return None, str(e)

    # 正则分章
    chapters = []
    pattern = re.compile(r'(^第[一二三四五六七八九十百千\d]+[章回卷节集幕部篇])', re.MULTILINE)
    parts = pattern.split(text)
    if len(parts) > 1:
        current_title = "前言"
        current_text = parts[0] if parts[0].strip() else ""
        for i in range(1, len(parts), 2):
            if i + 1 < len(parts):
                current_text += parts[i] + parts[i + 1]
            chapters.append({"title": current_title.strip(), "text": current_text.strip()})
            if i + 2 < len(parts):
                current_title = parts[i + 2] if i + 2 < len(parts) else ""
                current_text = ""
    else:
        chapters.append({"title": "正文", "text": text.strip()})
    return chapters, text


@router.get("/api/books/{book_id}/text")
async def get_book_text(book_id: str):
    """获取书籍纯文本 + 章节索引（缓存 1 小时）"""
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, f"{book_id}.json")

    # 读缓存
    if os.path.exists(cache_path):
        with open(cache_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    # 从书籍列表获取路径
    from main import scan_books
    books = scan_books()
    book = next((b for b in books if b["id"] == book_id), None)
    if not book:
        # 尝试直接查文件系统
        for root, dirs, files in os.walk(config.KNOWLEDGE_DIR):
            for f in files:
                ext = Path(f).suffix.lower()
                if ext in ('.epub', '.pdf', '.txt'):
                    bid = __import__('hashlib').md5(os.path.relpath(os.path.join(root, f), config.KNOWLEDGE_DIR).encode()).hexdigest()[:12]
                    if bid == book_id:
                        book = {"path": os.path.relpath(os.path.join(root, f), config.KNOWLEDGE_DIR), "file_type": ext.replace('.', ''), "title": Path(f).stem, "author": ""}
                        break

    if not book:
        raise HTTPException(status_code=404, detail="书籍未找到")

    filepath = os.path.join(config.KNOWLEDGE_DIR, book["path"]) if "path" in book else None
    if not filepath or not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="文件不存在")

    ext = Path(filepath).suffix.lower()
    if ext == '.epub':
        chapters, full_text = extract_epub_text(filepath)
    elif ext == '.txt':
        chapters, full_text = extract_txt_text(filepath)
    elif ext == '.pdf':
        raise HTTPException(status_code=400, detail="PDF 请使用原有阅读器")
    else:
        raise HTTPException(status_code=400, detail=f"不支持格式: {ext}")

    if not chapters:
        raise HTTPException(status_code=500, detail="文本提取失败")

    result = {
        "bookId": book_id,
        "title": book.get("title", ""),
        "author": book.get("author", ""),
        "chapters": chapters,
        "totalChars": len(full_text),
    }

    # 写缓存
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False)

    return result
