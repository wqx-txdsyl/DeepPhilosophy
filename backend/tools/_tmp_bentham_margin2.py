# -*- coding: utf-8 -*-
"""第十七章 边码候选样本 + 行尾页码混入检查"""
import json, os, re

D = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/74ee21ced920'
ch = json.load(open(os.path.join(D, '18.json'), encoding='utf-8'))

SEP = re.compile(r'(?<=[一-龥])\d{1,3}(?=[一-龥])')
BAD = re.compile(r'^[第后前年月日段卷页节条次号周期板序]')
ex = []
for b in ch.get('content', []):
    v = b.get('value', '')
    for m in SEP.finditer(v):
        pre = v[max(0, m.start() - 1):m.start()]
        if BAD.match(pre):
            continue
        if len(ex) < 16:
            ex.append(v[max(0, m.start() - 18):m.end() + 18].replace('\n', ' '))
print('--- 第十七章 边码候选样本 ---')
for e in ex:
    print('  ', e)

# 行尾页码混入: 块内 '\d+。' 或 行尾数字
print()
print('--- 含行尾页码特征的块(前 8) ---')
n = 0
for b in ch.get('content', []):
    v = b.get('value', '')
    if re.search(r'[一-龥]\d{1,4}[。，;；]?$', v):
        print('  ...%s' % v[-60:])
        n += 1
        if n >= 8:
            break
