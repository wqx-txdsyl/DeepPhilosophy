"""逐本审查所有书的章节标题质量"""
import os, json, re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHAPTER_DIR = os.path.join(BASE, 'backend', 'data', 'book_chapters')
BOOKS_FILE = os.path.join(BASE, 'app', 'public', 'books.json')

with open(BOOKS_FILE, 'r', encoding='utf-8') as f:
    books = json.load(f)

OK = []
HAS_ISSUES = []
NO_CHAPTERS = []

for b in books:
    bid = b['id']
    title = b['title']
    author = b.get('author', '')
    file_type = b.get('file_type', 'epub')
    ch_dir = os.path.join(CHAPTER_DIR, bid)

    if not os.path.isdir(ch_dir):
        NO_CHAPTERS.append((title, file_type))
        continue

    mf = os.path.join(ch_dir, 'meta.json')
    if not os.path.exists(mf):
        HAS_ISSUES.append((title, '无meta.json', author))
        continue

    with open(mf, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    ch_titles = meta.get('chapterTitles', [])
    ch_count = meta.get('chapterCount', 0)

    if not ch_titles:
        HAS_ISSUES.append((title, '章节标题为空', author))
        continue

    # 质量检查
    problems = []

    # 1. 与书名重复
    if len(ch_titles) >= 3 and all(title[:8] in t[:20] for t in ch_titles[:3]):
        problems.append('ALL_SAME_AS_BOOK_TITLE')

    # 2. 全泛型（全"第X章"）
    generic = sum(1 for t in ch_titles if re.match(r'^第\d+章$', t))
    if generic == len(ch_titles):
        problems.append('ALL_GENERIC_CHAPTERS')

    # 3. 含垃圾词
    bad_words = {'未知', '文硕阁', 'vf5otb', 'Unknown', 'Cover'}
    bad_count = sum(1 for t in ch_titles if t in bad_words)
    if bad_count > 0:
        problems.append('{}_BAD_WORDS'.format(bad_count))

    # 4. 乱码检测
    garbled = 0
    for t in ch_titles[:10]:
        if re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', t):
            garbled += 1
    if garbled > 0:
        problems.append('{}_GARBLED'.format(garbled))

    # 5. 英文标题
    en_count = sum(1 for t in ch_titles if re.match(r'^[A-Z][a-z]+', t))
    if en_count > len(ch_titles) * 0.5:
        problems.append('MOSTLY_ENGLISH')

    # 6. 含元数据页
    meta_pages = {'目录', '扉页', '书名页', '版权页', '版权信息', '封面', 'Cover'}
    meta_count = sum(1 for t in ch_titles if t in meta_pages)
    if meta_count > 0:
        problems.append('{}_META_PAGES'.format(meta_count))

    if problems:
        HAS_ISSUES.append((title, ','.join(problems), ch_count, list(ch_titles[:3])))
    else:
        OK.append((title, ch_count))

# --- 报告 ---
print('=== 审查结果 ===')
print()
print('OK: {} 本'.format(len(OK)))
print('有问题: {} 本'.format(len(HAS_ISSUES)))
print('无章节: {} 本'.format(len(NO_CHAPTERS)))
print()

if HAS_ISSUES:
    print('--- 有问题的书 ---')
    for item in HAS_ISSUES:
        title, problem, *rest = item
        ch_count = rest[0] if rest else '?'
        sample = rest[1] if len(rest) > 1 else []
        print()
        print('  《{}》'.format(title[:60]))
        print('  问题: {} | {}章'.format(problem, ch_count))
        if sample:
            print('  例: {}'.format(sample[:3]))

if NO_CHAPTERS:
    print()
    print('--- 无章节 (PDF/TXT，正常) ---')
    pdfs = sum(1 for t, ft in NO_CHAPTERS if ft != 'epub')
    epubs = sum(1 for t, ft in NO_CHAPTERS if ft == 'epub')
    print('  PDF/TXT: {}'.format(pdfs))
    print('  EPUB: {}'.format(epubs))
    if epubs > 0:
        for t, ft in NO_CHAPTERS:
            if ft == 'epub':
                print('  EPUB无章节: 《{}》'.format(t[:50]))
