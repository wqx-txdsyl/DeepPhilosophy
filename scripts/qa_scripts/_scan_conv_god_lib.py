# -*- coding: utf-8 -*-
"""库: 与神对话 111 章现状 (标题+字数+首段)"""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BID = "7657ef4a2cd3"
D = r"f:\program\Python\PhiAgent\backend\data\book_chapters\7657ef4a2cd3"
m = json.load(open(os.path.join(D, "meta.json"), encoding="utf-8"))
print(f"chapterCount={m['chapterCount']}")
for i in range(m["chapterCount"]):
    fp = os.path.join(D, f"{i}.json")
    if not os.path.exists(fp):
        print(f"[{i}] 缺文件"); continue
    j = json.load(open(fp, encoding="utf-8"))
    texts = [b["value"] for b in j["content"] if b.get("type") == "text"]
    w = sum(len(t) for t in texts)
    first = texts[0][:24] if texts else "-"
    print(f"[{i}] {j.get('title','')[:36]:<38} 段={len(texts):<5} 字={w:<7} 首={first!r}")
