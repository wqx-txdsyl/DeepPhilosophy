# -*- coding: utf-8 -*-
"""读《资本论》: 找目录页(页70-100), 看章标题真实起始页"""
import json, re

ckpt = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/dp_pdf_import_ckpt.json', encoding='utf-8'))
ocr = ckpt.get('ocr', {}).get('西方_路易_阿尔都塞_读_资本论_.pdf', {})

# 扫描所有页, 找含章标题模式的行(一、引言 / 九、马克思的巨大的理论革命 等)
TIT = re.compile(r'^[一二三四五六七八九十]、')
for p in range(60, 120):
    v = ocr.get(str(p), '')
    if not v:
        continue
    lines = [l.strip() for l in v.split('\n') if l.strip()]
    for i, ln in enumerate(lines):
        if TIT.match(ln):
            print('页%d [%d]: %s' % (p, i, ln[:45]))
