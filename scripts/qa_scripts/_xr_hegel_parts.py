# -*- coding: utf-8 -*-
"""黑格尔分级抽查：14 part 边界 + detail.toc==meta.toc + 无重复 index 断点"""
import json, os

BID = 'bbac1be0bb4b'
DP = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy'

m = json.load(open(os.path.join(DP, 'backend/data/book_chapters/%s/meta.json' % BID), encoding='utf-8'))
toc = m['toc']
d = json.load(open(os.path.join(DP, 'app/public/book_detail/%s.json' % BID), encoding='utf-8'))

# 1. detail.toc == meta.toc
print('1) detail.toc == meta.toc:', d['toc'] == toc)
print('   detail.chapterTitles 数:', len(d['chapterTitles']), ' meta.chapterTitles 数:', len(m['chapterTitles']))

# 2. part 边界抽查：每个 part 后首章 + part 前尾章
print()
print('2) 14 part 边界（part | 卷内首章 | 卷内尾章 | 下卷首章）:')
parts = [t for t in toc if t['type'] == 'part']
print('   part 数:', len(parts))
for i, p in enumerate(parts):
    # 卷内章节
    start = p['index']
    end = parts[i + 1]['index'] - 1 if i + 1 < len(parts) else 444
    chs = [t for t in toc if t['type'] == 'chapter' and start <= t['index'] <= end]
    first = chs[0]['title'] if chs else '?'
    last = chs[-1]['title'] if chs else '?'
    nxt = parts[i + 1]['title'] if i + 1 < len(parts) else '-'
    print('   [%3d-%3d] %-24s | 首:%s | 尾:%s | 下:%s' % (start, end, p['title'], first[:16], last[:16], nxt[:18]))

# 3. part 条目 index 都在其卷内
print()
print('3) 每卷 part.index == 卷内最小章 index:', all(p['index'] == min(t['index'] for t in toc if t['type'] == 'chapter' and p['index'] <= t['index'] <= (parts[i+1]['index']-1 if i+1 < len(parts) else 444)) for i, p in enumerate(parts)))

# 4. toc 里 chapter 条目连续性（index 从 0..444 每个恰好出现一次）
idxs = [t['index'] for t in toc if t['type'] == 'chapter']
print()
print('4) chapter index 连续 0..444:', idxs == list(range(445)))
