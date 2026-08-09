# -*- coding: utf-8 -*-
"""政治学: 找正文第一章标题页 + 导读尾页"""
import json, re

ckpt = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/dp_pdf_import_ckpt.json', encoding='utf-8'))
ocr = ckpt.get('ocr', {}).get('西方_亚里士多德_政治学.pdf', {})
print('OCR 页:', len(ocr))
for p in sorted(int(k) for k in ocr):
    v = ocr.get(str(p), '')
    lines = [l.strip() for l in v.split('\n') if l.strip()] if v else []
    for i, ln in enumerate(lines):
        if ln == '第一章' or ln.startswith('第一卷'):
            print('页%-3d [%02d]: %s' % (p, i, ln[:40]))
