# -*- coding: utf-8 -*-
"""全库标题行清理 dry-run: 输出每本 '首段==章标题' 与 '尾段==toc标题' 的明细
用法: python _bulk_clean_dry.py [--head-only] [--tail-only]
"""
import sys, os, re, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CH = r"f:\program\Python\PhiAgent\backend\data\book_chapters"
BOOKS = json.load(open(r"f:\program\Python\PhiAgent\app\public\books.json", encoding="utf-8"))
names = {b["id"]: b["title"] for b in BOOKS}

def norm(s):
    return re.sub(r"\s+", "", s or "")

DO_HEAD = "--tail-only" not in sys.argv
DO_TAIL = "--head-only" not in sys.argv
ndir = sorted(d for d in os.listdir(CH) if os.path.isdir(os.path.join(CH, d)) and not d.startswith("_"))
n_head_b, n_tail_b = 0, 0
for bid in ndir:
    D = os.path.join(CH, bid)
    mf = os.path.join(D, "meta.json")
    if not os.path.exists(mf):
        continue
    meta = json.load(open(mf, encoding="utf-8"))
    toc = meta["toc"]
    if isinstance(toc, dict):
        toc = [t for i, t in sorted(toc.items(), key=lambda kv: int(kv[0]))]
    if not toc or not isinstance(toc[0], dict):
        continue  # 存在与虚无等 OCR 重建中
    all_titles = {norm(t["title"]): t["title"] for t in toc if t.get("type") == "chapter"}
    heads, tails = [], []
    for t in toc:
        if t.get("type") != "chapter":
            continue
        fp = os.path.join(D, f"{t['index']}.json")
        if not os.path.exists(fp):
            continue
        ch = json.load(open(fp, encoding="utf-8"))
        vals = [x["value"] for x in ch["content"] if isinstance(x, dict) and x.get("type") == "text"]
        if len(vals) < 2:
            continue
        nt = norm(ch["title"])
        f0, l0 = norm(vals[0]), norm(vals[-1])
        if DO_HEAD and f0 == nt:
            heads.append(t["index"])
        if DO_TAIL and l0 and l0 in all_titles and l0 != nt:
            tails.append((t["index"], vals[-1][:34]))
    name = names.get(bid, bid)
    if heads:
        n_head_b += 1
        print(f"H {name[:20]:20s} {bid[:8]} :: {len(heads)}章 {heads[:12]}")
    if tails:
        n_tail_b += 1
        print(f"T {name[:20]:20s} {bid[:8]} :: {len(tails)}章")
        for idx, txt in tails[:4]:
            print(f"      #{idx} 尾段 {txt!r}")
print(f"\n== 首重复 {n_head_b} 本 / 尾污染 {n_tail_b} 本 ==")
