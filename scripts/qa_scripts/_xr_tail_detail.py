# -*- coding: utf-8 -*-
"""查尾部细节：页121/136/169 头部 + 页169-180 内容 + 页135 尾"""
import json
ck = json.load(open('f:/program/Python/PhiAgent/backend/data/dp_pdf_import_ckpt.json', encoding='utf-8'))
pages = ck['ocr']['西方_托马斯_库恩_结构之后的路.pdf']
for pn in (121, 135, 136, 168, 169, 170, 180):
    txt = str(pages[str(pn)])
    lines = [l.strip() for l in txt.split('\n') if l.strip()]
    print(f'=== 页{pn} ({len(lines)}行) ===')
    for l in lines[:14]:
        print('  ', repr(l[:50]))
    if len(lines) > 14:
        print('   ...尾部:', repr(lines[-2][:50]), '/', repr(lines[-1][:50]))
