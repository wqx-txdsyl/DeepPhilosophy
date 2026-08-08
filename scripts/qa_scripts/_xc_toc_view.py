# -*- coding: utf-8 -*-
"""查看某书 toc 分级结构（part/chapter/section 缩进打印）
用法: python _xc_toc_view.py <bid> [--first N]
"""
import sys, os, json

sys.stdout.reconfigure(encoding="utf-8")

BID = sys.argv[1]
FIRST = int(sys.argv[sys.argv.index("--first") + 1]) if "--first" in sys.argv else 10000
OUT = os.path.join(r"f:/program/Python/PhiAgent/backend/data/book_chapters", BID)
m = json.load(open(os.path.join(OUT, "meta.json"), encoding="utf-8"))
print(f"chapterCount={m['chapterCount']} toc条数={len(m['toc'])}")
shown = 0
for t in m["toc"]:
    if not isinstance(t, dict):
        print(f"  [非dict] {t!r}")
        continue
    if t.get("type") == "part":
        print(f"  [part] {t['title']} (组首章索引 {t['index']})")
    elif t["type"] == "chapter":
        print(f"    章{t['index']:>3}: {t['title'][:44]}")
    elif t["type"] == "section":
        print(f"      · {t['title'][:44]}")
    shown += 1
    if shown >= FIRST:
        print(f"  …（共 {len(m['toc'])} 条, 显示 {FIRST} 条）")
        break
