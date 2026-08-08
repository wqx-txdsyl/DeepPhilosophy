# -*- coding: utf-8 -*-
"""临时: 找"先验感性论的结论"标题行"""
import json, sys, re

sys.stdout.reconfigure(encoding="utf-8")
pages = json.load(open(r"f:/program/Python/DeepPhilosophy/DeepPhilosophy/scripts/qa_scripts/_xc_tmp_pages.json", encoding="utf-8"))

for pdf in range(104, 110):
    for li, l in enumerate(pages[str(pdf)].split("\n")):
        n = re.sub(r"\s+", "", l)
        if n and ("结论" in n or "感性论" in n):
            print(f"PDF{pdf} 行{li}: {l.strip()[:60]}")
