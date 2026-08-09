# -*- coding: utf-8 -*-
"""边码(中文间夹数字)统计 + 总目录章抽查"""
import json, os, re

D = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/74ee21ced920'
files = [f for f in os.listdir(D) if re.match(r'^\d+\.json$', f)]

# 边码: 一-龥 数字(1-3位) 一-龥, 排除 第X/年X/月X/X日/X段/X卷/X版/X页/X节/X条/X次/X号/X年
SEP = re.compile(r'(?<=[一-龥])\d{1,3}(?=[一-龥])')
BAD = re.compile(r'^[第后前年月日段卷页节条次号周期板序]')
total = 0
per_ch = {}
for fn in sorted(files, key=lambda x: int(x.split('.')[0])):
    ch = json.load(open(os.path.join(D, fn), encoding='utf-8'))
    n = 0
    ex = []
    for b in ch.get('content', []):
        v = b.get('value', '')
        for m in SEP.finditer(v):
            pre = v[max(0, m.start() - 1):m.start()]
            if BAD.match(pre):
                continue
            n += 1
            if len(ex) < 3:
                ex.append(v[max(0, m.start() - 12):m.end() + 12].replace('\n', ' '))
    per_ch[ch['title']] = n
    total += n
print('边码候选(中夹数字) 总数:', total)
for t, n in per_ch.items():
    if n:
        print('  %-16s %d' % (t[:16], n))

# 总目录章抽查
ch = json.load(open(os.path.join(D, '0.json'), encoding='utf-8'))
print()
print('总目录 块数:', len(ch['content']))
for b in ch['content'][:10]:
    print('  |', b['value'][:60])
print('  ...')
for b in ch['content'][-6:]:
    print('  |', b['value'][:60])
