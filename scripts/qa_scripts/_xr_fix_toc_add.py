# -*- coding: utf-8 -*-
"""自然与快乐 toc 补缺：正文有标题合并块、toc 缺对应节条
- 卷4(index15): '1.影像的本性与速度' sec=5   （正文块5 "1.·影像的本性与速度"+正文）
- 卷6(index17): '3."无鸟之湖"，奇特的泉水' sec=132（正文块132 同）
PA meta.json + book_detail.json 双补，插入位置按 sec 升序
"""
import json, sys
sys.stdout.reconfigure(encoding='utf-8')

PA_BC = 'f:/program/Python/PhiAgent/backend/data/book_chapters/221f09d04944/meta.json'
PA_BD = 'f:/program/Python/PhiAgent/backend/data/book_detail/221f09d04944.json'

NEW = [
    {'type': 'section', 'title': '1.影像的本性与速度', 'index': 15, 'sec': 5, 'level': 2},
    {'type': 'section', 'title': '3.“无鸟之湖”，奇特的泉水', 'index': 17, 'sec': 132, 'level': 2},
]

def insert_toc(toc, item):
    # 找同 index 且 sec > item.sec 的首条 → 插其前（保持 sec 升序）
    for i, e in enumerate(toc):
        if e.get('index') == item['index'] and e.get('sec', 0) > item['sec']:
            toc.insert(i, item)
            return i
    # 兜底：插到同 index 最后一个 section 之后
    last = -1
    for i, e in enumerate(toc):
        if e.get('index') == item['index'] and e.get('type') == 'section':
            last = i
    toc.insert(last + 1, item)
    return last + 1

for p in (PA_BC, PA_BD):
    d = json.load(open(p, encoding='utf-8'))
    toc = d['toc']
    already = [item['title'] for item in NEW if any(e.get('title') == item['title'] for e in toc)]
    if already:
        print('%s 已存在: %s' % (p, already))
        continue
    for item in NEW:
        pos = insert_toc(toc, item)
        print('%s 插入 %s @%d' % (p, item['title'], pos))
    json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
    print('  条数 %d' % len(toc))
