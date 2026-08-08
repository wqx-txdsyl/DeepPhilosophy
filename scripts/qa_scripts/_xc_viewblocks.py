# -*- coding: utf-8 -*-
"""临时: 查看第一版序 blocks 结构 + 页末字符统计"""
import json, sys

sys.stdout.reconfigure(encoding="utf-8")
d = json.load(open(r"f:/program/Python/PhiAgent/backend/data/book_chapters/8c0c6955c793/3.json", encoding="utf-8"))
print("章:", d["title"], "块数:", len(d["content"]))
for i, b in enumerate(d["content"][:5]):
    v = b["value"]
    print(f"--块{i} ({len(v)}字): {v[:40]!r} ... {v[-20:]!r}")

pages = json.load(open(r"f:/program/Python/DeepPhilosophy/DeepPhilosophy/scripts/qa_scripts/_xc_tmp_pages.json", encoding="utf-8"))
print("\n页末字符统计 (18-26):")
for k in range(18, 27):
    ls = [l.strip() for l in pages[str(k)].split("\n") if l.strip()]
    if ls:
        print(f"  p{k} 末行: {ls[-1][-30:]!r}")
