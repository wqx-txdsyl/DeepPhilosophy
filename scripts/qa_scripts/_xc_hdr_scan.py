# -*- coding: utf-8 -*-
"""临时: 扫全书页眉实况 + 0-14 页前件内容"""
import json, sys, re
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")
pages = json.load(open(r"f:/program/Python/DeepPhilosophy/DeepPhilosophy/scripts/qa_scripts/_xc_tmp_pages.json", encoding="utf-8"))
N = len(pages)
print("总页数:", N)

print("\n===== 0-14 页前件(每页前 4 非空行) =====")
for k in range(0, 15):
    ls = [l.strip() for l in pages[str(k)].split("\n") if l.strip()]
    print(f"--- p{k}: {ls[:4]}")

print("\n===== 每页首非空行 频次(Counter, top 40) =====")
c = Counter()
for k in range(N):
    ls = [l.strip() for l in pages[str(k)].split("\n") if l.strip()]
    if ls:
        c[ls[0][:40]] += 1
for line, cnt in c.most_common(40):
    print(f"{cnt:3d}  {line}")

print("\n===== 含'第'和'·'的路径类行(取样 25, 含页码) =====")
seen = set()
for k in range(N):
    for l in pages[str(k)].split("\n"):
        s = l.strip()
        if not s or "第" not in s:
            continue
        if re.search(r"[一二三四五六七八九十百\-]*[部分编卷章节]·", s) and s not in seen:
            seen.add(s)
for s in list(seen)[:25]:
    # 找所在页
    pg = next(str(k) for k in range(N) if s in pages[str(k)])
    print(f"p{pg}: {s[:50]}")
