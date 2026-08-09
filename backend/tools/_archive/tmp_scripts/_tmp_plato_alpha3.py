# -*- coding: utf-8 -*-
"""低频字母 H/V/M/J 与章15 SPHA 上下文 → 定清洗范围"""
import json, re

BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy'
D = BASE + '/backend/data/book_chapters/35279e2e439d'
meta = json.load(open(D + '/meta.json', encoding='utf-8'))

PAT = re.compile(r'(?<![A-Za-z0-9])[A-Z]{1,4}(?![A-Za-z0-9])')
for i, t in enumerate(meta['chapterTitles']):
    ch = json.load(open(D + '/%d.json' % i, encoding='utf-8'))
    text = '\n'.join(b.get('value', '') for b in ch.get('content', []))
    for m in PAT.finditer(text):
        g = m.group()
        if g in ('H', 'V', 'M', 'J', 'SPHA', 'SPH'):
            s = max(0, m.start() - 20)
            e = min(len(text), m.end() + 20)
            print('章%02d %-5s: %s' % (i, g, text[s:e].replace('\n', '|')))
