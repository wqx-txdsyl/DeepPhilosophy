# -*- coding: utf-8 -*-
"""自然辩证法 aa21ac425e87 结构调查：章节标题/段落切分/[num] 残留"""
import json, os, re

BID = 'aa21ac425e87'
BASE = f'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}'

# 1) 段落切分统计：全库段长分布 + 极短段
print('=== 全书段落形态统计 ===')
short_paras = {}  # 3字以内段的样本
num_split = []    # 含 [数字] 的段
for f in sorted(os.listdir(BASE)):
    if not f.endswith('.json') or f == 'meta.json':
        continue
    c = json.load(open(os.path.join(BASE, f), encoding='utf-8'))
    title = c.get('title', '')
    for b in c['content']:
        v = b.get('value', '') if isinstance(b, dict) else ''
        if not isinstance(v, str):
            continue
        s = v.strip()
        if len(s) <= 3:
            short_paras.setdefault(f, []).append(s[:20])
        if re.search(r'\[\d{1,4}\]', s):
            num_split.append((f, s[:60]))

print('极短段(≤3字) 文件分布:')
for f, lst in short_paras.items():
    print(f'  [{f}] {len(lst)} 条, 样本: {lst[:5]}')

print()
print(f'含 [数字] 的段总数: {len(num_split)}')
for f, s in num_split[:12]:
    print(f'  [{f}] {s}')

# 2) 细看章3 导言 段落形态
print()
print('=== 章3 导言 段落形态 ===')
c = json.load(open(os.path.join(BASE, '3.json'), encoding='utf-8'))
print('段数:', len(c['content']))
for i, b in enumerate(c['content'][:15]):
    v = b.get('value', '')
    print(f'  {i}| len={len(v)} | {v[:50].replace(chr(10), "⏎")}')

# 3) toc 标题原文里 [] 分布
print()
print('=== toc [] 标题统计 ===')
m = json.load(open(os.path.join(BASE, 'meta.json'), encoding='utf-8'))
bt = sum(1 for t in m['toc'] if '[' in t['title'])
print(f'带[]的toc条目: {bt}/{len(m["toc"])}')
