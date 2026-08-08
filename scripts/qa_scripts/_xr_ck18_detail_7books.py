# -*- coding: utf-8 -*-
"""抽查18：7 本 detail/章节数不符修复
病因: 引擎切章后 meta.json 修正过（章节合并/重建），detail 与 books.json 的
  chapterCount/chapterTitles/toc 未同步 → 前端目录与实际章节文件不符。
7 本（detail.cc vs 实际章节文件数）:
  0d31135f957d 6→5（detail 旧版混入编委会页）   2cbf90eb6f69 25→17（cc 虚高）
  4be7b72cf01d 12→7（旧版每章含①注释版重复项） 60eed962806b 12→10（cc 虚高）
  88b56fb4da52 16→21（detail 旧版重建后未同步） 8a451d16f1b4 10→11（同上）
  b2fbc225f414 12→15（同上）
修复: 以 DP backend/data/book_chapters/{bid}/meta.json（章节文件系统=权威）为准，
  覆盖双端 detail 的 toc/chapterCount/chapterTitles + DP books.json 的 chapterCount。
用法: python _xr_ck18_detail_7books.py
"""
import json, os, shutil

BIDS = ["0d31135f957d", "2cbf90eb6f69", "4be7b72cf01d", "60eed962806b",
        "88b56fb4da52", "8a451d16f1b4", "b2fbc225f414"]
CHAP = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters"
DA = "f:/program/Python/PhiAgent/app/public/book_detail"
DB = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail"
BOOKS = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

for bid in BIDS:
    m = json.load(open(f"{CHAP}/{bid}/meta.json", encoding="utf-8"))
    nfiles = len([x for x in os.listdir(f"{CHAP}/{bid}")
                  if x.endswith(".json") and x != "meta.json"])
    toc = m["toc"]
    # 0d31135f957d 特判：3 个 part 节点对应真实正文文件（第一/二/三部分，28464/7905/8575 字）
    #   → 转 chapter（前端 part 只渲染分组标题不可点击，会把主体内容藏起来）
    if bid == "0d31135f957d":
        for t in toc:
            if t.get("type") == "part":
                t["type"] = "chapter"
                t.pop("level", None)
        m["toc"] = toc
        m["chapterCount"] = len([t for t in toc if t.get("type") == "chapter"])
        json.dump(m, open(f"{CHAP}/{bid}/meta.json", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=None)
        print("✓ 0d31135f957d meta.toc: 3 part → chapter（已写回 meta.json）")
    titles = [t["title"] for t in toc if t.get("type") == "chapter"]
    assert len(titles) == nfiles, (bid, len(titles), nfiles)
    # 备份旧 detail（原样留档）
    for p in (f"{DA}/{bid}.json", f"{DB}/{bid}.json"):
        shutil.copy2(p, p + ".ck18bak")
    for p in (f"{DA}/{bid}.json", f"{DB}/{bid}.json"):
        d = json.load(open(p, encoding="utf-8"))
        old = (d.get("chapterCount"), len(d.get("chapterTitles", [])))
        d["toc"] = toc
        d["chapterCount"] = len(titles)
        d["chapterTitles"] = titles
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
        print(f"✓ {bid} cc {old[0]}→{len(titles)} (titles {old[1]}→{len(titles)}) {p.split('/')[-2]}")

# meta 三处同步（0d31135f957d 的 meta.toc 已改）
if True:
    for p in (f"f:/program/Python/PhiAgent/backend/data/book_chapters/0d31135f957d/meta.json",
              f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters/0d31135f957d/meta.json"):
        shutil.copy2(f"{CHAP}/0d31135f957d/meta.json", p)
        print(f"✓ meta 同步: {p.split('/')[-2]}/{p.split('/')[-1]}")

# books.json 同步
books = json.load(open(BOOKS, encoding="utf-8"))
for x in books:
    if str(x.get("id")) in BIDS:
        bid = str(x["id"])
        m = json.load(open(f"{CHAP}/{bid}/meta.json", encoding="utf-8"))
        n = len([t for t in m["toc"] if t.get("type") == "chapter"])
        old = x["chapterCount"]
        x["chapterCount"] = n
        print(f"✓ books.json {bid} cc {old}→{n}（{x['title'][:14]}）")
json.dump(books, open(BOOKS, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
print("✓ books.json 写入完成")
