# -*- coding: utf-8 -*-
"""边沁重建抽查: 第一章全文 + 导言章尾注释区"""
import json, os

D = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/74ee21ced920'

def show(chid, label, n=14):
    ch = json.load(open(os.path.join(D, '%d.json' % chid), encoding='utf-8'))
    print('===== %s (%d 块) =====' % (label, len(ch['content'])))
    for i, b in enumerate(ch['content'][:n]):
        v = b['value']
        print('[%02d] %s' % (i, v[:150].replace('\n', ' ')))
    print()

show(2, '第一章 功利原理')
# 导言尾部 5 块
ch = json.load(open(os.path.join(D, '1.json'), encoding='utf-8'))
print('===== 导言尾部 3 块 =====')
for b in ch['content'][-3:]:
    print('--', b['value'][:150].replace('\n', ' '))
