# -*- coding: utf-8 -*-
"""临时: 自然与快乐 节标题行定位 + 译名对照表"""
import json, sys, re

sys.stdout.reconfigure(encoding="utf-8")
pages = json.load(open(r"f:/program/Python/DeepPhilosophy/DeepPhilosophy/scripts/qa_scripts/_xc_tmp_pages.json", encoding="utf-8"))
N = len(pages)

print("===== 书信类 节标题（'第N节' / 'N.' 开头的短行, p18-67）=====")
for k in range(18, 68):
    ls = [l.strip() for l in pages[str(k)].split("\n") if l.strip()]
    for i, l in enumerate(ls):
        n = re.sub(r"\s+", "", l)
        if (re.match(r"^第[一二三四五六七八九十]+节", n) or re.match(r"^\d+\.", n)) and len(n) <= 30:
            print(f"p{k} 行{i}: {n[:36]}")

print("\n===== 万物本性论 卷内节标题（p70-273, '第N节' 开头）=====")
for k in range(70, 274):
    ls = [l.strip() for l in pages[str(k)].split("\n") if l.strip()]
    for i, l in enumerate(ls[:6]):
        n = re.sub(r"\s+", "", l)
        if re.match(r"^第[一二三四五六七八九十]+节", n) and len(n) <= 30:
            print(f"p{k} 行{i}: {n[:36]}")

print("\n===== 尾页 p265-273 每页前 5 行（找译名对照表）=====")
for k in range(265, 274):
    ls = [l.strip() for l in pages[str(k)].split("\n") if l.strip()]
    print(f"p{k}: {ls[:5]}")
