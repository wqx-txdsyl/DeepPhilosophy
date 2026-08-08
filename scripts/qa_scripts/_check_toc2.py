# -*- coding: utf-8 -*-
"""看柏拉图/增广贤文 toc 中与 chapterTitles 不一致的条目"""
import sys, os, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CH = r"f:/program/Python/PhiAgent/backend/data/book_chapters"
for bid, name in (("e74dc59d508e", "柏拉图"), ("e863b4cca50d", "增广贤文")):
    m = json.load(open(os.path.join(CH, bid, "meta.json"), encoding="utf-8"))
    toc = m["toc"]
    titles = m["chapterTitles"]
    print(f"=== {name} {bid}: chapterCount={m['chapterCount']} toc={len(toc)}")
    for i, t in enumerate(toc):
        tt = t.get("title") if isinstance(t, dict) else t
        typ = t.get("type") if isinstance(t, dict) else "?"
        idx = t.get("index") if isinstance(t, dict) else "?"
        mark = "" if tt in titles else "  <-- 不在 chapterTitles (残留?)"
        print(f"  [{i}] type={typ} index={idx} {tt!r}{mark}")
