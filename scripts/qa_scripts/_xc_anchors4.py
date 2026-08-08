# -*- coding: utf-8 -*-
"""临时: 验证 83/90/106/117/190/314 页标题行"""
import json, sys, re

sys.stdout.reconfigure(encoding="utf-8")
pages = json.load(open(r"f:/program/Python/DeepPhilosophy/DeepPhilosophy/scripts/qa_scripts/_xc_tmp_pages.json", encoding="utf-8"))

for pdf in [83, 90, 106, 117, 190, 314, 315]:
    print(f"===== PDF{pdf} =====")
    ls = [l.strip() for l in pages[str(pdf)].split("\n") if l.strip()]
    for l in ls[:10]:
        print(" ", l[:54])
