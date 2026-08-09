# -*- coding: utf-8 -*-
"""边沁: 从总目录页提取章名顺序 + 定位正文标题页"""
import json, re

ckpt = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/dp_pdf_import_ckpt.json', encoding='utf-8'))
ocr = ckpt.get('ocr', {}).get('西方_杰里米_边沁_道德与立法原理导论.pdf', {})

TITLE_RE = re.compile(r'^(第[一二三四五六七八九十百\d]+[章节卷篇部]|导言|前言|序|附录|索引|绪论|结论)[^。！？]{0,30}$')

# 1. 目录页(4-14)的章名行 = 真实章节顺序
toc_chapters = []
for p in range(4, 15):
    v = ocr.get(str(p), '')
    if not v:
        continue
    for ln in [l.strip() for l in v.split('\n') if l.strip()]:
        m = TITLE_RE.match(ln)
        if m and len(ln) < 40:
            toc_chapters.append((p, ln))

print('总目录章节行 (%d 条):' % len(toc_chapters))
for p, t in toc_chapters:
    print('  页%d: %s' % (p, t[:45]))

# 2. 正文标题页定位: 全库找同名短行
print()
print('正文标题定位:')
for p, t in toc_chapters:
    key = t
    # 找正文页里的同名行（跳过目录页本身）
    found = []
    for q in sorted(int(x) for x in ocr):
        if q <= 15:
            continue
        v = ocr[str(q)]
        if not v:
            continue
        for ln in [l.strip() for l in v.split('\n') if l.strip()]:
            if ln == key or ln.startswith(key):
                found.append(q)
                break
    print('  %s -> PDF 页 %s' % (t[:35], found[:2] or '未找到'))
