# -*- coding: utf-8 -*-
import json, glob
for p in glob.glob('f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/*.json'):
    d = json.load(open(p, encoding='utf-8'))
    if '尼采与哲学' in d.get('title', ''):
        print('尼采与哲学 bid:', d['bookId'])
        m = json.load(open(f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{d['bookId']}/meta.json", encoding='utf-8'))
        print('cc:', m['chapterCount'], '| toc:', [t['title'] for t in m['toc']])
        c0 = json.load(open(f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{d['bookId']}/0.json", encoding='utf-8'))
        print('章0 段落数:', len(c0['content']), '| 首段前80字:', repr(c0['content'][0]['value'][:80]))
        print('章0 前3段:', [repr(x['value'][:40]) for x in c0['content'][:3]])
        print('章0 尾段:', repr(c0['content'][-1]['value'][-60:]))
