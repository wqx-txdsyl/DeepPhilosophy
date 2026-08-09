# -*- coding: utf-8 -*-
"""看边沁 PDF 页 84-88(第一章区域) + 扫描全部章标题行"""
import json, re

ckpt = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/dp_pdf_import_ckpt.json', encoding='utf-8'))
ocr = ckpt.get('ocr', {}).get('西方_杰里米_边沁_道德与立法原理导论.pdf', {})

for p in range(84, 90):
    v = ocr.get(str(p), '')
    lines = [l.strip() for l in v.split('\n') if l.strip()]
    print('===== 页 %d (%d 行) =====' % (p, len(lines)))
    for i, ln in enumerate(lines[:10]):
        print('   [%02d] %s' % (i, ln[:60]))

print()
print('===== 全库章标题行(行首第X章/导言/附录/索引, 短行) =====')
TITLE = re.compile(r'^(第[一二三四五六七八九十百\d]+[章节]|导言|附录|索引|结语|结论)[^。！？]{0,25}$')
for p in sorted(int(x) for x in ocr):
    v = ocr.get(str(p), '')
    if not v:
        continue
    lines = [l.strip() for l in v.split('\n') if l.strip()]
    for i, ln in enumerate(lines):
        if TITLE.match(ln) and len(ln) <= 30 and i <= 10:
            print('  页%d 行%d: %s' % (p, i, ln))
