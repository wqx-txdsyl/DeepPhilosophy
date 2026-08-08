# -*- coding: utf-8 -*-
"""列出所有 epub 源的书 (book_detail file_type)"""
import sys, os, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DD = r"f:\program\Python\PhiAgent\backend\data\book_detail"
n = 0
epubs = []
for f in sorted(os.listdir(DD)):
    if not f.endswith(".json"):
        continue
    bid = f[:-5]
    try:
        j = json.load(open(os.path.join(DD, f), encoding="utf-8"))
    except Exception:
        continue
    ft = j.get("file_type") or j.get("fileType") or ""
    src = j.get("source") or j.get("src") or j.get("path") or ""
    if "epub" in ft.lower() or ".epub" in src.lower():
        n += 1
        epubs.append((j.get("title", bid), bid, ft, src))
print(f"epub 源书: {n} 本")
for t, bid, ft, src in sorted(epubs):
    print(f"  {t} | {bid} | {ft} | {src[:70]}")
