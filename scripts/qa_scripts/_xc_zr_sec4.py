# -*- coding: utf-8 -*-
"""临时: 万物本性论全部节标题行全面扫描（数字. / 汉字数字开头短行）+ p74/p124 全文"""
import json, sys, re

sys.stdout.reconfigure(encoding="utf-8")
pages = json.load(open(r"f:/program/Python/DeepPhilosophy/DeepPhilosophy/scripts/qa_scripts/_xc_tmp_pages.json", encoding="utf-8"))

print("===== 万物本性论 p70-268: 数字/汉字数字开头短行（≤18字）=====")
PAT = re.compile(r"^(?:\d+|[一二三四五六七八九十]{1,2})[.．、]?[一-龥A-Za-z①-⑳]{1,16}$")
for k in range(70, 269):
    ls = [l.strip() for l in pages[str(k)].split("\n") if l.strip()]
    for i, l in enumerate(ls):
        n = re.sub(r"\s+", "", l)
        if PAT.match(n) and not n.startswith("第"):
            print(f"p{k} 行{i}: {n}")

print("\n===== p74 全文 =====")
for i, l in enumerate([l.strip() for l in pages["74"].split("\n") if l.strip()]):
    print(f"p74 行{i}: {l}")

print("\n===== p124 行18-28 =====")
ls = [l.strip() for l in pages["124"].split("\n") if l.strip()]
for i, l in enumerate(ls[18:29], 18):
    print(f"p124 行{i}: {l}")

print("\n===== 第二卷中后部 p114-129: 前 4 行结构 =====")
for k in range(114, 130):
    ls = [l.strip() for l in pages[str(k)].split("\n") if l.strip()]
    hdr = ls[0] if ls else ""
    if re.search(r"\d+[.．]|^[一二三四五六七八九十]{1,2}[一-龥]", hdr):
        print(f"p{k} 行0: {hdr}")
