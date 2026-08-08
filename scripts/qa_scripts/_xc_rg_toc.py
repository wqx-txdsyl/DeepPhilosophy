# -*- coding: utf-8 -*-
"""临时: 荣格心理学 目录全文(p5-8) + 边界页(p14,16,18,20,66,68,70,78,80,196-214)"""
import json, sys

sys.stdout.reconfigure(encoding="utf-8")
pages = json.load(open(r"f:/program/Python/DeepPhilosophy/DeepPhilosophy/scripts/qa_scripts/_xc_tmp_pages.json", encoding="utf-8"))

print("===== 目录全文 p5-8 =====")
for k in range(5, 9):
    ls = [l.strip() for l in pages[str(k)].split("\n") if l.strip()]
    print(f"--- p{k}:")
    for l in ls:
        print(f"    {l[:60]}")

print("\n===== 边界页 p14,16,18,20,66,68,70,78,80 (前10行) =====")
for k in [14, 16, 18, 20, 66, 68, 70, 78, 80]:
    ls = [l.strip() for l in pages[str(k)].split("\n") if l.strip()]
    print(f"--- p{k} ({len(ls)}行): {ls[:10]}")

print("\n===== p196-214 每页首3行 (找 荣格德语著述目录) =====")
for k in range(196, 215):
    ls = [l.strip() for l in pages[str(k)].split("\n") if l.strip()]
    print(f"p{k}: {ls[:3]}")
