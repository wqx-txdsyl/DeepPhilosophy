# -*- coding: utf-8 -*-
"""抽查19/20：工具论加分篇 part + 地下室手记去分级
工具论（b471f41a78de）：16 章平铺（序/范畴篇/解释篇/前分析篇1-2卷/后分析篇1-2卷/论题篇1-8卷/辩谬篇）
  → 7 part（序/范畴篇/解释篇/前分析篇/后分析篇/论题篇/辩谬篇）+ 16 chapter 不变
地下室手记（799e9e2654f5）：3 章 + 2 part（地下室/雨雪霏霏）分级多余 → 纯 3 chapter
同步: 章节 meta 三处 + detail 双端 + books.json（cc 不变）
用法: python _xr_ck19_20_fenji.py
"""
import json, os, shutil

def load(p): return json.load(open(p, encoding="utf-8"))
def save(p, d): json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)

CHAP = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters"
SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters"
DST2 = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters"
DA = "f:/program/Python/PhiAgent/app/public/book_detail"
DB = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail"
BOOKS = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

def sync_meta(bid):
    """meta 三处同步 + detail 双端 + books.json"""
    m = load(f"{CHAP}/{bid}/meta.json")
    n = len([t for t in m["toc"] if t.get("type") == "chapter"])
    assert n == m["chapterCount"] == len(m.get("chapterTitles", []))
    for p in (f"{SRC}/{bid}/meta.json", f"{DST2}/{bid}/meta.json"):
        save(p, m)
    for p in (f"{DA}/{bid}.json", f"{DB}/{bid}.json"):
        d = load(p)
        d["toc"] = m["toc"]
        d["chapterCount"] = n
        d["chapterTitles"] = m["chapterTitles"]
        save(p, d)
    books = load(BOOKS)
    for x in books:
        if str(x.get("id")) == bid:
            x["chapterCount"] = n
    save(BOOKS, books)
    print(f"✓ {bid} 同步: meta×3 + detail×2 + books.json (cc={n})")

# ---- 工具论：7 part + 16 chapter ----
bid = "b471f41a78de"
m = load(f"{CHAP}/{bid}/meta.json")
titles = [t["title"] for t in m["toc"] if t.get("type") == "chapter"]
assert titles == ["序", "范畴篇", "解释篇",
                  "前分析篇第一卷", "前分析篇第二卷",
                  "后分析篇第一卷", "后分析篇第二卷",
                  "论题篇第一卷", "论题篇第二卷", "论题篇第三卷", "论题篇第四卷",
                  "论题篇第五卷", "论题篇第六卷", "论题篇第七卷", "论题篇第八卷",
                  "辩谬篇"], titles
# part 名 → 挂哪些 chapter
PARTS = [("序", [0]),
         ("范畴篇", [1]),
         ("解释篇", [2]),
         ("前分析篇", [3, 4]),
         ("后分析篇", [5, 6]),
         ("论题篇", [7, 8, 9, 10, 11, 12, 13, 14]),
         ("辩谬篇", [15])]
toc = []
pi = 0
for pname, chs in PARTS:
    toc.append({"type": "part", "title": pname, "index": pi, "level": 0})
    pi += 1
    for ci in chs:
        toc.append({"type": "chapter", "title": titles[ci], "index": ci})
m["toc"] = toc
save(f"{CHAP}/{bid}/meta.json", m)
print(f"✓ 工具论 toc: 16 chapter → 7 part + 16 chapter")
sync_meta(bid)

# ---- 地下室手记：去 part 纯 3 chapter ----
bid = "799e9e2654f5"
m = load(f"{CHAP}/{bid}/meta.json")
titles = [t["title"] for t in m["toc"] if t.get("type") == "chapter"]
assert titles == ["版本信息与译本前言", "地下室", "雨雪霏霏"], titles
m["toc"] = [{"type": "chapter", "title": t, "index": i} for i, t in enumerate(titles)]
m["chapterTitles"] = titles
m["chapterCount"] = len(titles)
save(f"{CHAP}/{bid}/meta.json", m)
print(f"✓ 地下室手记 toc: 去 2 part → 纯 3 chapter")
sync_meta(bid)
