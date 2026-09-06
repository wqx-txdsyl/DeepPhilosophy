# -*- coding: utf-8 -*-
"""小说理论.pdf OCR 提取 (复用 dp_pdf_import 的 PaddleOCR 流程)。后台运行, 产物写入 mia_batch/xiaoshuo_ocr.txt"""
import sys, os, json, time

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
import dp_pdf_import as imp

FP = r'F:/philosophy/西方/格奥尔格·卢卡奇/小说理论.pdf'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mia_batch', 'xiaoshuo_ocr.txt')

t0 = time.time()
print('开始 OCR 小说理论.pdf ...', flush=True)
# ocr_pdf(fp, ckpt, safe) — ckpt 结构见 dp_pdf_import; 单进程内断点够用
ckpt = {"ocr": {}}
text = imp.ocr_pdf(FP, ckpt, 'xsll')
with open(OUT, 'w', encoding='utf-8') as f:
    f.write(text)
print(f'OCR 完成: {len(text)} 字, 耗时 {(time.time()-t0)/60:.1f} 分钟 -> {OUT}', flush=True)
