# -*- coding: utf-8 -*-
"""验证: dp_paddle 残留图片与 probe 渲染图片是否同一内容"""
import os, io, sys, hashlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

from paddleocr import PaddleOCR

TMP = os.path.join(os.environ['TEMP'], 'dp_paddle')
oc = PaddleOCR(use_angle_cls=False, lang='ch', show_log=False)

# 1. 重导残留图片 (p0030) 的 OCR 结果
f1 = os.path.join(TMP, '西方_埃德蒙德_胡塞尔_现象学的观念.pdf_p0030.png')
f2 = os.path.join(TMP, 'probe_p30.png')  # 我自己渲染的
print('p0030.png 存在:', os.path.exists(f1), os.path.getsize(f1) if os.path.exists(f1) else '-')
print('probe_p30.png 存在:', os.path.exists(f2), os.path.getsize(f2) if os.path.exists(f2) else '-')
if os.path.exists(f1) and os.path.exists(f2):
    print('MD5 相同?', hashlib.md5(open(f1,'rb').read()).hexdigest() == hashlib.md5(open(f2,'rb').read()).hexdigest())
res = oc.ocr(f1, cls=False)
print('== p0030.png OCR:', ' | '.join(r[1][0] for r in (res[0] or []) if r and r[1])[:200])
res2 = oc.ocr(f2, cls=False)
print('== probe_p30.png OCR:', ' | '.join(r[1][0] for r in (res2[0] or []) if r and r[1])[:200])
