# -*- coding: utf-8 -*-
"""台账外已入库书：PA books_catalog − CHKLIST 登记，且实际有章节数据"""
import io, json, os, re, sys
sys.stdout.reconfigure(encoding='utf-8')

cat = json.load(open('f:/program/Python/PhiAgent/backend/data/books_catalog.json', encoding='utf-8'))
chk = io.open('f:/program/Python/PhiAgent/backend/tools/CHKLIST.md', encoding='utf-8').read()
reg_bids = set(re.findall(r'\|\s*\d+\s*\|[^|]+\|\s*([0-9a-f]{12,})', chk))

books = cat['books']
BC = 'f:/program/Python/PhiAgent/backend/data/book_chapters'

waiji = []
for b in books:
    bid = b.get('id')
    if not bid or bid in reg_bids:
        continue
    d = os.path.join(BC, bid)
    if not os.path.isdir(d):
        continue
    try:
        m = json.load(open(os.path.join(d, 'meta.json'), encoding='utf-8'))
        cc = m.get('chapterCount', '?')
    except Exception:
        cc = '?'
    waiji.append((bid, b.get('title', '')[:34], cc))

waiji.sort(key=lambda x: x[0])
print('台账外已入库', len(waiji), '本:')
for i, (bid, t, cc) in enumerate(waiji):
    print('%2d %s  %s  cc=%s' % (i, bid, t, cc))
