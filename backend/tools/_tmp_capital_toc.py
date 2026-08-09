# -*- coding: utf-8 -*-
"""读《资本论》目录页提取(页0-25)"""
import json, re

ckpt = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/dp_pdf_import_ckpt.json', encoding='utf-8'))
ocr = ckpt.get('ocr', {}).get('西方_路易_阿尔都塞_读_资本论_.pdf', {})
print('OCR 页:', len(ocr))
for p in range(0, 26):
    v = ocr.get(str(p), '')
    if not v:
        continue
    lines = [l.strip() for l in v.split('\n') if l.strip()]
    print('===== 页 %d (%d 行) =====' % (p, len(lines)))
    for ln in lines[:12]:
        print('  ', ln[:55])
