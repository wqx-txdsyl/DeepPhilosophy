# -*- coding: utf-8 -*-
"""临时: 606 全文"""
import json, sys

sys.stdout.reconfigure(encoding="utf-8")
pages = json.load(open(r"f:/program/Python/DeepPhilosophy/DeepPhilosophy/scripts/qa_scripts/_xc_tmp_pages.json", encoding="utf-8"))

ls = [l.strip() for l in pages["606"].split("\n") if l.strip()]
print(f"606 共 {len(ls)} 行")
for i, l in enumerate(ls):
    print(f"  {i}: {l[:65]}")
