# -*- coding: utf-8 -*-
"""新工具核查：打印 OCR 目录页（页2-4）原文 + 最后一页，对照书内结构"""
import json
CK = 'f:/program/Python/PhiAgent/backend/data/dp_pdf_import_ckpt.json'
SAFE = '西方_弗朗西斯_培根_新工具.pdf'
ck = json.load(open(CK, encoding='utf-8'))
pages = ck['ocr'][SAFE]
print('总页数: %d' % len(pages))
for k in ['0', '1', '2', '3', '4']:
    if k in pages:
        print('--- OCR 页 %s ---' % k)
        print(pages[k][:600])
last = sorted(pages, key=int)[-1]
print('--- OCR 最后一页 %s ---' % last)
print(pages[last][:400])
