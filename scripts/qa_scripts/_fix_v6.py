# -*- coding: utf-8 -*-
"""修复 v6 (2026-08-08): 8 本 part 缺 index 字段补齐 + 政治学卷标题 OCR 噪声规范化
用法: python _fix_v6.py [--write]
"""
import sys, os, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"f:\program\Python\PhiAgent\backend\tools")
import rebuild_auto as ra

WRITE = "--write" in sys.argv
CH = r"f:\program\Python\PhiAgent\backend\data\book_chapters"

# ══ 1. 8 本 part 补 index/level ══
BIDS = ["53b09f03e24e", "7657ef4a2cd3", "799e9e2654f5", "81218d6e1646",
        "a3e1832a509d", "c5013f33fe01", "f11f1b13c278", "f1e06cece874"]
for bid in BIDS:
    D = os.path.join(CH, bid)
    mf = os.path.join(D, "meta.json")
    meta = json.load(open(mf, encoding="utf-8"))
    toc = meta["toc"]
    if isinstance(toc, dict):
        toc = [v for k, v in sorted(toc.items(), key=lambda kv: int(kv[0]))]
    n = 0
    for i, t in enumerate(toc):
        if t.get("type") != "part":
            continue
        nxt = toc[i + 1]["index"] if i + 1 < len(toc) else len(toc) - 1
        if "index" not in t or t.get("level") != 0:
            t["index"] = nxt
            t["level"] = 0
            n += 1
    if n:
        meta["toc"] = toc
        print(f"{bid} {n} 个 part 补齐 index/level")
        if WRITE:
            json.dump(meta, open(mf, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            ra.sync_three(bid)

# ══ 2. 政治学: 卷标题 OCR 噪声规范化 ══
BID = "53b09f03e24e"
D = os.path.join(CH, BID)
mf = os.path.join(D, "meta.json")
meta = json.load(open(mf, encoding="utf-8"))
toc = meta["toc"]
MAP = {0: "第一卷", 1: "第二卷", 2: "第三卷", 3: "第四卷",
       4: "第五卷", 5: "第六卷", 6: "第七卷", 7: "第八卷"}
print(f"\n政治学 卷标题规范化")
for t in toc:
    idx = t.get("index")
    if idx in MAP and t["title"] != MAP[idx]:
        print(f"   [{t['type']}] {t['title']!r} → {MAP[idx]!r}")
        if WRITE:
            t["title"] = MAP[idx]
if WRITE:
    for idx, title in MAP.items():
        ch = json.load(open(os.path.join(D, f"{idx}.json"), encoding="utf-8"))
        if ch["title"] != title:
            ch["title"] = title
            json.dump(ch, open(os.path.join(D, f"{idx}.json"), "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)
    meta["toc"] = toc
    meta["chapterTitles"] = [t["title"] for t in toc if t.get("type") != "part"]
    json.dump(meta, open(mf, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    ra.sync_three(BID)
    print("政治学 sync_three 完成")
print("done")
