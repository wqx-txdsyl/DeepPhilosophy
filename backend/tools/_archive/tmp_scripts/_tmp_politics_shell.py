# -*- coding: utf-8 -*-
"""政治学 (53b09f03e24e) 空壳章定位"""
import json, os, re

D = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/53b09f03e24e'
files = sorted([f for f in os.listdir(D) if re.match(r'^\d+\.json$', f)], key=lambda x: int(x.split('.')[0]))
for fn in files:
    ch = json.load(open(os.path.join(D, fn), encoding='utf-8'))
    n = sum(len(b.get('value', '')) for b in ch.get('content', []))
    head = ch['content'][0].get('value', '')[:40] if ch.get('content') else '(空)'
    if n < 200:
        print('[%03d] %-20s %6d | %s' % (ch['index'], str(ch.get('title'))[:20], n, head))
