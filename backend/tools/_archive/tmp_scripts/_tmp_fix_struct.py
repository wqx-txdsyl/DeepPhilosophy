# -*- coding: utf-8 -*-
"""27 本结构问题统一修复 (2026-08-09 全量验证):
A. detail title/author 同步: pdf 以 meta 为准 (AUTHOR_FIX/MERGE_RULES 权威);
   epub 例外 2 本 (梦的解析/马克思恩格斯文集/MEGA) meta ← detail 完整作者
B. toc 字符串数组 → 对象数组 (5 本, chapterTitles 已是 N 项)
C. chapterTitles 从 toc 重建 (toc 对象数组且 index 覆盖完整)
D. 大问题 meta.title/author 空 → 回填
全部双端写回 + detail + books.json
"""
import json, os, sys, io, re

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy'
BC = os.path.join(BASE, 'backend/data/book_chapters')
PBC = os.path.join(BASE, 'app/public/backend/data/book_chapters')
DDIR = os.path.join(BASE, 'backend/data/book_detail')
PDIR = os.path.join(BASE, 'app/public/book_detail')
BJ = os.path.join(BASE, 'app/public/books.json')

def write_meta(bid, m):
    for pre in (BC, PBC):
        json.dump(m, open(os.path.join(pre, bid, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False)

def write_detail(bid, d):
    for pre in (DDIR, PDIR):
        json.dump(d, open(os.path.join(pre, bid + '.json'), 'w', encoding='utf-8'), ensure_ascii=False)

def load_meta(bid):
    return json.load(open(os.path.join(BC, bid, 'meta.json'), encoding='utf-8'))

def load_detail(bid):
    fp = os.path.join(DDIR, bid + '.json')
    return json.load(open(fp, encoding='utf-8')) if os.path.exists(fp) else {}

def sync_detail_from_meta(bid, m, d):
    d['title'] = m['title']; d['author'] = m['author']
    d['toc'] = m['toc']; d['chapterCount'] = m['chapterCount']; d['chapterTitles'] = m['chapterTitles']
    return d

def update_books(bid, title, author, cc):
    bj = json.load(open(BJ, encoding='utf-8'))
    items = bj if isinstance(bj, list) else bj.get('books', [])
    for it in items:
        if it.get('id') == bid:
            it['title'] = title; it['author'] = author; it['chapterCount'] = cc
            break
    json.dump(bj, open(BJ, 'w', encoding='utf-8'), ensure_ascii=False)

# ── A. title/author 统一 ──
# A_exception: meta ← detail (完整作者)
A_EPUB_FULL = {
    '7729ccdecb0f': '卡尔·马克思、弗里德里希·恩格斯',  # 马克思恩格斯文集 epub
    '1085686cbd33': '卡尔·马克思、弗里德里希·恩格斯',  # MEGA pdf (MERGE_RULES 标准顿号)
    '4fc33e4af5fb': None,  # 梦的解析: author 用 detail 原值 (完整作者列表)
}
# A_fix: detail ← meta (pdf, AUTHOR_FIX 权威)
A_PDF = ['10e1874c2255', '8c0c6955c793', 'f08c1ead3164', '178e7d06d42d', '40750581f8e8',
         'd1a2be0b5837', '64056c6623ee', '221f09d04944', '978ade412255', 'cc9d0d9358a7',
         '23ab04b02f68', '219b862077e1', 'dd75d637a2ad']

# ── B. toc 字符串数组 → 对象数组 ──
B_TOC_STR = ['48f7bf321598', 'dd75d637a2ad', '74ee21ced920', 'b3219ec260ed', '26f5e0df6d76']

# ── C. chapterTitles 从 toc 重建 ──
C_TOC_OK = ['88b56fb4da52', '8a451d16f1b4', '0d31135f957d', 'b2fbc225f414', '2cbf90eb6f69']

# ── D. 大问题 title/author 回填 ──
D_BID = '2cbf90eb6f69'
D_TITLE = '大问题'
D_AUTHOR = '罗伯特•所罗门'

changed = 0
# A
for bid in A_PDF:
    m = load_meta(bid); d = load_detail(bid)
    if not d: print('  !! detail 缺失 %s' % bid); continue
    if (d.get('title'), d.get('author')) != (m['title'], m['author']):
        print('A  %s: detail(%r,%r) -> meta(%r,%r)' % (bid, d.get('title'), d.get('author'), m['title'], m['author']))
        d = sync_detail_from_meta(bid, m, d)
        write_detail(bid, d)
        update_books(bid, m['title'], m['author'], m['chapterCount'])
        changed += 1
for bid, author in A_EPUB_FULL.items():
    m = load_meta(bid); d = load_detail(bid)
    if not d: print('  !! detail 缺失 %s' % bid); continue
    new_a = author or d.get('author')
    if m.get('author') != new_a:
        print('A  %s: meta.author %r -> %r' % (bid, m.get('author'), new_a))
        m['author'] = new_a
        write_meta(bid, m)
        d = sync_detail_from_meta(bid, m, d)
        write_detail(bid, d)
        update_books(bid, m['title'], m['author'], m['chapterCount'])
        changed += 1
    elif (d.get('title'), d.get('author')) != (m['title'], m['author']):
        d = sync_detail_from_meta(bid, m, d)
        write_detail(bid, d)
        update_books(bid, m['title'], m['author'], m['chapterCount'])
        changed += 1

# B
for bid in B_TOC_STR:
    m = load_meta(bid)
    toc = m.get('toc', [])
    if toc and isinstance(toc[0], str):
        n = m['chapterCount']
        new_toc = [{'type': 'chapter', 'title': t, 'index': i} for i, t in enumerate(toc)]
        m['toc'] = new_toc
        write_meta(bid, m)
        d = load_detail(bid)
        d = sync_detail_from_meta(bid, m, d)
        write_detail(bid, d)
        print('B  %s: toc 字符串数组 %d 项 -> 对象数组' % (bid, n))
        changed += 1
    else:
        print('B  %s: 已是对象数组, 跳过' % bid)

# C
for bid in C_TOC_OK:
    m = load_meta(bid)
    toc = m.get('toc', [])
    n = m['chapterCount']
    if not (isinstance(toc, list) and toc and isinstance(toc[0], dict)):
        print('C  %s: toc 非对象数组, 跳过' % bid); continue
    idx_map = {t.get('index'): t.get('title', '') for t in toc if isinstance(t.get('index'), int)}
    if set(idx_map.keys()) != set(range(n)):
        print('C  %s: toc index 覆盖不完整, 跳过 (缺 %s)' % (bid, sorted(set(range(n)) - set(idx_map))[:6]))
        continue
    titles = [idx_map[i] for i in range(n)]
    if m.get('chapterTitles') != titles:
        print('C  %s: chapterTitles %d 项 -> %d 项 (从 toc 重建)' % (bid, len(m.get('chapterTitles', [])), n))
        m['chapterTitles'] = titles
        write_meta(bid, m)
        d = load_detail(bid)
        d = sync_detail_from_meta(bid, m, d)
        write_detail(bid, d)
        changed += 1
    else:
        print('C  %s: chapterTitles 已一致' % bid)

# D
m = load_meta(D_BID); d = load_detail(D_BID)
if not m.get('title') or not m.get('author'):
    print('D  %s: meta title/author 缺失 -> 回填 (%r, %r)' % (D_BID, D_TITLE, D_AUTHOR))
    m['title'] = D_TITLE; m['author'] = D_AUTHOR
    write_meta(D_BID, m)
    d = sync_detail_from_meta(D_BID, m, d)
    write_detail(D_BID, d)
    update_books(D_BID, m['title'], m['author'], m['chapterCount'])
    changed += 1
else:
    print('D  %s: title/author 已存在, 跳过' % D_BID)

print('\n共修复 %d 本 — 逐个跑 verify_book.py 验证' % changed)
