# -*- coding: utf-8 -*-
"""
dp_merge_summaries.py — 将历史 book_summaries.json（title||author → summary）合并进 detail
- 只补无 summary（或 <50 字）的 detail
- 匹配: (title, author) 精确 → title 兜底
- 输出匹配统计
"""
import sys, io, os, json

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/
DDIR = os.path.join(BASE, "data", "book_detail")
SUMM = os.path.join(BASE, "data", "book_summaries.json")

summaries = json.load(open(SUMM, encoding="utf-8"))
by_key, by_title = {}, {}
for k, v in summaries.items():
    if "||" in k:
        t, a = k.split("||", 1)
        by_key[(t, a)] = v
        by_title.setdefault(t, v)
    else:
        by_title.setdefault(k, v)
print(f"book_summaries: {len(summaries)} entries", flush=True)

merged = 0
skip_done = 0
for fn in sorted(os.listdir(DDIR)):
    dp = os.path.join(DDIR, fn)
    x = json.load(open(dp, encoding="utf-8"))
    if x.get("summary") and len(x.get("summary", "")) >= 50:
        skip_done += 1
        continue
    t, a = x.get("title", ""), x.get("author", "")
    info = by_key.get((t, a)) or by_title.get(t)
    if info and isinstance(info, dict) and info.get("summary"):
        x["summary"] = info["summary"]
        if info.get("tags") and not x.get("tags"):
            x["tags"] = info["tags"]
        json.dump(x, open(dp, "w", encoding="utf-8"), ensure_ascii=False)
        merged += 1
        print(f"  + {t}", flush=True)
print(f"already done: {skip_done}, merged: {merged}", flush=True)
