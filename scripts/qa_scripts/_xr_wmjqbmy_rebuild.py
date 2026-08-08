# -*- coding: utf-8 -*-
"""#128 文明及其不满（弗洛伊德，浙江文艺 2019 三书合集）472af5b267ba 重建（一次性，旧数据重组）
病因（CHKLIST ✗B 多书合并，书级标题缺失）:
  旧数据 25 文件平铺 = 三本中译本合订：文明及其不满（0 扉页CIP + 1 译序 + 2 编者导言 +
  3-10 第一~八章）+ 一种幻想的未来（11 编者导言 + 12-21 第一~十章）+ 缘何而战？（22 编者导言 +
  23 书信正文）+ 24 附录 专业术语表。书间过渡页（英文名+中文名两块）粘在上一本末章尾。
重建:
  [part l0] 文明及其不满 / 一种幻想的未来 / 缘何而战？ ×3（书级分组）
  [ch] 24 章（删 0 扉页 CIP 纯元数据；10 尾剥离"The Future of an Illusion/一种幻想的未来"
      过渡块；21 尾剥离"Why War ?/缘何而战？"过渡块；1 尾英文书名页保留）
  cc 25 → 24 + 3 part。
用法: python _xr_wmjqbmy_rebuild.py [--dry]
"""
import json, os, sys, shutil

BID = "472af5b267ba"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

def norm(s):
    return re.sub(r"\s+", "", s or "")

import re

old = {}
for fn in os.listdir(SRC):
    if not fn.endswith(".json") or fn == "meta.json":
        continue
    ch = json.load(open(os.path.join(SRC, fn), encoding="utf-8"))
    old[int(fn[:-5])] = ch
assert len(old) == 25, len(old)

# 剥离过渡页（10 第八章尾 / 21 第十章尾各 2 块: 英文名 + 中文名）
def strip_tail(fn, n=2):
    for _ in range(n):
        old[fn]["content"].pop()

strip_tail(10, 2)   # The Future of an Illusion / 一种幻想的未来
strip_tail(21, 2)   # Why War ? / 缘何而战？

# ---- 结构表 ----
VOLS = [
    ("文明及其不满", [
        ("译序", [1]),
        ("英文版编者导言", [2]),
        ("第一章", [3]), ("第二章", [4]), ("第三章", [5]), ("第四章", [6]),
        ("第五章", [7]), ("第六章", [8]), ("第七章", [9]), ("第八章", [10]),
    ]),
    ("一种幻想的未来", [
        ("英文版编者导言", [11]),
        ("第一章", [12]), ("第二章", [13]), ("第三章", [14]), ("第四章", [15]),
        ("第五章", [16]), ("第六章", [17]), ("第七章", [18]), ("第八章", [19]),
        ("第九章", [20]), ("第十章", [21]),
    ]),
    ("缘何而战？", [
        ("英文版编者导言", [22]),
        ("缘何而战？（弗洛伊德致爱因斯坦）", [23]),
    ]),
]
STANDS = [("附录 专业术语表", [24])]   # 合集级附录（无 part）

# ---- 组装 ----
toc = []
files = {}
idx = 0

def push_ch(title, srcs):
    global idx
    blocks = []
    for s in srcs:
        blocks.extend(old[s]["content"])
    files[idx] = {"index": idx, "title": title, "content": blocks}
    toc.append({"type": "chapter", "title": title, "index": idx, "level": 1})
    idx += 1

for pt, chs in VOLS:
    toc.append({"type": "part", "title": pt, "index": idx, "level": 0})
    for t, srcs in chs:
        push_ch(t, srcs)
for t, srcs in STANDS:
    push_ch(t, srcs)

# ---- 校验 ----
n_part = sum(1 for t in toc if t["type"] == "part")
assert n_part == 3, n_part
assert len(files) == 24, len(files)
used = [s for _, chs in VOLS for _, srcs in chs for s in srcs] + [24]
assert len(used) == len(set(used)), "源文件重复使用"
for i in sorted(files):
    assert i == files[i]["index"], "index 连续"

total_chars = 0
for i in sorted(files):
    nc = sum(len(b.get("value", "")) for b in files[i]["content"])
    total_chars += nc
    print(f"  {i:2d} {files[i]['title'][:44]:46s} {nc:7d} 字")
print(f"总: {len(files)} 章 + {n_part} part, {total_chars} 字符（旧 25 章平级, cc 25→24）")
old_total = sum(sum(len(b.get("value", "")) for b in old[i]["content"]) for i in old)
print(f"旧数据总字数: {old_total}（删 0 扉页 {sum(len(b.get('value','')) for b in old[0]['content'])} 字 + 剥离过渡页 2×2 块）")
for t in toc:
    ind = "  " * t.get("level", 1)
    print(f"{ind}[{t['type']}] {t['title'][:44]}")
print("首:", files[0]["title"], "| 末:", files[23]["title"])

if "--dry" in sys.argv:
    title_norms = {norm(t["title"]) for t in toc}
    n_res = 0
    for i, ch in files.items():
        for k, b in enumerate(ch["content"]):
            if "value" not in b or not b["value"]:
                continue
            nv = norm(b["value"])
            prev = ch["content"][k - 1] if k > 0 else {}
            if len(nv) <= 10 and nv in title_norms and prev.get("type") != "image":
                print(f"⚠ 疑似章题残留 [{i} {ch['title'][:12]}]: {b['value'][:34]!r}")
                n_res += 1
    print(f"残留: {n_res}")
    sys.exit(0)

# ---- 写入 ----
if os.path.isdir(SRC):
    suf = "_old_bad"
    i2 = 2
    while os.path.isdir(SRC + suf):
        suf = f"_old_bad{i2}"
        i2 += 1
    os.rename(SRC, SRC + suf)
    print(f"备份旧数据 → {os.path.basename(SRC) + suf}")
os.makedirs(SRC)
old_meta = {}
old_bid = SRC + "_old_bad"
if os.path.isdir(old_bid) and os.path.exists(os.path.join(old_bid, "meta.json")):
    old_meta = json.load(open(os.path.join(old_bid, "meta.json"), encoding="utf-8"))
for i, ch in files.items():
    json.dump(ch, open(os.path.join(SRC, f"{i}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
meta = {
    "bookId": old_meta.get("bookId") or BID,
    "title": old_meta.get("title") or "文明及其不满",
    "author": old_meta.get("author") or "西格蒙德·弗洛伊德",
    "toc": toc,
    "cover": old_meta.get("cover"),
    "chapterCount": len(files),
    "chapterTitles": [ch["title"] for ch in files.values()],
}
json.dump(meta, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print(f"✓ 写入 {SRC}: {len(files)} 章 + meta.json")

shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
print("✓ 同步 DP chapters")

for p in (DETAIL_SRC, DETAIL_DST):
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))
        d["toc"] = toc
        d["chapterCount"] = len(files)
        d["chapterTitles"] = [ch["title"] for ch in files.values()]
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
        print(f"✓ book_detail 更新: {p}")

if os.path.exists(BOOKS_JSON):
    bj = json.load(open(BOOKS_JSON, encoding="utf-8"))
    bl = bj if isinstance(bj, list) else bj.get("books", [])
    hit = False
    for b in bl:
        if b.get("id") == BID:
            b["chapterCount"] = len(files)
            hit = True
    if hit:
        with open(BOOKS_JSON, "w", encoding="utf-8") as f:
            json.dump(bl if isinstance(bj, list) else {**bj, "books": bl}, f, ensure_ascii=False, indent=None)
        print("✓ books.json chapterCount 更新")
    else:
        print("⚠ books.json 未找到该书")
