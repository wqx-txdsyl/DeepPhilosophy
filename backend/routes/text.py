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
async def get_book_text(book_id: str, meta: str = "", chapter: str = ""):
    """获取预构建的书籍JSON。?meta=1 仅返回元数据(快速), ?chapter=N 仅返回第N章"""
    import urllib.request

    # 加载完整 JSON
    data = None
    if config.USE_OSS:
        oss_url = f"https://{config.OSS_BUCKET_HOST}/book_json/{book_id}.json"
        try:
            req = urllib.request.Request(oss_url)
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode('utf-8'))
        except: pass
    if not data:
        json_dir = os.path.join(os.path.dirname(__file__), "..", "data", "book_json")
        json_path = os.path.join(json_dir, f"{book_id}.json")
        if os.path.exists(json_path) and os.path.getsize(json_path) > 100:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
    if not data:
        raise HTTPException(status_code=404, detail="书籍数据未找到")

    # ?meta=1 → 仅返回元数据（快速加载，<5KB）
    if meta == "1":
        return {
            "bookId": data.get("bookId", book_id),
            "title": data.get("title", ""),
            "author": data.get("author", ""),
            "cover": data.get("cover"),
            "toc": data.get("toc", []),
            "totalChars": data.get("totalChars", 0),
            "estimatedPages": data.get("estimatedPages", 0),
            "chapterCount": len(data.get("chapters", [])),
            "chapterTitles": [c.get("title", "") for c in data.get("chapters", [])],
        }

    # ?chapter=N → 仅返回第 N 章
    if chapter:
        try:
            idx = int(chapter)
            chs = data.get("chapters", [])
            if 0 <= idx < len(chs):
                return {"chapter": chs[idx], "index": idx, "totalChapters": len(chs)}
            raise HTTPException(status_code=404, detail="章节不存在")
        except ValueError:
            pass

    return data

    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(CACHE_DIR, f"{book_id}.json")

    # 读旧缓存
    if os.path.exists(cache_path) and os.path.getsize(cache_path) > 100:
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


@router.get("/api/books/{book_id}/image/{img_name}")
async def get_book_image(book_id: str, img_name: str):
    """提供从 EPUB 提取的图片（本地缓存或从 OSS 代理）"""
    # 1. 本地提取的图片
    img_dir = os.path.join(os.path.dirname(__file__), "..", "data", "book_images")
    local_path = os.path.join(img_dir, img_name)
    if os.path.exists(local_path):
        ext = Path(img_name).suffix.lower()
        mime = IMG_EXTS.get(ext, 'image/png')
        return FileResponse(local_path, media_type=mime)

    # 2. OSS 代理
    if config.USE_OSS:
        import urllib.request
        oss_url = f"https://{config.OSS_BUCKET_HOST}/book_images/{img_name}"
        try:
            req = urllib.request.Request(oss_url)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = resp.read()
            ext = Path(img_name).suffix.lower()
            mime = IMG_EXTS.get(ext, 'image/png')
            # 缓存到本地
            os.makedirs(img_dir, exist_ok=True)
            with open(local_path, 'wb') as f: f.write(data)
            return Response(content=data, media_type=mime)
        except: pass

    raise HTTPException(status_code=404, detail="图片未找到")
