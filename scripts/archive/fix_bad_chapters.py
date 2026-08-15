"""用 rebuild_spine 修复有问题的章节（通过子进程调单本书）"""
import os, sys, json, re, hashlib, subprocess, shutil

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAPTER_DIR = os.path.join(BASE, 'backend', 'data', 'book_chapters')
BOOKS_DIR = 'F:/philosophy'
SPINE_SCRIPT = os.path.join(BASE, 'backend', 'tools', 'rebuild_spine.py')

with open(os.path.join(BASE, 'app', 'public', 'books.json'), 'r', encoding='utf-8') as f:
    books = json.load(f)

bad_books = []
for b in books:
    if b.get('file_type') != 'epub': continue
    bid = b['id']
    ch_dir = os.path.join(CHAPTER_DIR, bid)
    mf = os.path.join(ch_dir, 'meta.json')
    if not os.path.exists(mf): continue
    with open(mf, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    titles = meta.get('chapterTitles', [])
    book_title = meta.get('title', '')

    bad = False
    for t in titles:
        if book_title and len(book_title) > 5 and (t == book_title or book_title[:15] in t):
            bad = True; break
        if re.match(r'^[0-9a-fA-F]{4,}$', t): bad = True; break
        if t in ('Cover', '版权页', '版权信息', '版权', '目录', 'Unknown', '文硕阁', '封面', '未知', '书名'):
            bad = True; break

    if not bad: continue

    region = b['region']; author = b['author']
    search = os.path.join(BOOKS_DIR, region, author)
    if not os.path.isdir(search): continue
    for fn in os.listdir(search):
        if not fn.endswith('.epub'): continue
        rel = (region + '/' + author + '/' + fn).replace('\\', '/')
        if hashlib.md5(rel.encode()).hexdigest()[:12] == bid:
            bad_books.append((b, os.path.join(search, fn)))
            break

print('To fix: {}'.format(len(bad_books)))

for i, (book, epub_path) in enumerate(bad_books, 1):
    bid = book['id']
    title = book['title']
    idx = '[{}/{}]'.format(i, len(bad_books))

    # 删旧章节目录
    ch_dir = os.path.join(CHAPTER_DIR, bid)
    if os.path.isdir(ch_dir):
        shutil.rmtree(ch_dir)

    print('  {} {}'.format(idx, title[:40]), end=' ', flush=True)

    try:
        result = subprocess.run(
            [sys.executable, SPINE_SCRIPT, epub_path],
            capture_output=True, text=True, timeout=120,
            cwd=os.path.join(BASE, 'backend')
        )
        if result.returncode == 0:
            # rebuild_spine 用 text 块，提取后转换 HTML
            # 但我们直接用它的结果，保持 text 格式
            print('OK')
        else:
            print('FAIL: {}'.format((result.stderr or result.stdout)[:60]))
    except subprocess.TimeoutExpired:
        print('TIMEOUT')
    except Exception as e:
        print('ERR: {}'.format(e))

print('Done')
