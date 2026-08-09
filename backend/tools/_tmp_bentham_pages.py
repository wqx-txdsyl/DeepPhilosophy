# -*- coding: utf-8 -*-
"""边沁 ckpt 原始页结构诊断"""
import json

ckpt = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/dp_pdf_import_ckpt.json', encoding='utf-8'))
ocr = ckpt.get('ocr', {}).get('西方_杰里米_边沁_道德与立法原理导论.pdf', {})

# 全库搜正文标志句
all_text = ''
for k in sorted(int(x) for x in ocr):
    all_text += ocr[str(k)] or ''
for key in ['自然把人类置于', '两位主公', '第一章功利原理']:
    print('正文句[%s] 在 ckpt 中存在:' % key, key in all_text)

print()
print('===== 页 0-14 原始行 =====')
for p in range(15):
    v = ocr.get(str(p), '')
    lines = [l.strip() for l in v.split('\n') if l.strip()]
    print('--- 页 %d (%d 行) ---' % (p, len(lines)))
    for i, ln in enumerate(lines[:8]):
        print('   [%02d] %s' % (i, ln[:60]))
