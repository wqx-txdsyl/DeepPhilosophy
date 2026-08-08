# -*- coding: utf-8 -*-
"""临时: 荣格心理学 前 14 页(书名页/目录) + 各章标题定位"""
import json, sys, re

sys.stdout.reconfigure(encoding="utf-8")
pages = json.load(open(r"f:/program/Python/DeepPhilosophy/DeepPhilosophy/scripts/qa_scripts/_xc_tmp_pages.json", encoding="utf-8"))
N = len(pages)
print("总页数:", N)

print("\n===== 0-13 页(每页前 8 非空行) =====")
for k in range(0, 14):
    ls = [l.strip() for l in pages[str(k)].split("\n") if l.strip()]
    print(f"--- p{k}: {ls[:8]}")

print("\n===== 目录类页(0-20 全文) =====")
for k in range(0, 21):
    ls = [l.strip() for l in pages[str(k)].split("\n") if l.strip()]
    if any("章" in l or "前言" in l or "录" in l for l in ls[:6]):
        print(f"--- p{k}: {ls}")
