# -*- coding: utf-8 -*-
"""临时: 荣格心理学 各章文件 标题/字数/首尾"""
import json, sys, os

sys.stdout.reconfigure(encoding="utf-8")
BID = "d1a2be0b5837"
DIR = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"

meta = json.load(open(os.path.join(DIR, "meta.json"), encoding="utf-8"))
print("chapterCount:", meta.get("chapterCount"), "title:", meta.get("title"))
print("chapterTitles:", meta.get("chapterTitles"))

for i in range(meta.get("chapterCount", 0)):
    p = os.path.join(DIR, f"{i}.json")
    if not os.path.exists(p):
        print(f"{i}: 缺文件")
        continue
    ch = json.load(open(p, encoding="utf-8"))
    blocks = [b for b in ch.get("content", []) if b.get("type") == "text"]
    w = sum(len(b.get("value", "")) for b in blocks)
    head = blocks[0]["value"][:50].replace("\n", " ") if blocks else "(空)"
    tail = blocks[-1]["value"][-40:].replace("\n", " ") if blocks else ""
    print(f"\n[{i}] {ch.get('title')}  块{len(blocks)} {w}字")
    print(f"  首: {head}")
    print(f"  尾: {tail}")
