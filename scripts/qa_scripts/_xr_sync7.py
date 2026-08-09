# -*- coding: utf-8 -*-
"""同步 7 本 PA 已完成的书 → DP 入库（四层章节 + detail + books.json cc）
排除快乐的科学（⏳待定，竖排残次品）。title/author 以 books.json 现有为准，不动。
"""
import json, os, shutil

PA_CH = 'f:/program/Python/PhiAgent/backend/data/book_chapters'
PA_DETAIL = 'f:/program/Python/PhiAgent/backend/data/book_detail'
DP_PUBLIC = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public'
DP_BACKEND = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend'

BIDS = ['7bb94a203c8c', '9dc98919ade8', '3a23c3ec0466', 'cd1c72bf7f81',
        '75efcbb151b7', '37e1e8e2842b', 'f184edd21ac7']

# ① 章节四层：PA → DP backend + DP public/backend/data
for bid in BIDS:
    src = os.path.join(PA_CH, bid)
    if not os.path.exists(os.path.join(src, 'meta.json')):
        print('  ✗ %s 无 meta，跳过' % bid)
        continue
    for dst in (os.path.join(DP_BACKEND, 'data', 'book_chapters', bid),
                os.path.join(DP_PUBLIC, 'backend', 'data', 'book_chapters', bid)):
        if os.path.exists(dst):
            shutil.rmtree(dst)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copytree(src, dst)
    print('  ① 章节 ✓ %s' % bid)

# ② detail → DP public/book_detail
for bid in BIDS:
    src = os.path.join(PA_DETAIL, bid + '.json')
    if not os.path.exists(src):
        print('  ✗ %s 无 detail' % bid)
        continue
    shutil.copy2(src, os.path.join(DP_PUBLIC, 'book_detail', bid + '.json'))
    print('  ② detail ✓ %s' % bid)

# ③ books.json 只更新 chapterCount（title/author 不动）
bf = os.path.join(DP_PUBLIC, 'books.json')
books = json.load(open(bf, encoding='utf-8'))
for b in books:
    if b.get('id') in BIDS:
        mp = os.path.join(DP_BACKEND, 'data', 'book_chapters', b.get('id'), 'meta.json')
        m = json.load(open(mp, encoding='utf-8'))
        old = b.get('chapterCount')
        b['chapterCount'] = m.get('chapterCount')
        b['extract'] = 'ocr'
        print('  ③ %s %s: cc %s→%s' % (b.get('id'), b.get('title'), old, m.get('chapterCount')))
json.dump(books, open(bf, 'w', encoding='utf-8'), ensure_ascii=False)
# ④ PA app/public 层（前端数据源）：章节 + detail + books.json cc
PA_PUBLIC = 'f:/program/Python/PhiAgent/app/public'
for bid in BIDS:
    src = os.path.join(PA_CH, bid)
    if not os.path.exists(os.path.join(src, 'meta.json')):
        continue
    dst = os.path.join(PA_PUBLIC, 'backend', 'data', 'book_chapters', bid)
    if os.path.exists(dst):
        shutil.rmtree(dst)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copytree(src, dst)
    print('  ④ PA public 章节 ✓ %s' % bid)
for bid in BIDS:
    src = os.path.join(PA_DETAIL, bid + '.json')
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(PA_PUBLIC, 'book_detail', bid + '.json'))
        print('  ④ PA public detail ✓ %s' % bid)
pbf = os.path.join(PA_PUBLIC, 'books.json')
if os.path.exists(pbf):
    pbooks = json.load(open(pbf, encoding='utf-8'))
    for b in pbooks:
        if b.get('id') in BIDS:
            mp = os.path.join(PA_CH, b.get('id'), 'meta.json')
            m = json.load(open(mp, encoding='utf-8'))
            b['chapterCount'] = m.get('chapterCount')
            b['extract'] = 'ocr'
            print('  ④ PA books.json %s: cc→%s' % (b.get('id'), m.get('chapterCount')))
    json.dump(pbooks, open(pbf, 'w', encoding='utf-8'), ensure_ascii=False)
print('同步完成')
