# -*- coding: utf-8 -*-
"""临时: 导言页/丢弃页/尾行检查"""
import json, sys, re

sys.stdout.reconfigure(encoding="utf-8")
pages = json.load(open(r"f:/program/Python/DeepPhilosophy/DeepPhilosophy/scripts/qa_scripts/_xc_tmp_pages.json", encoding="utf-8"))

print("===== 57-78 导言页 前 2 非空行 =====")
for k in range(57, 79):
    ls = [l.strip() for l in pages[str(k)].split("\n") if l.strip()]
    print(f"p{k}: {ls[:2]}")

print("\n===== 79-80 / 604-605 / 756 丢弃页全文(≤12 行) =====")
for k in [79, 80, 604, 605, 756]:
    ls = [l.strip() for l in pages[str(k)].split("\n") if l.strip()]
    print(f"--- p{k} ({len(ls)}行): {ls[:12]}")

print("\n===== 含'附'独立行(无路径前缀) 取样 =====")
seen = set()
for k in range(N := 756):
    for l in pages[str(k)].split("\n"):
        s = l.strip()
        if not s or "附" not in s or "版原文" not in s:
            continue
        if re.match(r"^[［\[【！(]?\s*附?第?[一二三四五六七八九十百\-\.]{0,6}版原文", s) and not s.startswith("第"):
            if s not in seen:
                seen.add(s)
                print(f"p{k}: {s[:40]}")
    if len(seen) >= 15:
        break
