# -*- coding: utf-8 -*-
import sys, os, json, glob
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
bid = "9e4f98733f0b"
for dp in (r"f:/program/Python/PhiAgent/backend/data/book_detail",
           r"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_detail",
           r"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail"):
    p = os.path.join(dp, f"{bid}.json")
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))
        print(p)
        for k, v in d.items():
            if k not in ("toc", "chapterTitles", "chapterCount"):
                print("  ", k, "=", repr(v)[:150])
        break
# epub 源
for root in (r"F:/philosophy", r"f:/program/Python/PhiAgent/backend/data"):
    for p in glob.glob(root + "/**/*.epub", recursive=True):
        if "不平等" in p:
            print("epub 源:", p)
