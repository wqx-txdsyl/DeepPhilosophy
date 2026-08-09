# -*- coding: utf-8 -*-
"""探测现象学的观念 前置区 p0-p19 每页内容 (封面/总序/编者引论/目录)"""
import os, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

import fitz
from paddleocr import PaddleOCR

FP = r'F:\philosophy\西方\埃德蒙德·胡塞尔\现象学的观念.pdf'
doc = fitz.open(FP)
o = PaddleOCR(lang="ch", use_textline_orientation=True, cpu_threads=4)

for i in range(0, 20):
    pix = doc[i].get_pixmap(matrix=fitz.Matrix(1.0, 1.0))
    img = os.path.join(os.environ['TEMP'], 'front_%04d.png' % i)
    pix.save(img)
    r = o.ocr(img)
    lines = [x[1][0] for x in (r[0] or [])]
    head = lines[0][:16] if lines else '(空)'
    tail = lines[-1][:10] if lines else ''
    body = ''.join(lines)[:22]
    print('p%03d | %s | %s | %s' % (i, head, tail, body))
    os.remove(img)
doc.close()
