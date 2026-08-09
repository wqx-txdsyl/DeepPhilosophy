# -*- coding: utf-8 -*-
"""对照实验: 用与重导完全相同的 PaddleOCR 参数连续 OCR 20 页, 验证参数差异"""
import os, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

import fitz
from paddleocr import PaddleOCR

FP = r'F:\philosophy\西方\埃德蒙德·胡塞尔\现象学的观念.pdf'
o = PaddleOCR(lang="ch", use_textline_orientation=True, cpu_threads=4)

doc = fitz.open(FP)
for i in range(20):
    pix = doc[i].get_pixmap(matrix=fitz.Matrix(1.2, 1.2))
    img = os.path.join(os.environ['TEMP'], 'ctrl_p%04d.png' % i)
    pix.save(img)
    r = o.ocr(img)
    txt = "\n".join(x[1][0] for x in (r[0] or []))
    print('p%03d | %s' % (i, txt[:26].replace('\n', ' ')))
doc.close()
