# -*- coding: utf-8 -*-
"""存在与时间/与神对话 详情 + 找所有"存在与时间"相关书"""
import sys, os, re, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
DD = r"f:\program\Python\PhiAgent\backend\data\book_detail"
CH = r"f:\program\Python\PhiAgent\backend\data\book_chapters"

print("== 所有含'存在与时间'/'与神对话'/'存在与虚无'的书 ==")
for f in sorted(os.listdir(DD)):
    if not f.endswith(".json"): continue
    j = json.load(open(os.path.join(DD, f), encoding="utf-8"))
    t = j.get("title", "")
    if any(k in t for k in ("存在与时间", "与神对话", "存在与虚无")):
        print(f"  {t} | {f[:-5]} | {j.get('file_type')}")

for bid, name in [("c5013f33fe01", "存在与时间"), ("7657ef4a2cd3", "与神对话(全5卷)")]:
    meta = json.load(open(os.path.join(CH, bid, "meta.json"), encoding="utf-8"))
    print(f"\n== {name} ({bid}) chapterCount={meta.get('chapterCount')}")
    # 各章字数
    for i in range(meta.get("chapterCount", 0)):
        jp = os.path.join(CH, bid, f"{i}.json")
        if not os.path.exists(jp): continue
        j = json.load(open(jp, encoding="utf-8"))
        texts = [b["value"] for b in j.get("content", []) if b.get("type") == "text"]
        total = sum(len(t) for t in texts)
        if i < 3 or i >= meta["chapterCount"] - 1:
            print(f"  [{i}] {j.get('title')}: {total} 字 首={texts[1][:40] if len(texts)>1 else ''!r} 尾={texts[-1][:40]!r}")
        else:
            print(f"  [{i}] {j.get('title')}: {total} 字")
