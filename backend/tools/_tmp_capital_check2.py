# -*- coding: utf-8 -*-
"""读《资本论》重建后检查"""
import json, os, re

D = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/b3219ec260ed'
files = sorted([f for f in os.listdir(D) if re.match(r'^\d+\.json$', f)], key=lambda x: int(x.split('.')[0]))
print('章数:', len(files))
total = 0
for fn in files:
    ch = json.load(open(os.path.join(D, fn), encoding='utf-8'))
    n = sum(len(b.get('value', '')) for b in ch.get('content', []))
    total += n
    head = ch['content'][0].get('value', '')[:45] if ch.get('content') else '(空)'
    print('[%02d] %-22s %8d | %s' % (ch['index'], str(ch.get('title'))[:22], n, head))
print('合计:', total)
