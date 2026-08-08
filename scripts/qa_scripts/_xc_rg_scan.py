# -*- coding: utf-8 -*-
"""临时: 荣格心理学 全页扫描 —— 定位 绪论/各章/传略/索引/附录 标题页"""
import json, sys, re

sys.stdout.reconfigure(encoding="utf-8")
pages = json.load(open(r"f:/program/Python/DeepPhilosophy/DeepPhilosophy/scripts/qa_scripts/_xc_tmp_pages.json", encoding="utf-8"))
N = len(pages)

PATS = ["绪论", "第一章", "第二章", "第三章", "荣格传略", "人名索引", "名词术语", "著述目录", "附录"]
print(f"总页数 {N}\n===== 标题候选页（命中行 + 上下文 2 行）=====")
for k in range(N):
    ls = [l.strip() for l in pages[str(k)].split("\n") if l.strip()]
    for i, l in enumerate(ls):
        n = re.sub(r"\s+", "", l)
        for p in PATS:
            if n.startswith(p) or n == p:
                ctx = ls[max(0, i-2):i+4]
                print(f"\n--- p{k} 行{i}: {n}")
                for c in ctx:
                    print(f"    {c[:40]}")
                break
