"""
批量导入哲学书 — 两阶段
  python batch_import_books.py           → 生成待审 CSV
  python batch_import_books.py --review  → 读 CSV 全自动入库
"""
import os, sys, json, io, re, time, shutil, urllib.request, hashlib, zipfile, csv, subprocess
from bs4 import BeautifulSoup

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_DIR = 'F:/philosophy/new/100本哲学书单全收录'
TARGET_BASE = 'F:/philosophy'
PHIL_FILE = os.path.join(BASE, 'app', 'public', 'philosophers.json')
BOOKS_FILE = os.path.join(BASE, 'app', 'public', 'books.json')
DETAIL_DIR = os.path.join(BASE, 'app', 'public', 'book_detail')
REVIEW_FILE = os.path.join(BASE, 'scripts', '_review_books.csv')
SPINE_SCRIPT = os.path.join(BASE, 'backend', 'tools', 'rebuild_spine.py')
COVER_SCRIPT = os.path.join(BASE, 'backend', 'tools', 'build_covers_manifest.py')
SCORE_SCRIPT = os.path.join(BASE, 'scripts', 'score_item.py')

env_path = os.path.join(BASE, '.env')
for line in open(env_path, encoding='utf-8'):
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1)
        os.environ.setdefault(k.strip(), v.strip())
API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')

# encoding handled via PYTHONIOENCODING=utf-8

def extract_epub_meta(epub_path):
    try:
        with zipfile.ZipFile(epub_path, 'r') as z:
            names = z.namelist()
            rootfile = None
            for n in names:
                if n.endswith('container.xml'):
                    c = z.read(n).decode('utf-8', errors='ignore')
                    m = re.search(r'full-path="([^"]+)"', c)
                    if m: rootfile = m.group(1)
                    break
            if not rootfile:
                for n in names:
                    if n.endswith('.opf'): rootfile = n; break
            if not rootfile: return None, None
            opf = BeautifulSoup(z.read(rootfile).decode('utf-8', errors='ignore'), 'xml')
            title_el = opf.find('dc:title')
            author_el = opf.find('dc:creator')
            title = title_el.get_text().strip() if title_el else None
            author = author_el.get_text().strip() if author_el else None
            return title, author
    except: return None, None

def clean_author(raw):
    if not raw: return ''
    for junk in ['ePUBw.COM', 'epubw.com', 'z-lib.org', 'Z-Library']:
        raw = raw.replace(junk, '').replace(junk.lower(), '')
    raw = raw.replace(',', ' ').replace(',', ' ')
    return ' '.join(raw.split()).strip()

def scan_epubs():
    epubs = []
    for root, dirs, files in os.walk(SOURCE_DIR):
        for f in files:
            if f.endswith('.epub'):
                path = os.path.join(root, f)
                fname = os.path.splitext(f)[0].strip()
                fname = re.sub(r'^\d+\s*[-—-]?\s*', '', fname)
                meta_title, meta_author = extract_epub_meta(path)
                title = meta_title or fname
                author = clean_author(meta_author or '')
                epubs.append({'path': path, 'title': title, 'author': author, 'fname': fname})
    return epubs

# ==============================
# PHASE 1: generate CSV
# ==============================
if '--review' not in sys.argv:
    epubs = scan_epubs()
    with open(REVIEW_FILE, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['keep', 'title', 'author', 'region', 'filename'])
        for e in epubs:
            writer.writerow(['Y', e['title'], e['author'], '', e['fname']])
    print('Generated: {}'.format(REVIEW_FILE))
    print('Total: {} books'.format(len(epubs)))
    print()
    print('Edit in Excel:')
    print('  keep:   Y=import / N=skip')
    print('  title:  fix book title')
    print('  author: fix author name')
    print('  region: east/west/world')
    print()
    print('Then run: python {} --review'.format(__file__))
    sys.exit(0)

# ==============================
# PHASE 2: read CSV -> pipeline
# ==============================
print('=== Phase 2: Import ===')
print()

epubs = scan_epubs()
path_map = {e['fname']: e['path'] for e in epubs}

with open(REVIEW_FILE, 'r', encoding='utf-8-sig') as f:
    reader = csv.DictReader(f)
    books_to_add = []
    for row in reader:
        if row['keep'].strip().upper() != 'Y':
            t = row['title']
            print('  [SKIP] {}'.format(t[:50]))
            continue
        fname = row['filename'].strip()
        if fname not in path_map:
            print('  [MISS] {}'.format(fname))
            continue
        books_to_add.append({
            'path': path_map[fname],
            'title': row['title'].strip(),
            'author': row['author'].strip(),
            'region': row['region'].strip() or None,
        })

if not books_to_add:
    print('No books to import.')
    sys.exit(0)

total = len(books_to_add)
print('Importing: {} books'.format(total))

# Step 1: AI classify region
print()
print('=== 1. AI Classify ===')
for i, book in enumerate(books_to_add, 1):
    title = book['title']
    author = book['author']
    region = book['region']
    idx = '[{}/{}]'.format(i, total)

    # E/W -> 东方/西方
    if region and region.upper() in ('E', 'W'):
        book['region'] = '东方' if region.upper() == 'E' else '西方'
        region = book['region']

    if region and region in ('东方', '西方', '世界', 'east', 'west', 'world'):
        print('  {} {} -> {} (given)'.format(idx, title[:40], region))
        if region in ('east', 'west', 'world'):
            book['region'] = {'east': '东方', 'west': '西方', 'world': '世界'}[region]
        continue

    prompt = '哲学书《' + title + '》（作者：' + author + '）。判断属于哪个传统：东方/西方/世界。只返回一个词。'
    payload = {
        'model': 'deepseek-chat', 'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 0.1, 'max_tokens': 10, 'response_format': {'type': 'json_object'}
    }
    try:
        req = urllib.request.Request('https://api.deepseek.com/v1/chat/completions',
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + API_KEY})
        with urllib.request.urlopen(req, timeout=15) as resp:
            r = json.loads(resp.read().decode('utf-8'))
            content = json.loads(r['choices'][0]['message']['content'])
            answer = content.get('region', content.get('answer', '西方'))
            if '东' in str(answer): book['region'] = '东方'
            elif '西' in str(answer): book['region'] = '西方'
            else: book['region'] = '世界'
    except Exception as e:
        book['region'] = '西方'
    print('  {} {} -> {}'.format(idx, title[:40], book['region']))
    time.sleep(0.2)

# Step 2: Copy EPUBs
print()
print('=== 2. Copy EPUBs ===')
for book in books_to_add:
    dst_dir = os.path.join(TARGET_BASE, book['region'], book['author'])
    os.makedirs(dst_dir, exist_ok=True)
    dst = os.path.join(dst_dir, os.path.basename(book['path']))
    if not os.path.exists(dst):
        shutil.copy2(book['path'], dst)
    book['dst'] = dst
    try:
        print('  {}/{}/{}'.format(book['region'], book['author'], os.path.basename(dst)))
    except UnicodeEncodeError:
        print('  {}/{}'.format(book['region'], os.path.basename(dst)))

# Step 3-4: Skip chapters/covers for now (run rebuild_spine separately later)

# Step 3: Score + register
print()
print('=== 5. Score & Register ===')
with open(BOOKS_FILE, 'r', encoding='utf-8') as f:
    all_books = json.load(f)
with open(PHIL_FILE, 'r', encoding='utf-8') as f:
    philosophers = json.load(f)

for i, book in enumerate(books_to_add, 1):
    title = book['title']
    author = book['author']
    region = book['region']
    idx = '[{}/{}]'.format(i, total)

    # ID 必须与 rebuild_spine 一致：相对路径的 MD5
    rel_path = os.path.relpath(book['dst'], TARGET_BASE).replace('\\', '/')
    bid = hashlib.md5(rel_path.encode()).hexdigest()[:12]
    ext = os.path.splitext(book['path'])[1].lower().replace('.', '')
    size = round(os.path.getsize(book['path']) / 1024, 1)

    ch_file = os.path.join(BASE, 'backend', 'data', 'book_chapters', bid + '.json')
    chapter_count = 0
    if os.path.exists(ch_file):
        with open(ch_file, 'r', encoding='utf-8') as f:
            chapter_count = len(json.load(f))

    print('  {} {}'.format(idx, title[:40]), end=' ', flush=True)
    rank = 0
    try:
        result = subprocess.run(
            [sys.executable, SCORE_SCRIPT, title, '--type', 'book'],
            capture_output=True, text=True, timeout=30, cwd=BASE
        )
        scores = json.loads(result.stdout)
        rank = scores.get('rank', 0)
        print('score={}'.format(rank))
    except Exception as e:
        print('score=0 ({})'.format(e))

    all_books.append({
        'id': bid, 'title': title, 'author': author,
        'region': region, 'file_type': ext, 'file_size': size,
        'chapterCount': chapter_count, 'rank': rank, 'tags': []
    })

    if author not in ('合集&概述', '佚名', '?'):
        if author not in philosophers:
            philosophers[author] = {
                'name': author, 'era': '', 'country': '', 'school': '',
                'bio': author + '，哲学家。',
                'books': [title], 'book_count': 1,
                'region': region, 'rank': 0, 'wiki_url': ''
            }
        else:
            ph = philosophers[author]
            if 'books' not in ph: ph['books'] = []
            if title not in ph['books']:
                ph['books'].append(title)
            ph['book_count'] = len(ph['books'])

    time.sleep(0.3)

all_books.sort(key=lambda b: b.get('rank', 0), reverse=True)
with open(BOOKS_FILE, 'w', encoding='utf-8') as f:
    json.dump(all_books, f, ensure_ascii=False, indent=2)
with open(PHIL_FILE, 'w', encoding='utf-8') as f:
    json.dump(philosophers, f, ensure_ascii=False, indent=2)

print()
print('=== Done ===')
print('New: {}'.format(total))
print('Total books: {}'.format(len(all_books)))
print('Total philosophers: {}'.format(len(philosophers)))
