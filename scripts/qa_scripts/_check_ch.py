# -*- coding: utf-8 -*-
import json, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
bd = r"f:/program/Python/PhiAgent/backend/data/book_chapters/e7c27b39a87c"
for i in (0, 1, 16, 62):
    c = json.load(open(f"{bd}/{i}.json", encoding="utf-8"))
    print(f"=== {i}.json title={c['title']!r} content段数={len(c['content'])}")
    for x in c["content"][:3]:
        print(f"   {x['type']}: {x['value'][:80]!r}")
    v = c["content"][0]["value"]
    print("   中段采样:", repr(v[900:960]) if len(v) > 960 else "短")
