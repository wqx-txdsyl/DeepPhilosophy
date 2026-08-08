# -*- coding: utf-8 -*-
"""查 75 章内容: 卷标题残留形态 + 各卷首节首段"""
import json, sys, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
bd = r"f:/program/Python/PhiAgent/backend/data/book_chapters/e7c27b39a87c"
titles = ["一、悲剧", "二、能动与反动", "三、批判", "四、从怨恨到内疚", "五、超人：反辩证法"]
vol_first = [0, 16, 31, 46, 62]
for i in vol_first:
    c = json.load(open(f"{bd}/{i}.json", encoding="utf-8"))
    v = c["content"][0]["value"]
    print(f"=== {i}.json {c['title']!r} 首段前60字:")
    print("   ", repr(v[:60]))
# 全文搜残留
cnt = {t: 0 for t in titles}
for i in range(75):
    c = json.load(open(f"{bd}/{i}.json", encoding="utf-8"))
    for x in c["content"]:
        for t in titles:
            if t in x["value"]:
                cnt[t] += 1
print("\n卷标题在 75 章正文出现次数:", cnt)
# 节标题行形态: 各节首段是否以"数字."开头
bad = 0
for i in range(75):
    c = json.load(open(f"{bd}/{i}.json", encoding="utf-8"))
    v = c["content"][0]["value"]
    if not re.match(r"^\d{1,2}\.", v):
        bad += 1
        print(f"  首段非数字节标题开头: {i}.json {v[:30]!r}")
print("首段非'数字.'开头章数:", bad)
