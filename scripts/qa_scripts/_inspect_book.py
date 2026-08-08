# -*- coding: utf-8 -*-
"""查看一本书的文本层结构: python _inspect_book.py <书名关键词> [前N页]"""
import sys, os, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import fitz

kw = sys.argv[1]
N = int(sys.argv[2]) if len(sys.argv) > 2 else 12
src = None
for root, dirs, files in os.walk(r"F:\philosophy"):
    for f in files:
        if f.lower().endswith(".pdf") and kw in f:
            src = os.path.join(root, f)
            break
    if src: break
if not src:
    print("未找到:", kw); sys.exit(1)
print("源:", src)
d = fitz.open(src)
print("页数:", len(d))
for i in range(min(N, len(d))):
    t = d[i].get_text().strip().replace(chr(10), " ")[:90]
    if t: print(f"[p{i}] {t}")
d.close()
