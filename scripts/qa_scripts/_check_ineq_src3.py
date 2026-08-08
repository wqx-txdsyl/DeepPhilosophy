# -*- coding: utf-8 -*-
import sys, os, json, hashlib, glob
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CK = json.load(open(r"f:/program/Python/PhiAgent/backend/data/dp_pdf_import_ckpt.json", encoding="utf-8"))
books = CK.get("books", {})
print("ckpt books 总数:", len(books))
hit = None
for k in books:
    if "不平等" in k:
        hit = k
        print("命中 rel:", k)
        b = books[k]
        print("books 条目键:", list(b.keys()))
        print("pages 数量:", len(b.get("pages", {})))
        break
if not hit:
    # 全库找含"不平等"的 rel
    for k in books:
        if "卢梭" in k:
            print("卢梭 rel:", k)
# OCR 段: 找含不平等的 safe
for k in CK.get("ocr", {}):
    if "不平等" in k:
        print("ocr 段键:", k, "页数:", len(CK["ocr"][k]))
# 源文件全局搜索
for p in glob.glob(r"F:/philosophy/**/*.pdf", recursive=True):
    if "不平等" in p:
        print("源:", p)
