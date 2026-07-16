#!/usr/bin/env python3
"""
将每本 EPUB/TXT 转化为结构化 JSON：
  文本 + 目录 + 封面 + 内嵌图片(Base64) + 分页断点
存到 data/book_json/ → 上传 GitHub/OSS → 前端直读
用法: python build_book_json.py [--force]
"""
import os, sys, json, re, zipfile, base64, io, hashlib
from pathlib import Path
from html.parser import HTMLParser
from bs4 import BeautifulSoup  # pip install beautifulsoup4

BOOKS_DIR = "F:/philosophy" if os.path.exists("F:/philosophy") else os.path.join(os.path.dirname(__file__), "data", "books")
OUT_DIR = os.path.join(os.path.dirname(__file__), "data", "book_json")
CHARS_PER_PAGE = 1200  # 标准阅读页
FORCE = "--force" in sys.argv

# ── 图片类型检测 ──
IMG_EXTS = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif', '.webp': 'image/webp', '.svg': 'image/svg+xml', '.bmp': 'image/bmp'}

def is_image(name):
    return Path(name).suffix.lower() in IMG_EXTS

def img_to_base64(data, name):
    """图片字节 → data:image/xxx;base64,..."""
    ext = Path(name).suffix.lower()
    mime = IMG_EXTS.get(ext, 'image/png')
    b64 = base64.b64encode(data).decode()
    return f"data:{mime};base64,{b64}"


# ── EPUB 处理 ──
def process_epub(filepath):
    """从 EPUB 提取：封面、目录、章节(文本+图片)"""
    book = {"type": "epub", "chapters": [], "toc": [], "cover": None, "images": {}}
    try:
        with zipfile.ZipFile(filepath) as z:
            namelist = z.namelist()

            # 1. 收集所有图片（用文件名做 key）
            for name in namelist:
                if is_image(name) and '__MACOSX' not in name:
                    try:
                        data = z.read(name)
                        # 缩短 key 为文件名
                        key = Path(name).name
                        book["images"][key] = img_to_base64(data, name)
                    except: pass

            # 2. 找封面
            # 常见封面文件: cover.jpg, cover.png, 或以 cover 开头的图片
            for name in namelist:
                bn = Path(name).name.lower()
                if is_image(name) and ('cover' in bn or 'titlepage' in bn or 'front' in bn):
                    if bn in book["images"]:
                        book["cover"] = book["images"][bn]
                        break
            if not book["cover"] and book["images"]:
                book["cover"] = list(book["images"].values())[0]  # 第一个图片当封面

            # 3. 找 OPF 获取 spine 阅读顺序
            container_xml = None
            for name in namelist:
                if name.endswith('container.xml'):
                    container_xml = z.read(name).decode('utf-8', errors='ignore')
                    break
            rootfile = "content.opf"
            if container_xml:
                m = re.search(r'full-path="([^"]+)"', container_xml)
                if m: rootfile = m.group(1)

            # 4. 读 OPF 获取 spine + toc + metadata
            spine_items = []
            if rootfile in namelist:
                try:
                    opf = z.read(rootfile).decode('utf-8', errors='ignore')
                    soup = BeautifulSoup(opf, 'xml')
                    # metadata
                    title_tag = soup.find('dc:title')
                    if title_tag: book['title'] = title_tag.text.strip()
                    creator_tag = soup.find('dc:creator')
                    if creator_tag: book['author'] = creator_tag.text.strip()
                    # spine
                    for itemref in soup.find_all('itemref'):
                        idref = itemref.get('idref', '')
                        # find matching item
                        item = soup.find('item', id=idref)
                        if item:
                            href = item.get('href', '')
                            mtype = item.get('media-type', '')
                            spine_items.append({"id": idref, "href": href, "type": mtype})
                    # TOC (NCX)
                    ncx_href = None
                    for item in soup.find_all('item'):
                        if item.get('media-type') == 'application/x-dtbncx+xml':
                            ncx_href = item.get('href')
                    if ncx_href:
                        opf_dir = os.path.dirname(rootfile)
                        ncx_path = os.path.join(opf_dir, ncx_href) if opf_dir else ncx_href
                        ncx_path = ncx_path.replace('\\', '/')
                        if ncx_path in namelist:
                            try:
                                ncx = z.read(ncx_path).decode('utf-8', errors='ignore')
                                ncx_soup = BeautifulSoup(ncx, 'xml')
                                for nav in ncx_soup.find_all('navPoint'):
                                    label = nav.find('navLabel')
                                    content = nav.find('content')
                                    if label and content:
                                        book["toc"].append({
                                            "title": label.text.strip(),
                                            "src": content.get('src', ''),
                                        })
                            except: pass
                except Exception as e:
                    print(f"  ⚠ OPF parse error: {e}")

            # 5. 遍历 spine 提取章节内容
            opf_dir = os.path.dirname(rootfile) if '/' in rootfile or '\\' in rootfile else ''
            for si in spine_items:
                href = si['href']
                # 解析相对路径
                full_href = os.path.join(opf_dir, href).replace('\\', '/') if opf_dir else href
                if full_href not in namelist:
                    # 尝试只匹配文件名
                    candidates = [n for n in namelist if n.endswith(href.split('/')[-1])]
                    if candidates: full_href = candidates[0]
                    else: continue

                try:
                    html = z.read(full_href).decode('utf-8', errors='ignore')
                    soup = BeautifulSoup(html, 'html.parser')
                    title = soup.find(['h1', 'h2', 'h3', 'title'])
                    chapter_title = title.text.strip()[:80] if title else Path(href).stem

                    content_blocks = []
                    body = soup.find('body') or soup
                    for el in body.descendants:
                        if el.name in ('script', 'style', 'nav', 'head'): continue
                        if el.name == 'img':
                            src = el.get('src', '')
                            alt = el.get('alt', '')
                            # 匹配图片
                            img_key = Path(src).name if src else ''
                            if img_key in book["images"]:
                                content_blocks.append({"type": "image", "src": book["images"][img_key], "alt": alt})
                            elif src:
                                # 尝试模糊匹配
                                found = None
                                for k in book["images"]:
                                    if k.endswith(img_key) or img_key.endswith(k):
                                        found = k; break
                                if found:
                                    content_blocks.append({"type": "image", "src": book["images"][found], "alt": alt})
                                else:
                                    content_blocks.append({"type": "image", "src": src, "alt": alt, "missing": True})
                            continue
                        if isinstance(el, str):
                            text = el.strip()
                            if text:
                                # 合并连续文本
                                if content_blocks and content_blocks[-1]["type"] == "text":
                                    content_blocks[-1]["value"] += " " + text
                                else:
                                    content_blocks.append({"type": "text", "value": text})

                    if content_blocks:
                        book["chapters"].append({
                            "title": chapter_title,
                            "content": content_blocks,
                        })
                except Exception as e:
                    print(f"  ⚠ Chapter error ({href}): {e}")
    except Exception as e:
        print(f"  ✗ EPUB error: {e}")
        return None
    return book


# ── 计算分页 + 总字符数 ──
def add_pagination(book):
    total_chars = 0
    for ch in book.get("chapters", []):
        for block in ch["content"]:
            if block["type"] == "text":
                total_chars += len(block["value"])
    book["totalChars"] = total_chars
    book["estimatedPages"] = max(1, total_chars // CHARS_PER_PAGE)
    return book


# ── 主流程 ──
def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    count = 0
    for root, dirs, files in os.walk(BOOKS_DIR):
        for f in files:
            if not f.lower().endswith('.epub'): continue
            filepath = os.path.join(root, f)
            rel = os.path.relpath(filepath, BOOKS_DIR).replace('\\', '/')
            title = Path(f).stem
            author = rel.split('/')[1] if '/' in rel else ''
            book_id = hashlib.md5(rel.encode()).hexdigest()[:12]

            out_path = os.path.join(OUT_DIR, f"{book_id}.json")
            if os.path.exists(out_path) and not FORCE:
                continue  # 跳过已缓存

            print(f"[{count+1}] {title} ({author})")
            book = process_epub(filepath)
            if not book:
                print(f"  ✗ 跳过")
                continue
            book["bookId"] = book_id
            book["title"] = book.get("title") or title
            book["author"] = book.get("author") or author
            book["sourcePath"] = rel
            book = add_pagination(book)

            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(book, f, ensure_ascii=False)
            size_kb = os.path.getsize(out_path) / 1024
            chapters = len(book["chapters"])
            images = len(book["images"])
            print(f"  ✓ {chapters}章 {images}图 {book['estimatedPages']}页 {size_kb:.0f}KB → {out_path}")
            count += 1

    print(f"\nDone: {count} books → {OUT_DIR}")


if __name__ == '__main__':
    main()
