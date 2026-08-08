# -*- coding: utf-8 -*-
"""找尼采与哲学节标题出现页 + 前后页首行, 定位卷边界与卷标题形态"""
import sys, os, re, fitz
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
doc = fitz.open(r"F:/philosophy/西方/吉尔·德勒兹/尼采与哲学.pdf")
PATS = ["系谱学概念", "身体", "人文科学的改造", "反动与怨恨", "虚无主义（nihilisme）", "试金石", "永恒回归的问题", "思想的新形象", "反动力的胜利", "狄奥尼索斯和查拉斯图特拉"]
hits = []
for i in range(len(doc)):
    t = doc[i].get_text()
    for p in PATS:
        if p in t and re.search(r"^[0-9]{1,2}\.\s?" + re.escape(p[:6]), t, re.M):
            hits.append((i, p))
# 节标题页: 打印该页前 8 行 + 下页前 4 行
for i, p in hits:
    t = doc[i].get_text()
    lines = [l.strip() for l in t.split("\n") if l.strip()]
    print(f"\n=== 页{i}: 命中 {p!r}")
    print("  本页前8行:", " / ".join(lines[:8])[:160])
    t2 = doc[i+1].get_text() if i+1 < len(doc) else ""
    lines2 = [l.strip() for l in t2.split("\n") if l.strip()]
    print("  下页前4行:", " / ".join(lines2[:4])[:120])
doc.close()
