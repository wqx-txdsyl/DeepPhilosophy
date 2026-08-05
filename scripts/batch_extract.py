"""批量提取缺失章节的 EPUB"""
import os, sys, json, hashlib, shutil

# 使用独立提取函数
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)
from extract_one import extract_one

BASE = os.path.dirname(SCRIPT_DIR)
BOOKS_FILE = os.path.join(BASE, 'app', 'public', 'books.json')
CHAPTER_DIR = os.path.join(BASE, 'backend', 'data', 'book_chapters')
BOOKS_DIR = 'F:/philosophy'

with open(BOOKS_FILE, 'r', encoding='utf-8') as f:
    books = json.load(f)

chapter_dirs = {d for d in os.listdir(CHAPTER_DIR) if os.path.isdir(os.path.join(CHAPTER_DIR, d))}

# 找需要处理的 EPUB
todo = []
for b in books:
    if b.get('file_type') != 'epub':
        continue
    bid = b['id']
    if bid in chapter_dirs:
        continue  # 已有章节

    # 找文件
    region = b['region']
    author = b['author']
    search_dir = os.path.join(BOOKS_DIR, region, author)
    if not os.path.isdir(search_dir):
        continue

    found_file = None
    for f in os.listdir(search_dir):
        if not f.endswith('.epub'):
            continue
        rel_path = os.path.join(region, author, f).replace('\\', '/')
        fid = hashlib.md5(rel_path.encode()).hexdigest()[:12]
        if fid == bid:
            found_file = f
            break

    if found_file:
        fp = os.path.join(search_dir, found_file)
        todo.append((b, fp))
    else:
        # 模糊匹配
        for f in os.listdir(search_dir):
            if f.endswith('.epub'):
                fp = os.path.join(search_dir, f)
                todo.append((b, fp))
                break

print('To extract: {}'.format(len(todo)))

success = 0
for i, (book, epub_path) in enumerate(todo, 1):
    bid = book['id']
    title = book['title']
    out_dir = os.path.join(CHAPTER_DIR, bid)
    idx = '[{}/{}]'.format(i, len(todo))

    print('  {} {}'.format(idx, title[:40]), end=' ', flush=True)
    ok, info = extract_one(epub_path, out_dir)
    if ok:
        print('{}ch'.format(info))
        success += 1
    else:
        print('FAIL: {}'.format(info))

print()
print('Success: {}/{}'.format(success, len(todo)))

# 最终统计
chapter_dirs = {d for d in os.listdir(CHAPTER_DIR) if os.path.isdir(os.path.join(CHAPTER_DIR, d))}
book_ids = {b['id'] for b in books}
matched = book_ids & chapter_dirs
print('Chapter match: {}/{}'.format(len(matched), len(books)))
