# -*- coding: utf-8 -*-
"""政治学: 找正文第一章起始页(搜"我们见到每一个城邦"), 并看导读尾页"""
import json

ckpt = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/dp_pdf_import_ckpt.json', encoding='utf-8'))
ocr = ckpt.get('ocr', {}).get('西方_亚里士多德_政治学.pdf', {})
for p in sorted(int(k) for k in ocr):
    v = ocr.get(str(p), '')
    if '我们见到每一个城邦' in v or '每一个城邦' in v:
        lines = [l.strip() for l in v.split('\n') if l.strip()]
        print('页%d 含"每一个城邦", 前3行: %s' % (p, ' | '.join(l[:25] for l in lines[:3])))
    elif '吴恩裕' in v or '译者序' in v:
        print('页%d 含吴恩裕/译者序' % p)
