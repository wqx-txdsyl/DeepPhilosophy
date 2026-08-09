# -*- coding: utf-8 -*-
"""查霍布斯 ckpt 原始行: 用户报告的 3 处残留注释/断词"""
import json, re

ckpt = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/dp_pdf_import_ckpt.json', encoding='utf-8'))
ocr = ckpt.get('ocr', {}).get('西方_托马斯_霍布斯_托马斯_霍布斯.pdf', {})

KEY = ['至关重要', '尽管词汇表述不同', '经设计面来的国家', '译者注', '毋宁说', '意\n志']

for k in sorted(int(x) for x in ocr):
    v = ocr[str(k)]
    if not v:
        continue
    lines = [l.strip() for l in v.split('\n') if l.strip()]
    for i, ln in enumerate(lines):
        if any(t in ln for t in ['至关重要', '尽管词汇表述不同', '经设计面来的国家', '译者注']):
            print('页%d 行%d: [%s]' % (k, i, ln[:90]))
print()
print('--- 所有含"毋宁说"的行 ---')
for k in sorted(int(x) for x in ocr):
    v = ocr[str(k)]
    if not v:
        continue
    for i, ln in enumerate([l.strip() for l in v.split('\n') if l.strip()]):
        if '毋宁说' in ln:
            print('页%d 行%d: [%s]' % (k, i, ln[:90]))
