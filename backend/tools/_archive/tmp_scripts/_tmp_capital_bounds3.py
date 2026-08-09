# -*- coding: utf-8 -*-
"""读《资本论》: 页 238-250 头部, 定位九讲结尾/附录/巴里巴尔总标题"""
import json

ckpt = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/dp_pdf_import_ckpt.json', encoding='utf-8'))
ocr = ckpt.get('ocr', {}).get('西方_路易_阿尔都塞_读_资本论_.pdf', {})

for p in range(238, 251):
    v = ocr.get(str(p), '')
    lines = [l.strip() for l in v.split('\n') if l.strip()] if v else []
    print('===== 页 %d (%d行) =====' % (p, len(lines)))
    for ln in lines[:6]:
        print('  ', ln[:48])
