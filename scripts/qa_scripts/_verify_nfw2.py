# -*- coding: utf-8 -*-
"""零丢失验证: 旧 75 章全文 ⊆ 新 5 章全文（连续子串）+ 逐卷覆盖"""
import sys, os, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
NEW = r"f:/program/Python/PhiAgent/backend/data/book_chapters/e7c27b39a87c"
OLD = r"f:/program/Python/PhiAgent/backend/data/_rebuild_bak/e7c27b39a87c_old75ch"

def full(bd, n):
    parts = []
    for i in range(n):
        c = json.load(open(f"{bd}/{i}.json", encoding="utf-8"))
        parts.append("".join(x["value"] for x in c["content"] if x.get("type") == "text"))
    return "".join(parts)

old_txt = full(OLD, 75)
new_txt = full(NEW, 5)
print("旧全文长度:", len(old_txt), " 新全文长度:", len(new_txt))
i = new_txt.find(old_txt)
print("旧全文在新全文中的位置:", i, "(≥0 = 连续包含 ✓)")
# 每章包含验证
vols = [(0, 0, 16), (1, 16, 31), (2, 31, 46), (3, 46, 62), (4, 62, 75)]
for vi, s, e in vols:
    old_v = "".join(
        "".join(x["value"] for x in json.load(open(f"{OLD}/{i}.json", encoding="utf-8"))["content"] if x.get("type") == "text")
        for i in range(s, e))
    new_c = json.load(open(f"{NEW}/{vi}.json", encoding="utf-8"))
    new_v = "".join(x["value"] for x in new_c["content"] if x.get("type") == "text")
    # 剥离的卷残留字符串
    print(f"第{vi+1}章: 旧节{s}-{e-1} 旧len={len(old_v)} 新len={len(new_v)} 包含={new_v.find(old_v) >= 0}")
