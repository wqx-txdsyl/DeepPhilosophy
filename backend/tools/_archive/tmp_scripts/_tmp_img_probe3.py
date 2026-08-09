# -*- coding: utf-8 -*-
"""验证污染页 p0020-p0027 残留图片的实际内容"""
import os, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

from paddleocr import PaddleOCR

TMP = os.path.join(os.environ['TEMP'], 'dp_paddle')
oc = PaddleOCR(use_angle_cls=False, lang='ch', show_log=False)

import fitz
# 1. 重导残留图片
for i in range(19, 30):
    f = os.path.join(TMP, '西方_埃德蒙德_胡塞尔_现象学的观念.pdf_p%04d.png' % i)
    if os.path.exists(f):
        res = oc.ocr(f, cls=False)
        txt = ' | '.join(r[1][0] for r in (res[0] or []) if r and r[1])
        print('残留图 p%04d (%dB): %s' % (i, os.path.getsize(f), txt[:70]))
    else:
        print('残留图 p%04d 缺失' % i)

# 2. 对照: PDF 实际渲染的 p0020 (书页4)
doc = fitz.open(r'F:\philosophy\西方\埃德蒙德·胡塞尔\现象学的观念.pdf')
pix = doc[20].get_pixmap(matrix=fitz.Matrix(1.2, 1.2))
img = os.path.join(os.environ['TEMP'], 'real_p0020.png')
pix.save(img)
res = oc.ocr(img, cls=False)
txt = ' | '.join(r[1][0] for r in (res[0] or []) if r and r[1])
print('PDF真实 p0020 (书页4): %s' % txt[:70])
doc.close()
