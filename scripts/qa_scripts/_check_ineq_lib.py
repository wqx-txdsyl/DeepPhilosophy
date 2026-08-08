# -*- coding: utf-8 -*-
"""看库 9e4f98733f0b 当前: meta + 各章首尾段"""
import sys, re, json, glob
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
base = r"f:\program\Python\PhiAgent\backend\data\book_chapters\9e4f98733f0b"
m = json.load(open(base + r"\meta.json", encoding="utf-8"))
print("meta keys:", list(m.keys()))
print("chapterCount:", m.get("chapterCount"))
for t in m.get("toc", []):
    print("  toc:", json.dumps(t, ensure_ascii=False))
import os
print("\nfiles:", sorted(os.listdir(base)))
for f in sorted(os.listdir(base)):
    if f.endswith(".txt") and f.startswith("chapter"):
        c = open(os.path.join(base, f), encoding="utf-8").read()
        paras = [p.strip() for p in c.split("\n") if p.strip()]
        print(f"\n== {f} len={len(c)} 段数={len(paras)}")
        print("  首:", paras[0][:80] if paras else "")
        print("  尾:", paras[-1][:80] if paras else "")
