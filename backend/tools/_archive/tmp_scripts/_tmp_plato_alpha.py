# -*- coding: utf-8 -*-
"""探查柏拉图对话集里突然出现的孤立大写字母 (ABCDEF...) 的来源与分布"""
import json, re, os

BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy'
D = BASE + '/backend/data/book_chapters/35279e2e439d'
meta = json.load(open(D + '/meta.json', encoding='utf-8'))
titles = meta['chapterTitles']

# 孤立大写字母: 两侧不是字母/数字的单个或多个大写字母
PAT = re.compile(r'(?<![A-Za-z0-9])[A-Z]{1,3}(?![A-Za-z0-9])')

print('== 各章孤立大写字母统计 ==')
total = 0
for i, t in enumerate(titles):
    ch = json.load(open(D + '/%d.json' % i, encoding='utf-8'))
    text = '\n'.join(b.get('value', '') for b in ch.get('content', []))
    ms = PAT.findall(text)
    if ms:
        print('章%02d %-16s: %d 个 %s' % (i, t[:16], len(ms), ms[:8]))
        total += len(ms)
print('总计: %d 个孤立大写字母' % total)

# 抽样看上下文 (前 40 个)
print('\n== 上下文抽样 (前 40 个) ==')
n = 0
for i, t in enumerate(titles):
    ch = json.load(open(D + '/%d.json' % i, encoding='utf-8'))
    text = '\n'.join(b.get('value', '') for b in ch.get('content', []))
    for m in PAT.finditer(text):
        s = max(0, m.start() - 18)
        e = min(len(text), m.end() + 18)
        print('章%02d: …%s…' % (i, text[s:e].replace('\n', '|')))
        n += 1
        if n >= 40:
            break
    if n >= 40:
        break
