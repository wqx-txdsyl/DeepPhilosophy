# -*- coding: utf-8 -*-
"""边界案例: I/II/III/SAP/SP 的上下文 + 孤立字母的形态统计 (单独成行 vs 嵌句中)"""
import json, re

BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy'
D = BASE + '/backend/data/book_chapters/35279e2e439d'
meta = json.load(open(D + '/meta.json', encoding='utf-8'))

PAT = re.compile(r'(?<![A-Za-z0-9])[A-Z]{1,4}(?![A-Za-z0-9])')
# 单独成行 vs 嵌句中
alone = 0
inline = 0
ctx = []
for i, t in enumerate(meta['chapterTitles']):
    ch = json.load(open(D + '/%d.json' % i, encoding='utf-8'))
    text = '\n'.join(b.get('value', '') for b in ch.get('content', []))
    lines = text.split('\n')
    for ln in lines:
        s = ln.strip()
        if PAT.fullmatch(s):
            alone += 1
    for m in PAT.finditer(text):
        before = text[max(0, m.start() - 1):m.start()]
        after = text[m.end():m.end() + 1]
        # 行边界视为中文字境
        if (before and (before.isalpha())) or (after and after.isalpha()):
            continue  # 英文词内
        if '\n' in before or '\n' in after or before == '' or after == '':
            pass
        # 嵌句中: 两侧中文
        ctx.append((i, m.group(), text[max(0, m.start() - 12):m.end() + 12].replace('\n', '|')))
        inline += 1
print('单独成行: %d, 嵌句中: %d' % (alone, inline))

print('\n== I/II/III/SAP/SP 上下文 ==')
seen = set()
for i, g, c in ctx:
    if g in ('I', 'II', 'III', 'SAP', 'SP', 'S', 'P', 'L'):
        k = (g, c)
        if k in seen:
            continue
        seen.add(k)
        print('章%02d %-4s: %s' % (i, g, c))
    if len(seen) > 25:
        break

print('\n== 嵌句中全部字母频次 ==')
from collections import Counter
cnt = Counter(g for _, g, _ in ctx)
print(dict(cnt.most_common(15)))
