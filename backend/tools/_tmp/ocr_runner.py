# -*- coding: utf-8 -*-
"""通用 OCR 提取: python ocr_runner.py <pdf路径> <输出txt> — 复用 dp_pdf_import 的 PaddleOCR 流程"""
import sys, os
pdf, out = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import dp_pdf_import as imp
ckpt = {"ocr": {}}
text = imp.ocr_pdf(pdf, ckpt, os.path.basename(pdf))
with open(out, 'w', encoding='utf-8') as f:
    f.write(text)
print('DONE', len(text))
