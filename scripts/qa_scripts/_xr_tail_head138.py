# -*- coding: utf-8 -*-
import json, re
ck = json.load(open('f:/program/Python/PhiAgent/backend/data/dp_pdf_import_ckpt.json', encoding='utf-8'))
pages = ck['ocr']['西方_托马斯_库恩_结构之后的路.pdf']
for pn in range(138, 143):
    lines = [l.strip() for l in str(pages[str(pn)]).split('\n') if l.strip()]
    print(f'--- 页{pn} 头8行 ({len(lines)}行) ---')
    for i, l in enumerate(lines[:8]):
        print(f'  {i}| {l[:50]}')
# 找所有 '2.5x' 或带小数点的页码残留
print('\n=== 全书 2.5x 页码残留搜索 ===')
for pn in range(121, 181):
    lines = [l.strip() for l in str(pages[str(pn)]).split('\n') if l.strip()]
    for i, l in enumerate(lines[:5]):
        if re.match(r'^2\.\d\d', l):
            print(f'  页{pn} 行{i}: {l[:40]}')
