# -*- coding: utf-8 -*-
"""读《资本论》: 全书章标题候选扫描(页, 行号, 文本), 用于 SECTIONS 定位"""
import json, re

ckpt = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/dp_pdf_import_ckpt.json', encoding='utf-8'))
ocr = ckpt.get('ocr', {}).get('西方_路易_阿尔都塞_读_资本论_.pdf', {})

TIT = re.compile(r'^[一二三四五六七八九十]{1,2}、')
for p in sorted(int(k) for k in ocr):
    v = ocr.get(str(p), '')
    if not v:
        continue
    lines = [l.strip() for l in v.split('\n') if l.strip()]
    for i, ln in enumerate(lines):
        if TIT.match(ln):
            # 去掉行内页码残字 (页[0] 式)
            print('页%-3d [%02d] %s' % (p, i, ln[:50]))
