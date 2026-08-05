"""全面检查所有书：封面 + 目录 + 章节内容 + 简介"""
import os, json, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS_FILE = os.path.join(BASE, 'app', 'public', 'books.json')
CHAPTER_DIR = os.path.join(BASE, 'backend', 'data', 'book_chapters')
DETAIL_DIR = os.path.join(BASE, 'app', 'public', 'book_detail')
COVERS_DIR = os.path.join(BASE, 'app', 'public', 'covers')

with open(BOOKS_FILE, 'r', encoding='utf-8') as f:
    books = json.load(f)

total = len(books)
issues = {
    'no_cover': [],
    'no_toc': [],
    'no_chapters': [],
    'empty_chapters': [],
    'no_detail': [],
    'no_summary': [],
}

for i, b in enumerate(books, 1):
    bid = b['id']
    title = b['title']
    ext = b.get('file_type', 'epub')

    # 1. 封面 (仅 EPUB 需要)
    if ext == 'epub':
        has_cover = os.path.exists(os.path.join(COVERS_DIR, bid + '.webp'))
        if not has_cover:
            issues['no_cover'].append(title)

    # 2-3. 目录和章节
    ch_dir = os.path.join(CHAPTER_DIR, bid)
    if os.path.isdir(ch_dir):
        meta_file = os.path.join(ch_dir, 'meta.json')
        ch_files = [f for f in os.listdir(ch_dir) if f.endswith('.json') and f != 'meta.json']

        if os.path.exists(meta_file):
            with open(meta_file, 'r', encoding='utf-8') as f:
                meta = json.load(f)
            toc = meta.get('toc', meta.get('chapterTitles', []))
            if not toc:
                issues['no_toc'].append(title)
        else:
            issues['no_toc'].append(title)

        if not ch_files:
            issues['no_chapters'].append(title)
        else:
            # 检查章节是否有内容
            empty_count = 0
            for cf in ch_files[:3]:  # 抽样前3章
                with open(os.path.join(ch_dir, cf), 'r', encoding='utf-8') as f:
                    ch = json.load(f)
                content = ch.get('content', [])
                if not content or all(
                    not (b.get('value', '').strip()) if isinstance(b, dict) and b.get('type') == 'text' else True
                    for b in content
                ):
                    empty_count += 1
            if empty_count >= len(ch_files[:3]):
                issues['empty_chapters'].append(title)
    else:
        # PDF/TXT — chapters not applicable
        pass

    # 4. 简介 (book_detail)
    detail_file = os.path.join(DETAIL_DIR, bid + '.json')
    if os.path.exists(detail_file):
        with open(detail_file, 'r', encoding='utf-8') as f:
            detail = json.load(f)
        summary = detail.get('summary', '')
        if not summary or len(summary) < 30:
            issues['no_summary'].append(title)
    else:
        issues['no_detail'].append(title)

    if i % 50 == 0:
        print('  [{}/{}]...'.format(i, total))

# 报告
print()
print('=== 检查结果 ({}) ==='.format(total))
for issue_type, titles in issues.items():
    label = {
        'no_cover': '缺封面',
        'no_toc': '缺目录',
        'no_chapters': '缺章节文件',
        'empty_chapters': '章节空内容',
        'no_detail': '缺book_detail',
        'no_summary': '缺简介',
    }.get(issue_type, issue_type)
    print('\n[{}] {}: {}'.format(label, len(titles), '✓' if not titles else ''))
    for t in titles[:10]:
        print('  - {}'.format(t[:60]))
    if len(titles) > 10:
        print('  ... 等 {} 本'.format(len(titles) - 10))
