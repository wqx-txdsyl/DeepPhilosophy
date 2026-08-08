# -*- coding: utf-8 -*-
"""《哲学科学全书纲要》（黑格尔，贺麟译本）497b0228c3a6 重建（一次性，旧数据重排）
旧数据 89 章全平级（0-88），实为三版合订，各版内部 部门→部分→字母节 三级：
  0-15 = 1817 初版（§1-471）：0 扉页(删) / 1【前言】/ 2 导论 §1-11 / 3 引论 §12-37
           / 4-14 逻辑学(存在论§38-62/本质论§63-107/概念论§108-192) 自然哲学(§193-299)
             精神哲学(§300-471) / 15 译后记
  16-50 = 1827 版（§1-574）：16 第二版前言 / 17 第一版前言 / 18 导论 §1-25
           / 19-22 更切近概念与划分(A/B/C 态度) / 23-31 逻辑学 / 32-41 自然哲学
           / 42-49 精神哲学(49 绝对精神整章含 a.艺术./b.受启宗教./c.哲学.) / 50 译后记
  51-88 = 1830 版（§1-577）：51-53 三版前言 / 54 导论 / 55-67 逻辑学(85-87 分章 A艺术/B宗教/C哲学)
           / 68-77 自然哲学 / 78-87 精神哲学 / 88 译后记
部门标题（逻辑学等）在 EPUB 中丢失（1817 版只有 7"B. 自然哲学."/11"C. 精神哲学." 残留，
该两章实为部门导论 §193-197/§300-306）；1827/1830 版"第一部分 存在论"等部分标题亦丢失
（23 直接是 A. 质.）。重建：
  [part] 9 = 部门×版本（逻辑学（1817年版）等）
  [ch]  48 = 独立章 11（前言/导论/引论/译后记×3 组）+ 部门内 37
        组织层部分（1827/1830 存在论等）标题从 1817 版对应章继承，内容 = 其下字母节拼接
  [sec] 81 = 字母节（1817 从章内字母行切 toc 锚点；1827/1830 从独立章降级；49 章内 a/b/c 锚点）
  section 无独立文件（toc 锚点，index=所属 chapter，哲学100问模式）
文件内容逐 block 原样保留。89.json 缺失为正常（编号 0-88 共 89 个）。
用法: python _xr_hexg_rebuild.py [--dry]
"""
import json, os, re, sys, shutil

BID = "497b0228c3a6"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

def norm(s):
    return re.sub(r"\s+", "", s or "")

old = {}
for i in range(89):
    p = os.path.join(SRC, f"{i}.json")
    assert os.path.exists(p), f"缺旧文件 {p}"
    old[i] = json.load(open(p, encoding="utf-8"))

# ---- 结构表 ----
# (part, title_from, sources, sections)
#   title_from: 组织层标题继承源（读该文件 title）或 None(=sources[0])
#   sections: None=无 / "auto"=从章内按 [ABC]\s*\. 行提取 / [n,...]=源章降级（标题读各自文件）
#             / ("text", [标题,...])=显式标题（49 章内锚点）
STANDS = [1, 2, 3, 15, 16, 17, 50, 51, 52, 53, 88]          # 独立章（无 part），0 扉页删除
# 15/50 译后记文件尾部粘入下一版目录页（"目录"→"返回总目录"，含"返回总目录"）——剥除，题献保留
STRIP_TOC = {15, 50}
# 18/54 导论文件中间压入部门标题"第一部分. 逻辑学."与"引论."行（逻辑学引论标题）——剥除
STRIP_STRUCT = {18, 54}
V1817 = [
    ("逻辑学（1817年版）", 4, [4], "auto"),
    ("逻辑学（1817年版）", 5, [5], "auto"),
    ("逻辑学（1817年版）", 6, [6], "auto"),
    ("自然哲学（1817年版）", 7, [7], None),
    ("自然哲学（1817年版）", 8, [8], None),
    ("自然哲学（1817年版）", 9, [9], "auto"),
    ("自然哲学（1817年版）", 10, [10], "auto"),
    ("精神哲学（1817年版）", 11, [11], None),
    ("精神哲学（1817年版）", 12, [12], "auto"),
    ("精神哲学（1817年版）", 13, [13], "auto"),
    ("精神哲学（1817年版）", 14, [14], ("text", ["a. 艺术宗教.", "b. 受启宗教.", "c. 哲学."])),
]
V1827 = [
    ("逻辑学（1827年版）", 18, [18], None),
    ("逻辑学（1827年版）", 22, [19, 20, 21, 22], [19, 20, 21]),
    ("逻辑学（1827年版）", 4, [23, 24, 25], [23, 24, 25]),
    ("逻辑学（1827年版）", 5, [26, 27, 28], [26, 27, 28]),
    ("逻辑学（1827年版）", 6, [29, 30, 31], [29, 30, 31]),
    ("自然哲学（1827年版）", 32, [32], None),
    ("自然哲学（1827年版）", 8, [33, 34, 35], [33, 34, 35]),
    ("自然哲学（1827年版）", 9, [36, 37, 38], [36, 37, 38]),
    ("自然哲学（1827年版）", 10, [39, 40, 41], [39, 40, 41]),
    ("精神哲学（1827年版）", 42, [42], None),
    ("精神哲学（1827年版）", 12, [43, 44, 45], [43, 44, 45]),
    ("精神哲学（1827年版）", 13, [46, 47, 48], [46, 47, 48]),
    ("精神哲学（1827年版）", 14, [49], ("text", ["a . 艺术.", "b . 受启宗教.", "c . 哲学."])),
]
V1830 = [
    ("逻辑学（1830年版）", 54, [54], None),
    ("逻辑学（1830年版）", 58, [55, 56, 57, 58], [55, 56, 57]),
    ("逻辑学（1830年版）", 4, [59, 60, 61], [59, 60, 61]),
    ("逻辑学（1830年版）", 5, [62, 63, 64], [62, 63, 64]),
    ("逻辑学（1830年版）", 6, [65, 66, 67], [65, 66, 67]),
    ("自然哲学（1830年版）", 68, [68], None),
    ("自然哲学（1830年版）", 8, [69, 70, 71], [69, 70, 71]),
    ("自然哲学（1830年版）", 9, [72, 73, 74], [72, 73, 74]),
    ("自然哲学（1830年版）", 10, [75, 76, 77], [75, 76, 77]),
    ("精神哲学（1830年版）", 78, [78], None),
    ("精神哲学（1830年版）", 12, [79, 80, 81], [79, 80, 81]),
    ("精神哲学（1830年版）", 13, [82, 83, 84], [82, 83, 84]),
    ("精神哲学（1830年版）", 14, [85, 86, 87], [85, 86, 87]),
]
ALPHA = re.compile(r"^[ABC]\s*\.\s*\S+\s*\.$")

def strip_toc_residue(blocks):
    """剥译后记尾部粘入的下一版目录页（"目录"→"返回总目录"，含首尾行）。无则原样返回。"""
    idxs = [k for k, b in enumerate(blocks)
            if isinstance(b, dict) and "value" in b and norm(b["value"]) in ("目录", "返回总目录")]
    if len(idxs) >= 2:
        a, b2 = idxs[0], idxs[-1]
        del blocks[a:b2 + 1]
    return blocks

def strip_struct_titles(blocks):
    """剥导论文件中压入的部门/引论标题行（"第一部分. 逻辑学."/"引论."）。"""
    out = []
    for b in blocks:
        if isinstance(b, dict) and "value" in b and norm(b["value"]) in ("第一部分.逻辑学.", "引论."):
            continue
        out.append(b)
    return out

def sec_titles(srcs, spec):
    """返回 (title 列表, 段边界块索引或 None)。spec=None → 无 section。"""
    if spec is None:
        return [], None
    if isinstance(spec, tuple) and spec[0] == "text":
        return list(spec[1]), None
    if spec == "auto":
        ch = old[srcs[0]]
        vals = [(k, b.get("value", "")) for k, b in enumerate(ch["content"])
                if isinstance(b, dict) and "value" in b]
        hits = [v for k, v in vals if ALPHA.match(v)]
        if len(hits) != 3:
            print(f"⚠ [{srcs[0]}] auto 提取 {len(hits)} 个字母节（期望 3）: {hits}")
        return hits, None
    return [old[s]["title"] for s in spec], None

# ---- 组装 ----
toc = []
files = {}
idx = 0
cur_part = None

def push_ch(title, blocks, secs):
    global idx
    files[idx] = {"index": idx, "title": title, "content": blocks}
    toc.append({"type": "chapter", "title": title, "index": idx, "level": 1})
    for si, st in enumerate(secs, 1):
        toc.append({"type": "section", "title": st, "index": idx, "sec": si, "level": 2})
    idx += 1

for si in STANDS:  # 独立章
    blocks = list(old[si]["content"])
    if si in STRIP_TOC:
        blocks = strip_toc_residue(blocks)
    if si in STRIP_STRUCT:
        blocks = strip_struct_titles(blocks)
    push_ch(old[si]["title"], blocks, [])

for grp in (V1817, V1827, V1830):
    prev_part = None
    for part, tf, srcs, spec in grp:
        if part != prev_part:
            toc.append({"type": "part", "title": part, "index": idx, "level": 0})
            prev_part = part
        title = old[tf]["title"]
        blocks = []
        for s in srcs:
            bs = list(old[s]["content"])
            if s in STRIP_TOC:
                bs = strip_toc_residue(bs)
            if s in STRIP_STRUCT:
                bs = strip_struct_titles(bs)
            blocks.extend(bs)
        secs, _ = sec_titles(srcs, spec)
        push_ch(title, blocks, secs)

# ---- 校验 ----
n_part = sum(1 for t in toc if t["type"] == "part")
n_sec = sum(1 for t in toc if t["type"] == "section")
assert n_part == 9, n_part
assert len(files) == 48, len(files)
assert n_sec == 84, n_sec
for i, t in enumerate(toc):
    if t["type"] == "section" and (i == 0 or toc[i - 1]["type"] != "section" or toc[i - 1]["index"] != t["index"]):
        assert toc[i - 1]["type"] == "chapter" and toc[i - 1]["index"] == t["index"], f"section 错位: {t}"

total_chars = 0
for i in sorted(files):
    nc = sum(len(b.get("value", "")) for b in files[i]["content"])
    total_chars += nc
    print(f"  {i:3d} {files[i]['title'][:36]:38s} {nc:7d} 字")
print(f"总: {len(files)} 章 + {n_part} part + {n_sec} section, {total_chars} 字符（旧 89 章平级, cc 89→48）")
old_total = 0
for i in range(89):
    old_total += sum(len(b.get("value", "")) for b in old[i].get("content", []))
print(f"旧数据总字数: {old_total}（删 0 扉页后差 {old_total - total_chars}）")
for t in toc:
    ind = "  " * t.get("level", 1)
    print(f"{ind}[{t['type']} {t.get('sec','')}] {t['title'][:40]}")
print("首:", files[0]["title"], "| 末:", files[47]["title"])

if "--dry" in sys.argv:
    title_norms = {norm(t["title"]) for t in toc}
    n_res = 0
    for i, ch in files.items():
        for b in ch["content"]:
            if "value" not in b:
                continue
            v = b["value"]
            nv = norm(v)
            if nv in {"未知", "目录"} or (len(v) <= 40 and nv in title_norms):
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
    "title": old_meta.get("title") or "哲学科学全书纲要",
    "author": old_meta.get("author") or "黑格尔",
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
