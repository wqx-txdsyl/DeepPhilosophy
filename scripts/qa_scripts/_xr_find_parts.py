# -*- coding: utf-8 -*-
"""技术与时间 + 哲学科学全书纲要 的 level 层级编码"""
import json

for bid, name in [('06e202800bb2', '技术与时间'), ('497b0228c3a6', '哲学科学全书纲要')]:
    m = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/%s/meta.json' % bid, encoding='utf-8'))
    toc = m['toc']
    print('=' * 20, name, 'toc=%d' % len(toc))
    lv = {}
    for t in toc:
        lv.setdefault(t.get('level'), []).append(t)
    print('level 分布:', {k: len(v) for k, v in lv.items()})
    print('--- level 值清单（按出现顺序）---')
    seen = []
    for t in toc:
        l = t.get('level')
        if l not in seen:
            seen.append(l)
            print('  level=%r  首条: %s' % (l, (t.get('title') or '')[:30]))
    print('--- 前 12 条 ---')
    for t in toc[:12]:
        print('   [%s] level=%r type=%r sec=%r %s' % (t.get('index'), t.get('level'), t.get('type'), t.get('sec'), (t.get('title') or '')[:36]))
    print()
