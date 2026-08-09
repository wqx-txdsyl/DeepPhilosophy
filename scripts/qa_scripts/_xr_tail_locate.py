# -*- coding: utf-8 -*-
"""定位 121-180 页尾部结构：第十一章/后记/第三部分访谈标题行"""
import json, re
ck = json.load(open('f:/program/Python/PhiAgent/backend/data/dp_pdf_import_ckpt.json', encoding='utf-8'))
pages = ck['ocr']['西方_托马斯_库恩_结构之后的路.pdf']
for pn in range(121, 181):
    txt = str(pages[str(pn)])
    lines = [l.strip() for l in txt.split('\n') if l.strip()]
    marks = []
    for i, l in enumerate(lines[:8]):
        if re.match(r'^第[一二三]+部分', l) or '章' in l[:8] or l.startswith('■') or re.match(r'^\d{1,3}$', l) or l.startswith('结构之后') or '后记' in l or '讨论' in l[:12] or '访谈' in l:
            marks.append(f'{i}:{l[:30]}')
    print(f'--- 页{pn} ({len(lines)}行) ---')
    for m in marks:
        print('   ', m)
