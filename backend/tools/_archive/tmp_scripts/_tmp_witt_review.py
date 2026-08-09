# -*- coding: utf-8 -*-
"""维特根斯坦文集重导后: 85 章字符量/标题序列 + ncx 树结构 → 设计层级 toc"""
import json, os, zipfile, re
from bs4 import BeautifulSoup

B = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy'
D = B + '/backend/data/book_chapters/c0e78ea6f80a'

m = json.load(open(D + '/meta.json', encoding='utf-8'))
print('meta chapterCount:', m.get('chapterCount'), '| toc:', len(m.get('toc') or []), '| chapterTitles:', len(m.get('chapterTitles') or []))

print()
print('=== 85 章字符量 ===')
sizes = []
for i in range(m.get('chapterCount', 0)):
    ch = json.load(open(D + '/%d.json' % i, encoding='utf-8'))
    n = sum(len(b.get('value', '')) for b in ch.get('content', []))
    sizes.append(n)
    flag = ' <-- 空壳' if n < 800 else (' <-- 超大' if n > 80000 else '')
    print('%2d %-34s %7d%s' % (i, (ch.get('title') or '?')[:30], n, flag))

print()
print('=== ncx 树（卷级/章级）===')
EP = r'F:/philosophy/西方/路德维希·维特根斯坦/《维特根斯坦文集（套装全8卷）》.epub'
with zipfile.ZipFile(EP) as z:
    ncx = BeautifulSoup(z.read('toc.ncx').decode('utf-8', 'ignore'), 'xml')
    for np in ncx.find_all('navPoint', recursive=False):
        lab = np.find('text')
        lv = np.find('navPoint')
        sub = [s.find('text').text.strip()[:30] for s in (np.find_all('navPoint') if lv else [])]
        print('卷: %s' % lab.text.strip()[:40])
        for s in sub:
            print('    └ %s' % s)
