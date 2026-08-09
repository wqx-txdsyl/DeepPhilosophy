# -*- coding: utf-8 -*-
"""页 216 前 22 行 + 页 215 尾部"""
import json

ckpt = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/dp_pdf_import_ckpt.json', encoding='utf-8'))
ocr = ckpt.get('ocr', {}).get('西方_路易_阿尔都塞_读_资本论_.pdf', {})
for p in (215, 216):
    lines = [l.strip() for l in ocr.get(str(p), '').split('\n') if l.strip()]
    print('===== 页 %d (%d行) =====' % (p, len(lines)))
    for i, ln in enumerate(lines):
        print('  [%02d] %s' % (i, ln[:50]))
