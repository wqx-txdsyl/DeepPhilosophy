# -*- coding: utf-8 -*-
"""读《资本论》: 页 250-258 详细内容, 定位第二部分标题页"""
import json

ckpt = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/dp_pdf_import_ckpt.json', encoding='utf-8'))
ocr = ckpt.get('ocr', {}).get('西方_路易_阿尔都塞_读_资本论_.pdf', {})

for p in range(250, 259):
    v = ocr.get(str(p), '')
    lines = [l.strip() for l in v.split('\n') if l.strip()] if v else []
    print('===== 页 %d =====' % p)
    for ln in lines[:8]:
        print('  ', ln[:48])
