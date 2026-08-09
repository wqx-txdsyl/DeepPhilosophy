# -*- coding: utf-8 -*-
"""书架 403 本按格式统计 + epub 全量核验状态审计"""
import json, re
from collections import Counter

bj = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json', encoding='utf-8'))
bl = bj if isinstance(bj, list) else bj.get('books', [])
print('书架总数:', len(bl))

# 1. 格式构成
ft = Counter(b.get('file_type', '?') for b in bl)
print('格式构成:', dict(ft))

# 2. CHKLIST 状态
cklist = open('f:/program/Python/PhiAgent/backend/tools/CHKLIST.md', encoding='utf-8').read()
rows = re.findall(r'\|\s*(\d+)\s*\|\s*([^|]+?)\s*\|\s*([0-9a-f]{12})\s*\|[^|]*\|\s*([^|]+?)\s*\|', cklist)
status_by_bid = {r[2]: (int(r[0]), r[1].strip(), r[3].strip()) for r in rows}

# 3. epub 书逐本核验状态
epub_pending, epub_done = [], []
for b in bl:
    if b.get('file_type') != 'epub':
        continue
    st = status_by_bid.get(b['id'])
    if st is None:
        epub_pending.append(('(无CHKLIST)', b['title'], '—'))
    elif st[2].startswith(('✅', '✓')):
        epub_done.append((st[0], b['title'], st[2]))
    else:
        epub_pending.append((st[0], b['title'], st[2]))
print()
print('epub 共 %d 本: 已核验 %d | 未核验/待定 %d' % (
    len(epub_done) + len(epub_pending), len(epub_done), len(epub_pending)))
print()
print('== epub 未核验清单 ==')
for st, t, s in sorted(epub_pending, key=lambda x: (x[2], str(x[0]))):
    print('  #%-5s %s [%s]' % (st, t[:40], s))

# 4. 其他格式未核验（pdf/txt）
print()
print('== 非 epub 未核验 ==')
other_pending = []
for b in bl:
    if b.get('file_type') == 'epub':
        continue
    st = status_by_bid.get(b['id'])
    if st is None or not st[2].startswith(('✅', '✓')):
        other_pending.append((st[0] if st else '(无)', b['title'], b.get('file_type', '?'), st[2] if st else '—'))
for st, t, f, s in sorted(other_pending, key=lambda x: x[1]):
    print('  #%-5s [%s] %s [%s]' % (st, f, t[:40], s))
