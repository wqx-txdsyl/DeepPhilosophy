# -*- coding: utf-8 -*-
"""段级零丢失验证: 旧 75 章每段(剥卷残留后)按序出现于新 5 章"""
import sys, os, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
NEW = r"f:/program/Python/PhiAgent/backend/data/book_chapters/e7c27b39a87c"
OLD = r"f:/program/Python/PhiAgent/backend/data/_rebuild_bak/e7c27b39a87c_old75ch"
STRIP = ["一、悲剧一、悲剧", "二、能动与反动", "三、批判三、批判", "四、从怨恨到内疚", "五、超人：反辩证法"]

old_segs = []
for i in range(75):
    c = json.load(open(f"{OLD}/{i}.json", encoding="utf-8"))
    for x in c["content"]:
        if x.get("type") == "text":
            v = x["value"]
            for p in STRIP:
                if v.startswith(p):
                    v = v[len(p):]
            old_segs.append(v)
new_segs = []
for i in range(5):
    c = json.load(open(f"{NEW}/{i}.json", encoding="utf-8"))
    new_segs += [x["value"] for x in c["content"] if x.get("type") == "text"]
print(f"旧段数 {len(old_segs)}  新段数 {len(new_segs)}  差值 {len(new_segs)-len(old_segs)} (应=插入节标题数)")

# 序列匹配: 旧段按序出现在新段列表
j = 0
missing = []
for v in old_segs:
    while j < len(new_segs) and new_segs[j] != v:
        j += 1
    if j >= len(new_segs):
        missing.append(v[:40])
        break
print("缺失段:", missing if missing else "无 ✓ 全部旧段按序存在")
# 插入段 = 新段中不在旧序列里的 → 应为节标题行
new_only = [v for v in new_segs if v not in old_segs]
import re
secs = [v for v in new_only if re.match(r"^\d{1,2}\. ", v)]
other = [v for v in new_only if not re.match(r"^\d{1,2}\. ", v)]
print(f"插入段 {len(new_only)} 个: 节标题式 {len(secs)} 个, 其他 {len(other)} 个")
for v in other[:10]:
    print("   ⚠", repr(v[:50]))
