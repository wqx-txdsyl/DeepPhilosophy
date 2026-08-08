# -*- coding: utf-8 -*-
"""检查某书指定章节结构与内容: python _inspect_ch.py <bid> <n>"""
import sys, os, json

BID, N = sys.argv[1], sys.argv[2]
D = os.path.join(r"f:\program\Python\PhiAgent\backend\data\book_chapters", BID)
fp = os.path.join(D, f"{N}.json")
ch = json.load(open(fp, encoding="utf-8"))
print(f"== {N}.json title: {ch['title']!r}")
print(f"   content type: {type(ch['content'])} 段数: {len(ch['content'])}")
total = 0
for i, x in enumerate(ch["content"]):
    if isinstance(x, dict):
        v = x.get("value", "")
        total += len(v)
        print(f"   [{i}] {type(v).__name__} 字{len(v)}: {repr(v[:200])}")
    else:
        print(f"   [{i}] {type(x).__name__}: {repr(x)[:200]}")

m = json.load(open(os.path.join(D, "meta.json"), encoding="utf-8"))
toc = m["toc"]
print(f"\n== meta toc type: {type(toc).__name__}")
if isinstance(toc, dict):
    print("   keys:", list(toc)[:8], "...")
    items = list(toc.items())
    print("   后4条:", [(k, v.get("title") if isinstance(v, dict) else v) for k, v in items[-4:]])
else:
    print("   后4条:", [(t.get("title") if isinstance(t, dict) else t) for t in toc[-4:]])
print(f"== chapterCount: {m.get('chapterCount')}")
