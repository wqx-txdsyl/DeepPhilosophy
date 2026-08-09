# -*- coding: utf-8 -*-
"""边沁重建验证: 残留模式扫描 + 章结构"""
import json, os, re

D = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/74ee21ced920'
files = sorted(f for f in os.listdir(D) if f.endswith('.json'))
files.remove('meta.json')
print('章数:', len(files))

PATTERNS = [
    ('孤立页码 ^\\d{1,4}$', re.compile(r'(?m)^\d{1,4}$')),
    ('脚注锚点[①-⑨]', re.compile(r'[①-⑨]')),
    ('@残留', re.compile(r'@')),
    ('页眉第X章行', re.compile(r'(?m)^第[一二三四五六七八九十百]+章[^。]{0,10}$')),
    ('罗马页码', re.compile(r'(?m)^[ivxlIVXL]{1,8}$')),
    ('中缝单字行', re.compile(r'(?m)^[一-龥]{1}$')),
]
hits = {k: [] for k, _ in PATTERNS}
for fn in files:
    ch = json.load(open(os.path.join(D, fn), encoding='utf-8'))
    for blk in ch.get('content', []):
        v = blk.get('value', '')
        for name, pat in PATTERNS:
            for m in pat.finditer(v):
                hits[name].append('ch%s: …%s…' % (ch['index'], v[max(0, m.start() - 20):m.end() + 20].replace('\n', ' ')))
for name, lst in hits.items():
    print('%-24s %d' % (name, len(lst)))
    for h in lst[:5]:
        print('    ', h)

# 章字符量与块数
print()
total = 0
for fn in files:
    ch = json.load(open(os.path.join(D, fn), encoding='utf-8'))
    n = sum(len(b.get('value', '')) for b in ch.get('content', []))
    total += n
    print('  [%02d] %-14s %6d 字符 %3d 块' % (ch['index'], ch['title'][:14], n, len(ch.get('content', []))))
print('合计:', total)
