# -*- coding: utf-8 -*-
"""自然辩证法：重复 index 章节 + 33/34/35 细目章内容形态"""
import json, os

BID = 'aa21ac425e87'
BASE = f'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}'

m = json.load(open(os.path.join(BASE, 'meta.json'), encoding='utf-8'))
print('=== toc 重复 index ===')
seen = {}
for t in m['toc']:
    seen.setdefault(t['index'], []).append(t['title'])
for idx, titles in seen.items():
    if len(titles) > 1:
        print(f'  [{idx}]', ' / '.join(titles))

print()
for fi in (33, 34, 35, 32):
    c = json.load(open(os.path.join(BASE, f'{fi}.json'), encoding='utf-8'))
    print(f'=== [{fi}] {c.get("title","")[:40]} 段数 {len(c["content"])} ===')
    for b in c['content'][:10]:
        v = b.get('value', '')
        print('  |', v[:55].replace(chr(10), ' ⏎ '))
    print()
