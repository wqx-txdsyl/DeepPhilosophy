# -*- coding: utf-8 -*-
"""临时: 自然与快乐 目录全文 + 篇章/卷标题定位"""
import json, sys, re

sys.stdout.reconfigure(encoding="utf-8")
pages = json.load(open(r"f:/program/Python/DeepPhilosophy/DeepPhilosophy/scripts/qa_scripts/_xc_tmp_pages.json", encoding="utf-8"))
N = len(pages)

print("===== 目录 p14-15 全文 =====")
for k in (14, 15):
    ls = [l.strip() for l in pages[str(k)].split("\n") if l.strip()]
    print(f"--- p{k}:")
    for l in ls:
        print(f"    {l}")

print("\n===== 上编各篇标题（第X/七/八/九 开头行 + 书信标题行）=====")
PATS = ["致希罗多德信", "致皮索克勒信", "致梅瑙凯信", "遗嘱", "临终书信", "基本要道", "梵蒂冈", "贤人论", "奥依诺安达", "第[一二三四五六七八九]卷", "序诗"]
for k in range(16, 274):
    ls = [l.strip() for l in pages[str(k)].split("\n") if l.strip()]
    for i, l in enumerate(ls[:4]):
        n = re.sub(r"\s+", "", l)
        for p in PATS:
            if re.match(p, n):
                print(f"p{k} 行{i}: {n[:50]}")
                break
