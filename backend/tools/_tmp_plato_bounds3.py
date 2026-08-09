# -*- coding: utf-8 -*-
"""看 692/693/694/705/706/707 块完整内容, 修正章15/16边界"""
import json, os

CD = r'F:\program\Python\DeepPhilosophy\DeepPhilosophy\backend\data\book_chapters\35279e2e439d'
blocks = []
for fi in (3, 4):
    ch = json.load(open(os.path.join(CD, '%d.json' % fi), encoding='utf-8'))
    for b in ch.get('content', []):
        blocks.append(b.get('value', ''))

for i in (692, 693, 694, 705, 706, 707):
    print('===[%d]===' % i)
    print(blocks[i][:400])
    print()
