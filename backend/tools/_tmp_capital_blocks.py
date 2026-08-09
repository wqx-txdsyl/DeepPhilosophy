# -*- coding: utf-8 -*-
"""读《资本论》(b3219ec260ed): 块长度分布, 找出过长段落(>6000字符)"""
import json, os

D = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/b3219ec260ed'
files = sorted([f for f in os.listdir(D) if f.endswith('.json') and f != 'meta.json'], key=lambda x: int(x.split('.')[0]))
print('章节文件数:', len(files))
stats = {}
overlong = []
for fn in files:
    ch = json.load(open(os.path.join(D, fn), encoding='utf-8'))
    n = len(ch.get('content', []))
    lens = [len(b.get('value', '')) for b in ch.get('content', [])]
    mx = max(lens) if lens else 0
    stats[fn] = (ch.get('title'), n, mx, lens)
    for i, l in enumerate(lens):
        if l > 6000:
            overlong.append((fn, i, l, ch.get('title')))

print('\n=== 每章块数与最大块 ===')
for fn in files:
    t, n, mx, lens = stats[fn]
    print('%s %-22s 块:%3d 最大:%5d 均长:%5d' % (fn, (t or '?')[:18], n, mx, (sum(lens) // n) if n else 0))

print('\n=== 超长块 (>6000) ===')
for fn, i, l, t in overlong:
    print('%s [%d] 块%03d: %d字符 %s' % (fn, int(fn.split('.')[0]), i, l, (t or '')[:16]))
print('超长块总数:', len(overlong))
