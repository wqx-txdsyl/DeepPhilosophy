# -*- coding: utf-8 -*-
"""读《资本论》: 边界页检查 (78-83, 256-261, 383-388)"""
import json

ckpt = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/dp_pdf_import_ckpt.json', encoding='utf-8'))
ocr = ckpt.get('ocr', {}).get('西方_路易_阿尔都塞_读_资本论_.pdf', {})

for p in list(range(78, 84)) + list(range(256, 262)) + list(range(383, 389)):
    v = ocr.get(str(p), '')
    if not v:
        print('页%d: (无文本)' % p)
        continue
    lines = [l.strip() for l in v.split('\n') if l.strip()]
    head = ' | '.join(l[:22] for l in lines[:3])
    tail = ' | '.join(l[:22] for l in lines[-2:])
    print('页%-3d (%2d行) %s ||| 尾: %s' % (p, len(lines), head[:70], tail[:50]))
