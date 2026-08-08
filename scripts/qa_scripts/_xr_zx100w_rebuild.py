# -*- coding: utf-8 -*-
"""《哲学100问（套装共3册）》（书杰）a325bbdc496e 重建（一次性，ncx 驱动 + 旧数据复用）
epub: F:/philosophy/东方/书杰/哲学100问（套装共3册）.epub
旧数据 296 章全平级（应为 篇章→(一、二、三/导言)→条目 三级）。
真实结构（toc.ncx 树，332 条目）:
  [skip] 套装名/3 册名/书名页×3/版权页×3/目录×3（无正文价值）
  [ch]   自序×3 / 参考书目×3 / 后记×3（无 part）
  [part] 16 篇章（第X篇章 YYY）
    [ch] 册1（从古希腊到黑格尔）: 导言×2 + 一、二、三×13
    [sec] 册1 条目 109 + 小结 6（原为独立文件，并入归属 chapter）
    [ch] 册2（人，诗意地栖居）+ 册3（后现代的刺）: 条目+小结 164（无更低级标题）
→ 188 章 + 16 part + 115 section。文件内容逐 block 原样保留。
用法: python _xr_zx100w_rebuild.py [--dry]
"""
import json, os, re, sys, shutil

BID = "a325bbdc496e"
NCX = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/scripts/qa_scripts/_tmp_zx100w_ncx.json"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

def norm(s):
    return re.sub(r"\s+", "", s or "")

seq = json.load(open(NCX, encoding="utf-8"))
assert len(seq) == 332
SKIP = {"书名页", "版权页", "目录"}

# ---- 旧数据映射（按 册名+标题；"参考书目/后记"三册同名）----
# 旧数据文件无册信息，用 ncx 顺序回填：遍历旧 toc（即 ncx 序）与 ncx 条目对齐
d_old = json.load(open(f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json", encoding="utf-8"))
old_order = [t["title"] for t in d_old["toc"]]
# ncx 非组织条目（有独立文件的）按序 = 旧 toc 序（含版权页/目录——旧数据有这些文件）
file_titles = []  # (book, title) 按 ncx 序
cur_book = None
for depth, title in seq:
    if depth == 0:
        continue
    if depth == 1:
        cur_book = title
        continue
    if depth == 2 and "篇章" in title:
        continue
    if depth == 2 and title == "书名页":
        continue  # 旧数据无书名页文件
    if depth == 3 and re.match(r"^[一二三四五]+、", title) and cur_book == "哲学100问：从古希腊到黑格尔":
        continue  # 组织层"一、二、三"（无独立文件）
    if depth in (2, 3, 4):
        file_titles.append((cur_book, title))
assert len(file_titles) == len(old_order), (len(file_titles), len(old_order))
old_by_key = {}
for (b, t), ot in zip(file_titles, old_order):
    assert norm(t) == norm(ot), (t, ot)
    fn = os.path.join(SRC, f"{old_order.index(ot)}.json")
old_map = {}
for fn in os.listdir(SRC):
    if not fn.endswith(".json") or fn == "meta.json":
        continue
    ch = json.load(open(os.path.join(SRC, fn), encoding="utf-8"))
    old_map.setdefault(norm(ch["title"]), []).append(ch)
# 用 ncx 序建立 (book, title) → 文件（同名时按顺序取）
old_by_key = {}
for (b, t) in file_titles:
    lst = old_map.get(norm(t))
    assert lst, f"旧文件缺失: {b} / {t}"
    old_by_key[(b, t)] = lst.pop(0)

# ---- ncx 结构树 ----
tree = []      # part 节点 {"title","chapters":[...]} 或 chapter 节点 {"title","sections":[...]}
cur_book = None
cur_part = None
cur_ch = None
miss = []
for depth, title in seq:
    if depth == 0:            # 套装名
        continue
    if depth == 1:            # 册名
        cur_book = title
        continue
    if depth == 2:
        if "篇章" in title:
            cur_part = {"title": title, "chapters": [], "book": cur_book}
            tree.append(cur_part)
        elif title in SKIP:
            continue
        else:                 # 自序/参考书目/后记
            cur_part = None
            cur_ch = {"title": title, "sections": [], "book": cur_book}
            tree.append(cur_ch)
        continue
    if depth == 3:            # 导言/一二三（册1）或 条目/小结（册2/3）
        cur_ch = {"title": title, "sections": [], "book": cur_book}
        cur_part["chapters"].append(cur_ch)
        continue
    if depth == 4:            # 册1 条目/小结
        cur_ch["sections"].append({"title": title, "book": cur_book})

# ---- 组装 chapter 内容 ----
ALL_TITLE_NORMS = None  # 组装后填入（toc 标题集合）

def trim_trailing(blocks):
    """剥除文件尾部粘入的下一章标题行（旧数据条目文件末尾残留，如"二、古希腊三贤"）。"""
    i = len(blocks) - 1
    while i >= 0:
        b = blocks[i]
        if "value" not in b:
            i -= 1
            continue
        if norm(b["value"]) in ALL_TITLE_NORMS:
            del blocks[i]
            i -= 1
            continue
        break
    return blocks

def fetch(nodes):
    """nodes: chapter dict 列表；返回内容块列表（自身文件 + sections 拼入）。
    组织层 chapter（一、二、三）无自身文件，仅拼 sections。"""
    out = []
    for n in nodes:
        self_ch = old_by_key.get((n["book"], n["title"]))
        if self_ch:
            for b in self_ch["content"]:
                out.append(b)
        for s in n.get("sections", []):
            ch = old_by_key.get((s["book"], s["title"]))
            assert ch, f"section 文件缺失: {s['book']} / {s['title']}"
            for b in ch["content"]:
                out.append(b)
    return out

toc = []
files = {}
idx = 0
for node in tree:
    if "chapters" in node:  # part
        parts = node["chapters"]
        for ci, c in enumerate(parts):
            if ci == 0:
                toc.append({"type": "part", "title": node["title"], "index": idx, "level": 0})
            files[idx] = {"index": idx, "title": c["title"], "content": fetch([c])}
            toc.append({"type": "chapter", "title": c["title"], "index": idx, "level": 1})
            for si, s in enumerate(c.get("sections", []), 1):
                toc.append({"type": "section", "title": s["title"], "index": idx, "sec": si, "level": 2})
            idx += 1
    else:  # 独立 chapter（自序/参考书目/后记）
        files[idx] = {"index": idx, "title": node["title"], "content": fetch([node])}
        toc.append({"type": "chapter", "title": node["title"], "index": idx, "level": 1})
        idx += 1

# 剥除文件尾部粘入的下一章标题行
ALL_TITLE_NORMS = {norm(t["title"]) for t in toc}
for ch in files.values():
    trim_trailing(ch["content"])

# ---- 校验 ----
assert not miss, f"缺失条目: {miss}"
assert idx == 188, f"章数 {idx} ≠ 188"
n_part = sum(1 for t in toc if t["type"] == "part")
n_sec = sum(1 for t in toc if t["type"] == "section")
assert n_part == 16 and n_sec == 115, (n_part, n_sec)
# section 序列校验：每章首个 section 前项必须是同 index 的 chapter
for i, t in enumerate(toc):
    if t["type"] == "section" and (i == 0 or toc[i - 1]["type"] != "section" or toc[i - 1]["index"] != t["index"]):
        assert toc[i - 1]["type"] == "chapter" and toc[i - 1]["index"] == t["index"], f"section 错位: {t}"

total_chars = 0
for i in sorted(files):
    nc = sum(len(b.get("value", "")) for b in files[i]["content"])
    total_chars += nc
    print(f"  {i:3d} {files[i]['title'][:44]:46s} {nc:7d} 字")
print(f"总: {len(files)} 章 + {n_part} part + {n_sec} section, {total_chars} 字符（旧 296 章平级）")

old_total = 0
for fn in os.listdir(SRC):
    if fn.endswith(".json") and fn != "meta.json":
        ch = json.load(open(os.path.join(SRC, fn), encoding="utf-8"))
        old_total += sum(len(b.get("value", "")) for b in ch.get("content", []))
print(f"旧数据总字数: {old_total}")

# toc 打印（按层级缩进）
for t in toc:
    ind = "  " * t.get("level", 1)
    print(f"{ind}[{t['type']} {t.get('sec','')}] {t['title'][:44]}")
print("首:", files[0]["title"], "| 末:", files[len(files) - 1]["title"])

if "--dry" in sys.argv:
    n_res = 0
    for i, ch in files.items():
        title_norms = {norm(t["title"]) for t in toc}
        for b in ch["content"]:
            if "value" not in b:
                continue
            v = b["value"]
            nv = norm(v)
            if nv in {"未知", "目录"} or (len(v) <= 60 and nv in title_norms):
                print(f"⚠ 疑似残留 [{i} {ch['title'][:10]}]: {v[:36]}")
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
    "title": old_meta.get("title") or "哲学100问（套装共3册）",
    "author": old_meta.get("author") or "书杰",
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
