# -*- coding: utf-8 -*-
"""查尼采与哲学源 PDF 文本层: 卷/章标题形态"""
import sys, os, re, glob, fitz
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

hits = glob.glob(r"F:/philosophy/**/*尼采与哲学*.pdf", recursive=True)
print("候选:", hits)
if not hits:
    sys.exit(0)
p = hits[0]
doc = fitz.open(p)
print(f"页数 {len(doc)}  文本层总字数", sum(len(doc[i].get_text()) for i in range(len(doc))))
pat = re.compile(r"(第[一二三四五六七八九十]+[章卷部]|^\s*[一二三四五六七八九十]+[、\.．]\s*[^\n]{2,20}$|^\s*\d+[、\.．]\s*[^\n]{2,20}$)")
from collections import Counter
found = []
for i in range(len(doc)):
    t = doc[i].get_text()
    for m in pat.finditer(t):
        line = t[m.start():m.start()+25].replace("\n", "⏎")
        found.append((i, line))
# 汇总去重
seen = set()
for i, line in found:
    key = line[:14]
    if key in seen:
        continue
    seen.add(key)
    print(f"页{i:03d}  {line}")
doc.close()
