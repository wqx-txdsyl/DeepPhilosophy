# -*- coding: utf-8 -*-
"""临时: 自然与快乐 前 70 页扫描 —— 书名页/目录/上编下编结构"""
import json, sys

sys.stdout.reconfigure(encoding="utf-8")
pages = json.load(open(r"f:/program/Python/DeepPhilosophy/DeepPhilosophy/scripts/qa_scripts/_xc_tmp_pages.json", encoding="utf-8"))
N = len(pages)
print("总页数:", N)

print("\n===== 0-70 页(每页前 6 非空行) =====")
for k in range(0, 71):
    ls = [l.strip() for l in pages[str(k)].split("\n") if l.strip()]
    print(f"p{k}: {ls[:6]}")
