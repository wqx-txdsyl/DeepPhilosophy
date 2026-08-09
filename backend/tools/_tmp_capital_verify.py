# -*- coding: utf-8 -*-
"""读《资本论》重建验证: 注释块位置 + 残留扫描"""
import json, os, re

D = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/b3219ec260ed'
PATTERNS = [
    ('孤立页码', re.compile(r'(?m)^\d{1,4}$')),
    ('页眉行', re.compile(r'(?m)^读《资本论》$|^从《资本论》到马克思的哲学$|^关于历史唯物主义的基本概念$|^资本论》的对象$')),
    ('中缝单行', re.compile(r'(?m)^[一-龥A-Za-z]{1,2}$')),
    ('@残留', re.compile(r'@')),
]
for chid in [12, 18]:
    ch = json.load(open(os.path.join(D, '%d.json' % chid), encoding='utf-8'))
    print('===== [%d] %s (%d 块) 尾部 3 块 =====' % (ch['index'], ch['title'], len(ch['content'])))
    for b in ch['content'][-3:]:
        print('  |', b['value'][:120].replace('\n', ' '))
    print()

for fn in sorted(os.listdir(D)):
    if not re.match(r'^\d+\.json$', fn):
        continue
    ch = json.load(open(os.path.join(D, fn), encoding='utf-8'))
    for blk in ch.get('content', []):
        v = blk.get('value', '')
        for name, pat in PATTERNS:
            for m in pat.finditer(v):
                print('残留 %s [%s]: …%s…' % (name, ch['title'][:10], v[max(0, m.start() - 15):m.end() + 15].replace('\n', ' ')))
