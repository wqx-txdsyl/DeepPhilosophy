# -*- coding: utf-8 -*-
"""与神对话重建后：第五卷结构人工对照抽查"""
import json, os

DP = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy'
BID = '7657ef4a2cd3'
m = json.load(open(os.path.join(DP, 'backend/data/book_chapters/%s/meta.json' % BID), encoding='utf-8'))
d = json.load(open(os.path.join(DP, 'app/public/book_detail/%s.json' % BID), encoding='utf-8'))

print('detail.toc == meta.toc:', d['toc'] == m['toc'])
print('chapterTitles 数:', len(d['chapterTitles']), len(m['chapterTitles']))
print()
print('=== 第五卷结构（index 92-116）===')
for t in m['toc']:
    if 92 <= t['index'] <= 116:
        print('   [%3s] %-9s lv=%s sec=%s %s' % (t['index'], t['type'], t.get('level'), t.get('sec'), t.get('title')))
print()
print('=== 各卷 part 一览 ===')
for t in m['toc']:
    if t['type'] == 'part':
        print('   [%3s] lv=%s %s' % (t['index'], t.get('level'), t['title']))
print()
print('=== chapterTitles 关键位（95/105/111 应为小章节标题）===')
print('  [95]:', m['chapterTitles'][95])
print('  [105]:', m['chapterTitles'][105])
print('  [111]:', m['chapterTitles'][111])
print('  [116]:', m['chapterTitles'][116])
