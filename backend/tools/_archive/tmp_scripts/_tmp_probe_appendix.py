# -*- coding: utf-8 -*-
"""探测现象学的观念 PDF 附录区 (p88-p153) 每页 OCR 首行 + 页眉, 搞清书尾真实结构"""
import os, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

import fitz
from paddleocr import PaddleOCR

FP = r'F:\philosophy\西方\埃德蒙德·胡塞尔\现象学的观念.pdf'
doc = fitz.open(FP)
print('总页数:', doc.page_count)
o = PaddleOCR(lang="ch", use_textline_orientation=True, cpu_threads=4)

for i in range(85, doc.page_count):
    pix = doc[i].get_pixmap(matrix=fitz.Matrix(1.0, 1.0))
    img = os.path.join(os.environ['TEMP'], 'probe_%04d.png' % i)
    pix.save(img)
    r = o.ocr(img)
    lines = [x[1][0] for x in (r[0] or [])]
    txt = ' '.join(lines)
    # 页眉 = 首行, 页脚页码 = 末行
    head = lines[0][:18] if lines else ''
    tail = lines[-1][:6] if lines else ''
    body = txt[:24]
    print('p%03d | %s | %s | %s' % (i, head, tail, body))
    os.remove(img)
doc.close()
