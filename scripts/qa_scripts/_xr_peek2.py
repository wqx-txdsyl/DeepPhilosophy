# -*- coding: utf-8 -*-
"""新工具核查：关键页原文 + 2.json 关键串定位 + PDF 真实页数"""
import json, os, re
CK = 'f:/program/Python/PhiAgent/backend/data/dp_pdf_import_ckpt.json'
SAFE = '西方_弗朗西斯_培根_新工具.pdf'
ck = json.load(open(CK, encoding='utf-8'))
pages = ck['ocr'][SAFE]

for k in ['5', '10', '11', '109', '110']:
    if k in pages:
        print('===== OCR 页 %s（书内页 %d）=====' % (k, int(k) - 4))
        print(pages[k])
        print()

print('===== OCR 页 294（书内页 290）=====')
print(pages.get('294', '缺失')[:1500])
print()
print('===== OCR 页 295（书内页 291）全文 =====')
print(pages.get('295', '缺失'))
