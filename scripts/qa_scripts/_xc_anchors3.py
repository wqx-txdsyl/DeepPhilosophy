# -*- coding: utf-8 -*-
"""临时: 法规第一节标题行搜索"""
import json, sys, re

sys.stdout.reconfigure(encoding="utf-8")
pages = json.load(open(r"f:/program/Python/DeepPhilosophy/DeepPhilosophy/scripts/qa_scripts/_xc_tmp_pages.json", encoding="utf-8"))

for pdf in range(662, 667):
    print(f"===== PDF{pdf} =====")
    ls = [l.strip() for l in pages[str(pdf)].split("\n") if l.strip()]
    for l in ls[:12]:
        print(" ", l[:56])
