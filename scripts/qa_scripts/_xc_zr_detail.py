# -*- coding: utf-8 -*-
"""临时: 自然与快乐 孤立单字行 + 关键页细节"""
import json, sys, re

sys.stdout.reconfigure(encoding="utf-8")
pages = json.load(open(r"f:/program/Python/DeepPhilosophy/DeepPhilosophy/scripts/qa_scripts/_xc_tmp_pages.json", encoding="utf-8"))

print("===== 孤立单字'一~九'行（p3-273）=====")
for k in range(3, 274):
    ls = [l.strip() for l in pages[str(k)].split("\n") if l.strip()]
    for i, l in enumerate(ls):
        n = re.sub(r"\s+", "", l)
        if re.match(r"^[一二三四五六七八九]$", n):
            print(f"p{k} 行{i}: {n}  上下文: {ls[max(0,i-1):i+2]}")

print("\n===== 关键页详情 =====")
for k in (49, 50, 51, 67, 68, 69, 98, 99, 124, 125, 129, 130, 160, 161, 268, 269, 272, 273):
    ls = [l.strip() for l in pages[str(k)].split("\n") if l.strip()]
    print(f"--- p{k} ({len(ls)}行): {ls[:8]}")
