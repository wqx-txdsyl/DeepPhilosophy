# -*- coding: utf-8 -*-
"""尼采与哲学重建收尾: books.json chapterCount 5→6 + ckpt 清理"""
import sys, json, os, re

sys.stdout.reconfigure(encoding="utf-8")

# 1) books.json chapterCount（两端）
for bj in [r"f:/program/Python/PhiAgent/app/public/books.json",
           r"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"]:
    books = json.load(open(bj, encoding="utf-8"))
    tag = os.path.basename(os.path.dirname(os.path.dirname(bj)))
    for b in books:
        if b.get("id") == "e7c27b39a87c":
            print(f"books.json[{tag}] chapterCount: {b.get('chapterCount')} → 6")
            b["chapterCount"] = 6
    json.dump(books, open(bj, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("步骤4 OK")

# 2) ckpt: 删 ocr 记录（防重扫再走 OCR 覆盖）+ books 记录 src 更新
ckp = r"f:/program/Python/PhiAgent/backend/data/dp_pdf_import_ckpt.json"
ck = json.load(open(ckp, encoding="utf-8"))
rel = "西方/吉尔·德勒兹/尼采与哲学.pdf"
safe = re.sub(r"[^\w\-.]", "_", rel)
if safe in ck.get("ocr", {}):
    del ck["ocr"][safe]
    print("ckpt ocr 记录已删:", safe)
else:
    print("ckpt ocr 无此记录（无需删）")
for k, v in list(ck.get("books", {}).items()):
    if k == rel:
        if isinstance(v, dict):
            v["src"] = "text_layer"
        print("ckpt books 更新:", k, "→", v if isinstance(v, dict) else v)
json.dump(ck, open(ckp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("步骤5 OK")
