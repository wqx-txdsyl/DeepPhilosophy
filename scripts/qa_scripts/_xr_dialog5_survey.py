# -*- coding: utf-8 -*-
"""工具论 chapterTitles 构成 + 与神对话 meta 现状"""
import json, os

DP = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy'

d = json.load(open(os.path.join(DP, 'app/public/book_detail/b471f41a78de.json'), encoding='utf-8'))
print('工具论 chapterTitles:')
print(' ', d['chapterTitles'])
print()

m = json.load(open(os.path.join(DP, 'backend/data/book_chapters/7657ef4a2cd3/meta.json'), encoding='utf-8'))
print('与神对话 meta: toc=%d chapterCount=%r chapterTitles=%d' % (len(m['toc']), m.get('chapterCount'), len(m.get('chapterTitles', []))))
print('meta toc 类型分布:')
from collections import Counter
print(' ', dict(Counter((t.get('type'), t.get('level')) for t in m['toc'])))
print('meta 前 3 条:', json.dumps(m['toc'][:3], ensure_ascii=False)[:250])
print('meta chapterTitles 前 5:', m.get('chapterTitles', [])[:5])
print('meta chapterTitles 后 5:', m.get('chapterTitles', [])[-5:])
