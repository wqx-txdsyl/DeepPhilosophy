# -*- coding: utf-8 -*-
"""政治学: 找导读正文去向(页3"在亚里士多德之前…") + 章 0 内容结构"""
import json, os, re

D = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/53b09f03e24e'
ch0 = json.load(open(os.path.join(D, '0.json'), encoding='utf-8'))
print('章0 keys:', list(ch0.keys()))
print('章0 content 类型:', type(ch0.get('content')).__name__, '长度:', len(ch0.get('content') or []))
print('章0 完整:', json.dumps(ch0, ensure_ascii=False)[:300])

files = sorted([f for f in os.listdir(D) if re.match(r'^\d+\.json$', f)], key=lambda x: int(x.split('.')[0]))
found = []
for fn in files:
    ch = json.load(open(os.path.join(D, fn), encoding='utf-8'))
    for b in ch.get('content', []):
        if '在亚里士多德之前' in b.get('value', '') or '吴恩裕' in b.get('value', ''):
            found.append((fn, ch.get('title'), b.get('value', '')[:40]))
print('导读内容所在章:', found[:5])
