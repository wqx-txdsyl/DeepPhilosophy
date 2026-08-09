# -*- coding: utf-8 -*-
"""边沁: 375-468 页结构 + 页 28"""
import json, re

ckpt = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/dp_pdf_import_ckpt.json', encoding='utf-8'))
ocr = ckpt.get('ocr', {}).get('西方_杰里米_边沁_道德与立法原理导论.pdf', {})

# 页 28
v = ocr.get('28', '')
print('===== 页 28 =====')
for ln in [l.strip() for l in v.split('\n') if l.strip()][:6]:
    print('  ', ln[:60])

# 375-468 每页前 4 行
TITLE = re.compile(r'^(附录|索引|译后记|后记|人名|名词|编者|第一卷|第二卷|跋|注)[^。！？]{0,25}$|^(第十七章[^。！？]{0,25})$')
print()
print('===== 375-468 每页首行 ====')
for p in range(375, 469):
    v = ocr.get(str(p), '')
    lines = [l.strip() for l in v.split('\n') if l.strip()]
    if not lines:
        continue
    first = lines[0][:45]
    # 只打印标题页(行0非页码/页眉)
    m = TITLE.match(lines[0]) if lines else None
    if m or p in (375, 376, 377, 395, 400, 420, 440, 460, 465, 468):
        print('页%d: %s' % (p, first))
