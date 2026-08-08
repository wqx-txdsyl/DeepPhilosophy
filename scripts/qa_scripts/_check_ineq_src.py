# -*- coding: utf-8 -*-
"""查源 PDF 文本层: 页序/注释块/标题页分布"""
import sys, os, re, glob, fitz
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
hits = glob.glob(r"F:/philosophy/**/*不平等*.pdf", recursive=True)
print("候选:", hits)
if not hits:
    sys.exit(0)
doc = fitz.open(hits[0])
print(f"页数 {len(doc)} 文本层总字数 {sum(len(doc[i].get_text()) for i in range(len(doc)))}")
# 每页首 2 行 + 含"注释"关键词页标记
for i in range(len(doc)):
    t = doc[i].get_text()
    lines = [l.strip() for l in t.split("\n") if l.strip()]
    head = " / ".join(lines[:3])[:80]
    print(f"页{i:03d} {len(t):6d}字 | {head}")
doc.close()
