# -*- coding: utf-8 -*-
"""边沁重建质量排查: 章内目录 vs 正文"""
import json, os

D = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/74ee21ced920'
for i in [0, 1, 2, 3]:
    ch = json.load(open(os.path.join(D, '%d.json' % i), encoding='utf-8'))
    blocks = ch['content']
    print('[%d] %s | %d 块' % (i, ch['title'][:30], len(blocks)))
    for b in blocks[:2]:
        print('    %s' % b['value'][:80])
    print()

# 搜正文标志句
for i in range(6):
    ch = json.load(open(os.path.join(D, '%d.json' % i), encoding='utf-8'))
    txt = ' '.join(b['value'] for b in ch['content'])
    for key in ['自然把人类置于', '两位主公', '功利原理']:
        if key in txt:
            print('[%d] 含[%s]' % (i, key))
