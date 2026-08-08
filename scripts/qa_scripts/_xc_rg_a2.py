# -*- coding: utf-8 -*-
"""临时: 荣格 附录1/附录2/人名索引 块结构查看（A2 判断）"""
import json, sys

sys.stdout.reconfigure(encoding="utf-8")
DIR = r"f:/program/Python/PhiAgent/backend/data/book_chapters/d1a2be0b5837"
meta = json.load(open(f"{DIR}/meta.json", encoding="utf-8"))
for ci in (7, 10, 11):
    ch = json.load(open(f"{DIR}/{ci}.json", encoding="utf-8"))
    blocks = [b for b in ch["content"] if b.get("type") == "text"]
    print(f"\n== [{ci}] {ch['title']} 块{len(blocks)} ==")
    for i, b in enumerate(blocks):
        v = b["value"]
        print(f"--- 块{i} ({len(v)}字): {v[:80]!r}")
        if len(v) > 80:
            print(f"      尾… {v[-60:]!r}")
