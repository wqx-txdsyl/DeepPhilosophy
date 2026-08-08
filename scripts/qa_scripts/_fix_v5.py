# -*- coding: utf-8 -*-
"""修复 v5 (2026-08-08): 康德著作集 189 章 9 著作 part 分级 + #171 封面章改标题
用法: python _fix_v5.py [--write]
"""
import sys, os, json, shutil
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"f:\program\Python\PhiAgent\backend\tools")
import rebuild_auto as ra

WRITE = "--write" in sys.argv
BID = "309de54e4392"
CH = r"f:\program\Python\PhiAgent\backend\data\book_chapters"
D = os.path.join(CH, BID)
mf = os.path.join(D, "meta.json")
meta = json.load(open(mf, encoding="utf-8"))
toc = meta["toc"]
if isinstance(toc, dict):
    toc = [t for i, t in sorted(toc.items(), key=lambda kv: int(kv[0]))]
meta["toc"] = toc

# 9 著作边界: (part 标题, 起始章, 结束章含)
PARTS = [
    ("纯粹理性批判", 0, 24),
    ("实践理性批判", 25, 51),
    ("论优美感和崇高感", 52, 52),
    ("道德形而上学", 53, 78),
    ("判断力批判·审美判断力批判", 79, 101),
    ("判断力批判·目的论判断力批判", 102, 140),
    ("道德形而上学奠基", 141, 155),
    ("未来形而上学导论", 156, 170),
    ("逻辑学讲义", 171, 188),
]
assert len(toc) == 189 and toc[-1]["index"] == 188

# #171 封面章 → 前言
ch171 = json.load(open(os.path.join(D, "171.json"), encoding="utf-8"))
assert ch171["title"] == "封面", ch171["title"]
ch171["title"] = "前言"
if WRITE:
    json.dump(ch171, open(os.path.join(D, "171.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("#171 [封面] → [前言]")

new_toc = []
for pt, lo, hi in PARTS:
    new_toc.append({"type": "part", "title": pt, "index": lo, "level": 0})
    for t in toc:
        if lo <= t["index"] <= hi:
            new_toc.append({"type": "chapter", "title": t["title"], "index": t["index"], "level": 1})
print(f"新 toc: {len(new_toc)} 条 ({len(PARTS)} part + {len(new_toc)-len(PARTS)} chapter)")
meta["toc"] = new_toc
if WRITE:
    BAK = os.path.join(CH, "_rebuild_bak", f"{BID}_v6_parts")
    os.makedirs(BAK, exist_ok=True)
    if not os.listdir(BAK):
        for f in sorted(os.listdir(D)):
            shutil.copy2(os.path.join(D, f), os.path.join(BAK, f))
    json.dump(meta, open(mf, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("meta.json 写入完成")
    ra.sync_three(BID)
    print("sync_three 完成")
print("done")
