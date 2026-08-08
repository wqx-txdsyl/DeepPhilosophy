# -*- coding: utf-8 -*-
"""《开放社会及其敌人》（卡尔·波普尔）67d0b7e3c795 重建（一次性，旧数据重组）
epub: F:/philosophy/西方/卡尔·波普尔/开放社会及其敌人.epub（34 split，旧数据 30 文件一一对应）
旧数据 30 章全平级：0 目录页（垃圾）、2"正文"（实为原书"引言"）、3/14 卷首题词页当 chapter、
第一卷/第二卷应为 part。EPUB 源验证（spine 顺序）：
  004 导言：卡尔·波普尔与开放社会（独立章）
  005 引言（作者自序，独立章，旧名"正文"）
  006 第一卷 柏拉图的符咒（卷首题词 278 字）→ part
  007-016 第一章至第十章 → 第一卷 part 下（题词并入第一章开头）
  017 第十一章章题页（27 字纯标题，无正文，EPUB 分页遗留，不建章）
  018 第二卷 预言的高潮（卷首题词 7 字）→ part（题词并入第十一章开头）
  019-033 第十一章至第二十五章 → 第二卷 part 下
→ 27 章 + 2 part。cc 30 → 27。删 0 目录页；2"正文"改"引言"并剥内容首块标题行。
旧数据各章字数与 EPUB 一致（第一章 1911/第二章 5459 系 EPUB 源删节，非导入丢失）。
用法: python _xr_kfs_rebuild.py [--dry]
"""
import json, os, re, sys, shutil

BID = "67d0b7e3c795"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

def norm(s):
    return re.sub(r"\s+", "", s or "")

old = {}
for i in range(30):
    p = os.path.join(SRC, f"{i}.json")
    assert os.path.exists(p), f"缺旧文件 {p}"
    old[i] = json.load(open(p, encoding="utf-8"))

# ---- 结构表 ----
# (title, sources, part)  sources: 内容源文件（并入顺序）；part: 所属 part 标题或 None
STANDS = [  # 独立章（无 part）
    ("导言：卡尔·波普尔与开放社会", [1], None),
    ("引言", [2], None),          # 旧名"正文"，内容 = 原书引言（作者自序）
]
VOL1 = ("第一卷 柏拉图的符咒", [
    ("第一章 历史主义和命运的神话", [3, 4]),   # 3 = 卷首题词并入章首
    ("第二章 赫拉克利特", [5]),
    ("第三章 柏拉图的形式论或理念论", [6]),
    ("第四章 变化与静止", [7]),
    ("第五章 自然与约定", [8]),
    ("第六章 极权主义的正义", [9]),
    ("第七章 领导的原则", [10]),
    ("第八章 哲学王", [11]),
    ("第九章 唯美主义、完善主义、乌托邦主义", [12]),
    ("第十章 开放社会及其敌人", [13]),
])
VOL2 = ("第二卷 预言的高潮：黑格尔、马克思及余波", [
    ("第十一章 黑格尔主义的亚里士多德根源", [14, 15]),  # 14 = 卷首题词并入章首
    ("第十二章 黑格尔与新部落主义", [16]),
    ("第十三章 马克思的社会学决定论", [17]),
    ("第十四章 社会学的自主性", [18]),
    ("第十五章 经济的历史唯物主义", [19]),
    ("第十六章 阶级", [20]),
    ("第十七章 法律和社会体系", [21]),
    ("第十八章 社会主义的来临", [22]),
    ("第十九章 社会革命", [23]),
    ("第二十章 资本主义及其命运", [24]),
    ("第二十一章 对预言的评价", [25]),
    ("第二十二章 历史主义的道德理论", [26]),
    ("第二十三章 知识社会学", [27]),
    ("第二十四章 神谕哲学及对理性的反叛", [28]),
    ("第二十五章 历史有意义吗？", [29]),
])

# ---- 组装 ----
toc = []
files = {}
idx = 0
ALL_TITLE_NORMS = {norm(t) for t, srcs, pt in STANDS} \
    | {norm(t) for pt, chs in (VOL1, VOL2) for t, srcs in chs}

def push_ch(title, blocks):
    global idx
    # 剥内容中与 toc 标题精确重复的块（旧"正文"文件首块"引言"、无 h 标签 split 的章题行
    # "第四章 变化与静止"等；正文引用句不会整行精确等于章标题）
    blocks = [b for b in blocks
              if not (isinstance(b, dict) and "value" in b and norm(b["value"]) in ALL_TITLE_NORMS)]
    files[idx] = {"index": idx, "title": title, "content": blocks}
    toc.append({"type": "chapter", "title": title, "index": idx, "level": 1})
    idx += 1

for t, srcs, pt in STANDS:
    blocks = []
    for s in srcs:
        blocks.extend(old[s]["content"])
    push_ch(t, blocks)
for pt, chs in (VOL1, VOL2):
    toc.append({"type": "part", "title": pt, "index": idx, "level": 0})
    for t, srcs in chs:
        blocks = []
        for s in srcs:
            blocks.extend(old[s]["content"])
        push_ch(t, blocks)

# ---- 校验 ----
n_part = sum(1 for t in toc if t["type"] == "part")
assert n_part == 2, n_part
assert len(files) == 27, len(files)
total_chars = 0
for i in sorted(files):
    nc = sum(len(b.get("value", "")) for b in files[i]["content"])
    total_chars += nc
    print(f"  {i:2d} {files[i]['title'][:40]:42s} {nc:7d} 字")
print(f"总: {len(files)} 章 + {n_part} part, {total_chars} 字符（旧 30 章平级, cc 30→27）")
old_total = 0
for i in range(30):
    old_total += sum(len(b.get("value", "")) for b in old[i].get("content", []))
print(f"旧数据总字数: {old_total}（删 0 目录页 {sum(len(b.get('value','')) for b in old[0]['content'])} 字）")
for t in toc:
    ind = "  " * t.get("level", 1)
    print(f"{ind}[{t['type']}] {t['title'][:44]}")
print("首:", files[0]["title"], "| 末:", files[26]["title"])

if "--dry" in sys.argv:
    n_res = 0
    for i, ch in files.items():
        for b in ch["content"]:
            v = b.get("value", "")
            nv = norm(v)
            if nv in {"未知", "目录"} or (len(v) <= 24 and nv in ALL_TITLE_NORMS):
                print(f"⚠ 疑似残留 [{i} {ch['title'][:10]}]: {v[:34]}")
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
    "title": old_meta.get("title") or "开放社会及其敌人",
    "author": old_meta.get("author") or "卡尔·波普尔",
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
