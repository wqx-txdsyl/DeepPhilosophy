# -*- coding: utf-8 -*-
"""验证尼采与哲学 5 章: 残留剥离/节标题写回/三端一致"""
import sys, os, json, hashlib
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
bd = r"f:/program/Python/PhiAgent/backend/data/book_chapters/e7c27b39a87c"
for i in range(5):
    c = json.load(open(f"{bd}/{i}.json", encoding="utf-8"))
    print(f"=== {i}.json {c['title']!r} {len(c['content'])}段")
    print("   首段:", repr(c["content"][0]["value"][:60]))
    print("   次段:", repr(c["content"][1]["value"][:50]))
# 节标题段统计（"数字. "开头独立段）
for i in range(5):
    c = json.load(open(f"{bd}/{i}.json", encoding="utf-8"))
    n = sum(1 for x in c["content"] if x["value"][:2].isdigit() and x["value"][2:3] == ".")
    print(f"  {c['title']}: 节标题独立段 {n} 个")
# 残留检查
bad = []
for i in range(5):
    c = json.load(open(f"{bd}/{i}.json", encoding="utf-8"))
    for x in c["content"]:
        for pat in ("一、悲剧一、悲剧", "二、能动与反动", "三、批判三、批判", "四、从怨恨到内疚", "五、超人：反辩证法"):
            if pat in x["value"]:
                bad.append((i, pat))
print("残留:", bad if bad else "无 ✓")
# 三端
import sys as _s
_s.path.insert(0, r"f:/program/Python/PhiAgent/backend/tools")
import rebuild_auto as ra
for tag, base in (("DP后端", ra.DP_BACKEND), ("DPpublic", ra.DP_PUBLIC + "/backend")):
    d = os.path.join(base, "data", "book_chapters", "e7c27b39a87c")
    dm = json.load(open(os.path.join(d, "meta.json"), encoding="utf-8"))
    same = dm["chapterTitles"] == [json.load(open(f"{bd}/{i}.json", encoding="utf-8"))["title"] for i in range(5)]
    same_md5 = all(
        json.dumps(json.load(open(f"{bd}/{i}.json", encoding="utf-8")), ensure_ascii=False)
        == json.dumps(json.load(open(f"{d}/{i}.json", encoding="utf-8")), ensure_ascii=False)
        for i in range(5)
    )
    print(f"{tag}: chapterCount={dm['chapterCount']} toc={len(dm['toc'])} titles一致={same} 内容md5一致={same_md5}")
