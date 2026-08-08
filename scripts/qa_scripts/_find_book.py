# -*- coding: utf-8 -*-
import sys, os, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CH = r"f:/program/Python/PhiAgent/backend/data/book_chapters"
for b in sorted(os.listdir(CH)):
    mfp = os.path.join(CH, b, "meta.json")
    if os.path.exists(mfp):
        m = json.load(open(mfp, encoding="utf-8"))
        t = m.get("title", "")
        if "论人类不平等" in t or "不平等" in t:
            print(b, repr(t), "章节数:", m.get("chapterCount"), "作者:", m.get("author"))
