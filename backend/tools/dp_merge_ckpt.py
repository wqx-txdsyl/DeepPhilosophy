# -*- coding: utf-8 -*-
"""dp_merge_ckpt.py — 合并并行 OCR 的 shard checkpoint 到主 ckpt"""
import sys, io, os, json

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/
MAIN = os.path.join(BASE, "data", "dp_pdf_import_ckpt.json")

main = json.load(open(MAIN, encoding="utf-8")) if os.path.exists(MAIN) else {"books": {}, "ocr": {}}
merged_books, merged_ocr = 0, 0
for s in range(1, 8):
    sp = os.path.join(BASE, "data", f"dp_pdf_import_ckpt_s{s}.json")
    if not os.path.exists(sp):
        continue
    d = json.load(open(sp, encoding="utf-8"))
    nb = 0
    for k, v in d.get("books", {}).items():
        if k not in main.get("books", {}):
            main.setdefault("books", {})[k] = v
            nb += 1
    merged_books += nb
    for k, v in d.get("ocr", {}).items():
        if k not in main.get("ocr", {}):
            main.setdefault("ocr", {})[k] = v
            merged_ocr += 1
    print(f"  s{s}: +{nb} books, ocr {len(d.get('ocr', {}))} 条", flush=True)
json.dump(main, open(MAIN, "w", encoding="utf-8"), ensure_ascii=False)
print(f"合并完成: books {len(main.get('books', {}))}, ocr {len(main.get('ocr', {}))}（新增 {merged_books} books / {merged_ocr} ocr）", flush=True)
