# -*- coding: utf-8 -*-
"""临时: 万物本性论卷内节标题全页扫描 + 卷标题页格式"""
import json, sys, re

sys.stdout.reconfigure(encoding="utf-8")
pages = json.load(open(r"f:/program/Python/DeepPhilosophy/DeepPhilosophy/scripts/qa_scripts/_xc_tmp_pages.json", encoding="utf-8"))

print("===== 万物本性论 '第N节' 标题（全行扫描, p70-268）=====")
for k in range(70, 269):
    ls = [l.strip() for l in pages[str(k)].split("\n") if l.strip()]
    for i, l in enumerate(ls):
        n = re.sub(r"\s+", "", l)
        if re.match(r"^第[一二三四五六七八九十百]+节", n) and len(n) <= 28:
            print(f"p{k} 行{i}: {n}")

print("\n===== 卷标题页（p70/99/130/161/195/233 每页前 8 行）=====")
for k in (70, 99, 130, 161, 195, 233):
    ls = [l.strip() for l in pages[str(k)].split("\n") if l.strip()]
    print(f"--- p{k}: {ls[:8]}")
