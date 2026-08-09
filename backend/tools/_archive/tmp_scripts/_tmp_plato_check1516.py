# -*- coding: utf-8 -*-
"""检查重切后 15/16 章内容归属"""
import json

CD = r'F:\program\Python\DeepPhilosophy\DeepPhilosophy\backend\data\book_chapters\35279e2e439d'
for i in (15, 16):
    ch = json.load(open('%s/%d.json' % (CD, i), encoding='utf-8'))
    print('===[%d] %s: %d 块===' % (i, ch['title'], len(ch['content'])))
    for b in ch['content'][:3]:
        print('  首块:', b['value'][:120].replace('\n', '⏎'))
    print('  ...')
    for b in ch['content'][-2:]:
        print('  尾块:', b['value'][:120].replace('\n', '⏎'))
    print()
