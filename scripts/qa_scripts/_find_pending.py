# -*- coding: utf-8 -*-
"""找出 F:/philosophy 中未完成 OCR 的 PDF（不在 ckpt 或 ckpt 里有 fail 页）"""
import sys, os, json
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
import fitz

CKPT = r"f:\program\Python\PhiAgent\backend\data\dp_pdf_import_ckpt.json"
ck = json.load(open(CKPT, encoding="utf-8"))
ocr = ck.get("ocr", {})

print(f"ckpt 中已登记 OCR 书: {len(ocr)} 本\n")
print("═══ 未在 ckpt 中的 PDF（从未 OCR 或未完成）═══")
for p in sorted(Path(r"F:\philosophy").rglob("*.pdf")):
    rel = p.as_posix().replace("F:/philosophy/", "")
    if rel not in ocr:
        try:
            doc = fitz.open(str(p))
            n = doc.page_count
            doc.close()
            print(f"  {n:4d}页  {rel}")
        except Exception as e:
            print(f"  打开失败 {rel}: {e}")

print("\n═══ ckpt 中带 fail 页的书（断点续传会重跑）═══")
for k in sorted(ocr):
    d = ocr[k]
    if not isinstance(d, dict):
        continue
    failed = sum(1 for v in d.values() if v == "__FAILED__" or (isinstance(v, str) and not v.strip()))
    if failed:
        print(f"  fail={failed:3d}  {k}")
