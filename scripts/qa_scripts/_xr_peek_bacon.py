# -*- coding: utf-8 -*-
"""新工具核查：打印各章首/尾片段供人工逐条核对"""
import json, os
OUT = os.path.dirname(os.path.abspath(__file__)) + '/_xr_out_bacon'
for f in sorted(os.listdir(OUT)):
    p = os.path.join(OUT, f)
    d = json.load(open(p, encoding='utf-8'))
    if f == 'meta.json':
        print('=== meta.json ===')
        print('title=%s author=%s cc=%d' % (d['title'], d['author'], d['chapterCount']))
        for t in d['toc']:
            print('  toc[%d] %s' % (t['index'], t['title']))
        continue
    v = d['content'][0]['value']
    print('=== %s === title=%r len=%d' % (f, d['title'], len(v)))
    print('-- 开头 250 字:')
    print(v[:250])
    print('-- 结尾 250 字:')
    print(v[-250:])
    print()
