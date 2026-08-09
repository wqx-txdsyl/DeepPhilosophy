# -*- coding: utf-8 -*-
"""验证: 重导残留的 p0000-p0009 图片逐张 OCR, 与重导章节结果对比"""
import os, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

from paddleocr import PaddleOCR

TMP = os.path.join(os.environ['TEMP'], 'dp_paddle')
oc = PaddleOCR(use_angle_cls=False, lang='ch', show_log=False)

for i in range(10):
    f = os.path.join(TMP, '西方_埃德蒙德_胡塞尔_现象学的观念.pdf_p%04d.png' % i)
    if not os.path.exists(f):
        print('p%04d 缺失' % i); continue
    try:
        res = oc.ocr(f, cls=False)
        txt = ' | '.join(r[1][0] for r in (res[0] or []) if r and r[1])
    except Exception as e:
        txt = 'ERR: %s' % e
    print('== p%04d: %s' % (i, txt[:150]))
