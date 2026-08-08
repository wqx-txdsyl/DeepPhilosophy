# -*- coding: utf-8 -*-
"""批量跑 dp_ocr_check: 遍历全部 PDF 入库书(含 OCR 标记), 汇总非 ✓ 项"""
import sys, os, json, re, io
sys.path.insert(0, r"f:\program\Python\DeepPhilosophy\DeepPhilosophy\backend\tools")
sys.path.insert(0, r"f:\program\Python\PhiAgent\backend\tools")
import dp_ocr_check

BASE = r"f:\program\Python\PhiAgent\backend\data"
CH = os.path.join(BASE, "book_chapters")

# 收集 PDF 书: book_detail 有 file_type=pdf 或 extract=ocr, 且 book_chapters 存在
pdfs = []
for f in os.listdir(os.path.join(BASE, "book_detail")):
    if not f.endswith(".json"):
        continue
    d = json.load(open(os.path.join(BASE, "book_detail", f), encoding="utf-8"))
    bid = d.get("bookId")
    if not bid or not os.path.exists(os.path.join(CH, bid, "meta.json")):
        continue
    ft = d.get("file_type")
    ex = d.get("extract")
    if ft == "pdf" or ex == "ocr":
        pdfs.append((bid, d.get("title", ""), ft, ex))
pdfs.sort(key=lambda x: x[0])
print(f"PDF/OCR 书 {len(pdfs)} 本\n", flush=True)

results = {}
import contextlib, io as _io
for bid, title, ft, ex in pdfs:
    print(f"=== {bid} {title[:20]} [{ft}/{ex}] ===", flush=True)
    cap = _io.StringIO()
    with contextlib.redirect_stdout(cap):
        try:
            dp_ocr_check.main(bid)
        except Exception as e:
            print(f"  !! 异常: {e}")
    out = cap.getvalue()
    bad = [ln for ln in out.splitlines() if ("✗" in ln or "⚠" in ln) and "[" in ln]
    results[bid] = (title, bad)
    if bad:
        print("  -> 非✓:", " | ".join(b.strip()[:60] for b in bad), flush=True)

print("\n\n===== 汇总: 全部 PDF 书非 ✓ 项 =====", flush=True)
nfail_total = 0
for bid, (title, bad) in sorted(results.items()):
    if bad:
        nfail_total += 1
        print(f"{bid} {title[:24]}:", flush=True)
        for b in bad:
            print(f"    {b.strip()}", flush=True)
print(f"\n有问题的书: {nfail_total}/{len(pdfs)}", flush=True)
