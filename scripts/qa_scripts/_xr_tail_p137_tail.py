# -*- coding: utf-8 -*-
import json
ck = json.load(open('f:/program/Python/PhiAgent/backend/data/dp_pdf_import_ckpt.json', encoding='utf-8'))
pages = ck['ocr']['西方_托马斯_库恩_结构之后的路.pdf']
for pn in (137, 138):
    lines = [l.strip() for l in str(pages[str(pn)]).split('\n') if l.strip()]
    print(f'===== 页{pn} 尾10行 ({len(lines)}行) =====')
    for i, l in enumerate(lines[-10:], start=len(lines) - 10):
        print(f'{i:2d}| {l[:60]}')
