# -*- coding: utf-8 -*-
"""查《论人类不平等的起源和基础》: 各章首/尾段完整性 + 跨章散落"""
import sys, os, json, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
bd = r"f:/program/Python/PhiAgent/backend/data/book_chapters/9e4f98733f0b"
m = json.load(open(bd + "/meta.json", encoding="utf-8"))
print("章节数:", m["chapterCount"])
for i in range(m["chapterCount"]):
    c = json.load(open(f"{bd}/{i}.json", encoding="utf-8"))
    texts = [x["value"] for x in c["content"] if x.get("type") == "text"]
    w = sum(len(t) for t in texts)
    first = texts[0][:45] if texts else "!"
    last = texts[-1][-60:] if texts else "!"
    end_ok = texts[-1].rstrip().endswith(("。", "！", "？", "”", "）", "…", ".")) if texts else False
    start_ok = not texts[0].startswith(("，", "。", "、", "；", "）", "”")) if texts else False
    print(f"[{i}] {c['title']!r} {w}字 首:{first!r}")
    print(f"     尾:{last!r} 尾段完整={end_ok} 首段正常={start_ok}")
