# -*- coding: utf-8 -*-
"""皮尔斯文选: 孤立大写字母检查 (同类 Stephanus/页边标注?)"""
import json, re

BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy'
D = BASE + '/backend/data/book_chapters/8b1e1c5ebaac'
meta = json.load(open(D + '/meta.json', encoding='utf-8'))

PAT = re.compile(r'(?<![A-Za-z0-9])[A-Z]{1,4}(?![A-Za-z0-9])')
ALONE = re.compile(r'^[A-Z]{1,4}$')
alone = 0
inline = 0
samples = []
for i, t in enumerate(meta['chapterTitles']):
    ch = json.load(open(D + '/%d.json' % i, encoding='utf-8'))
    text = '\n'.join(b.get('value', '') for b in ch.get('content', []))
    for ln in text.split('\n'):
        if ALONE.match(ln.strip()):
            alone += 1
    for m in PAT.finditer(text):
        before = text[max(0, m.start() - 1):m.start()]
        after = text[m.end():m.end() + 1]
        if (before and before.isalpha()) or (after and after.isalpha()):
            continue
        inline += 1
        if len(samples) < 15:
            s = max(0, m.start() - 15); e = min(len(text), m.end() + 15)
            samples.append('章%02d %-4s: %s' % (i, m.group(), text[s:e].replace('\n', '|')))
print('单独成行: %d, 嵌句中: %d' % (alone, inline))
print('== 样本 ==')
for s in samples:
    print(' ', s)
