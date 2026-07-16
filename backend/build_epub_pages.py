#!/usr/bin/env python3
"""
预计算所有 EPUB 书籍的总页数，写入 JSON 缓存文件。
页数 = 全书总字符数 / 1500（约等于标准印刷页）
用法: python build_epub_pages.py
"""
import os, json, zipfile, re
from pathlib import Path
from html.parser import HTMLParser

# 配置
BOOKS_DIR = "F:/philosophy"
OUTPUT = os.path.join(os.path.dirname(__file__), "..", "app", "public", "epub_pages.json")
CHARS_PER_PAGE = 1500  # 标准印刷页约 1500 中文字符

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.skip = False
    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style', 'head', 'nav'):
            self.skip = True
    def handle_endtag(self, tag):
        if tag in ('script', 'style', 'head', 'nav'):
            self.skip = False
        if tag in ('p', 'div', 'br', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote'):
            self.text.append('\n')
    def handle_data(self, data):
        if not self.skip:
            self.text.append(data.strip())

def count_epub_chars(filepath):
    """提取 EPUB 全文并统计字符数"""
    text = []
    try:
        with zipfile.ZipFile(filepath) as z:
            for name in z.namelist():
                if name.endswith(('.xhtml', '.html', '.htm')) and not '/nav' in name.lower():
                    try:
                        html = z.read(name).decode('utf-8', errors='ignore')
                        parser = TextExtractor()
                        parser.feed(html)
                        text.append(''.join(parser.text))
                    except: pass
    except: return 0
    full = '\n'.join(text)
    return len(full.strip())

def main():
    pages = {}
    total = 0
    for root, dirs, files in os.walk(BOOKS_DIR):
        for f in files:
            if not f.lower().endswith('.epub'): continue
            filepath = os.path.join(root, f)
            rel = os.path.relpath(filepath, BOOKS_DIR).replace('\\', '/')
            chars = count_epub_chars(filepath)
            if chars > 100:
                p = max(1, chars // CHARS_PER_PAGE)
                pages[rel] = p
                total += 1
                if total % 20 == 0: print(f"  {total} books processed...")
    # Also index by book title for lookup
    by_title = {}
    for rel, p in pages.items():
        title = Path(rel).stem
        author = rel.split('/')[1] if '/' in rel else ''
        key = f"{title}||{author}"
        by_title[key] = p
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump({"byPath": pages, "byTitle": by_title, "charPerPage": CHARS_PER_PAGE, "total": total}, f, ensure_ascii=False)
    print(f"Done: {total} EPUBs → {OUTPUT}")

if __name__ == '__main__':
    main()
