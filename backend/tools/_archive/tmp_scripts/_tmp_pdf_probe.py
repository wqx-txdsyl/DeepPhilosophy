# -*- coding: utf-8 -*-
"""探测 现象学的观念.pdf 各页真实内容 (OCR 单页识别, 判断文件是否张冠李戴)"""
import os, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

import fitz
from paddleocr import PaddleOCR

FP = r'F:\philosophy\西方\埃德蒙德·胡塞尔\现象学的观念.pdf'
PAGES = [0, 1, 2, 5, 30, 60, 100, 126, 130, 140, 150, 153]

ocr = PaddleOCR(use_angle_cls=False, lang='ch', show_log=False)
doc = fitz.open(FP)
for i in PAGES:
    pix = doc[i].get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
    tmp = os.path.join(os.environ['TEMP'], 'probe_p%d.png' % i)
    pix.save(tmp)
    res = ocr.ocr(tmp, cls=False)
    txt = ' | '.join(r[1][0] for r in (res[0] or []) if r and r[1])
    print('== p%d (第 %d 页): %s' % (i, i + 1, txt[:200]))
doc.close()
