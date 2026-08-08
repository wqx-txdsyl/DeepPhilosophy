# -*- coding: utf-8 -*-
"""#132 时代的精神状况（卡尔·雅斯贝尔斯，王德峰译）fa7ea6998d5b 重建
病因（CHKLIST ✗B 五编标题缺失，编下章齐全但只有章一级）:
  旧数据 21 文件平铺：版权/前言/导言/目录+五编章节，编级 part 全缺，章与章平级；
  且旧"目录"章(15792字)内容实为导言正文（错位导入），旧导言仅 2546 字（缺大部分）。
EPUB 源（F:/philosophy/西方/卡尔·雅斯贝尔斯/时代的精神状况.epub）验证（spine 31）:
  0 titlepage(跳) / 1 版权信息(109字,删) / 2 英译本重印前言(h1 369字) /
  3 导言(h1 17230字) / 4 目录(261字) / 5 第一编名页(10字,跳) / 6 第一编导言(828字) /
  7-12 第一~六章(第一编 生活秩序的界限) / 13 第二编名页(9字,跳) / 14 第二编导言(566字) /
  15-17 第一~三章(第二编 整体中的意志) / 18 第三编名页(12字,跳) / 19 第三编导言(1005字) /
  20-21 第一~二章(第三编 精神的衰亡与可能性) / 22 第四编名页(14字,跳) / 23 第四编导言(3169字) /
  24-25 第一~二章(第四编 当代关于人的实存的观念) / 26 第五编名页(10字,跳) /
  27-29 第一~三章(第五编 人类可能的未来) / 30 译后记(h1 4788字)。
重建:
  [ch] 英译本重印前言 / 导言 / 目录 / 译后记
  [part l0] 第一篇 生活秩序的界限 ×5 编（编名页标题承载；第五编无编前导言）
    [ch] 第X篇导言（编前导言正文，剥离编名标题行）
    [ch] 各章（h2 章标题剥离；h3 节标题保留为正文块）
  内容 = spine 块流（BLOCK_TAGS 切分，同 rebuild_spine._body_to_blocks）。
  cc 21 → 24（3 前置 + 16 章 + 4 编导言 + 1 译后记）+ 5 part。
用法: python _xr_sdjszk_rebuild.py [--dry]
"""
import json, os, re, sys, shutil, zipfile
from bs4 import BeautifulSoup, NavigableString

BID = "fa7ea6998d5b"
EPUB = "F:/philosophy/西方/卡尔·雅斯贝尔斯/时代的精神状况.epub"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

def norm(s):
    return re.sub(r"\s+", "", s or "")

# ---- EPUB 读取 ----
z = zipfile.ZipFile(EPUB)
opf_path = [n for n in z.namelist() if n.endswith(".opf")][0]
opf_txt = z.read(opf_path).decode("utf-8", "ignore")
manif = {}
for m in re.finditer(r"<item[^>]*?/?>", opf_txt):
    tag = m.group(0)
    mid = re.search(r'id="([^"]+)"', tag)
    mhref = re.search(r'href="([^"]+)"', tag)
    if mid and mhref:
        manif[mid.group(1)] = mhref.group(1)
spine = [manif[rid] for rid in re.findall(r'<itemref[^>]*?idref="([^"]+)"', opf_txt) if rid in manif]
assert len(spine) == 31, len(spine)

def read_file(href):
    cand = [n for n in z.namelist() if n.split("/")[-1] == href.split("/")[-1]]
    assert cand, href
    return z.read(cand[0]).decode("utf-8", "ignore")

BLOCK_TAGS = {'p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
              'li', 'blockquote', 'pre', 'section', 'article', 'br', 'hr'}

def blocks_from_desc(desc):
    blocks = []
    pending = ""
    def flush():
        nonlocal pending
        if pending:
            blocks.append({"type": "text", "value": pending.strip()})
            pending = ""
    for el in desc:
        if getattr(el, "name", None) in ("script", "style", "nav", "head", "title"):
            continue
        if getattr(el, "name", None) in BLOCK_TAGS:
            flush()
            continue
        if isinstance(el, NavigableString):
            text = el.strip()
            if text:
                if pending:
                    pending += text if text in "，。；：！？、「」『』“”‘’（）" else " " + text
                else:
                    pending = text
    flush()
    return blocks

file_blocks = {}
for si, href in enumerate(spine):
    raw = read_file(href)
    soup = BeautifulSoup(raw, "html.parser")
    for t in soup(["script", "style", "nav", "head", "title"]):
        t.decompose()
    body = soup.body or soup
    file_blocks[si] = blocks_from_desc(body.descendants)

# ---- 结构表（spine 驱动）----
LEAFS = [2, 3, 4, 30]          # 英译本重印前言 / 导言 / 目录 / 译后记
BIAN = [                        # (part标题, 编名页, 编导言页或None, [章spine...])
    ("第一篇 生活秩序的界限", 5, 6, [7, 8, 9, 10, 11, 12]),
    ("第二篇 整体中的意志", 13, 14, [15, 16, 17]),
    ("第三篇 精神的衰亡与可能性", 18, 19, [20, 21]),
    ("第四篇 当代关于人的实存的观念", 22, 23, [24, 25]),
    ("第五篇 人类可能的未来", 26, None, [27, 28, 29]),
]
BIAN_TEXT = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五"}

toc = []
files = {}
idx = 0

def push_ch(title, blocks):
    global idx
    # 剥离章首标题块（EPUB 文件首块 = h1/h2 标题文本，toc 已承载）
    while blocks and blocks[0].get("type") == "text" and norm(blocks[0]["value"]) == norm(title):
        blocks = blocks[1:]
    files[idx] = {"index": idx, "title": title, "content": blocks}
    toc.append({"type": "chapter", "title": title, "index": idx, "level": 1})
    idx += 1

# 前置叶章（目录章固定标题"目录"）
for si in LEAFS:
    blk = file_blocks[si]
    title = "目录" if si == 4 else (blk[0]["value"] if blk and blk[0].get("type") == "text" else f"part{si}")
    push_ch(title, blk)

# 五编
for k, (pt, tpage, intro, chs) in enumerate(BIAN):
    assert not file_blocks[tpage], (tpage, file_blocks[tpage])   # 编名页应为纯标题(跳过)
    toc.append({"type": "part", "title": pt, "index": idx, "level": 0})
    if intro is not None:
        # 编前导言章（篇名在 EPUB head/title，已被删；blocks 即导言正文）
        push_ch(f"第{BIAN_TEXT[k+1]}篇导言", file_blocks[intro])
    for si in chs:
        blk = file_blocks[si]
        title = blk[0]["value"] if blk and blk[0].get("type") == "text" else f"章{si}"
        push_ch(title, blk)

assert len(files) == 24, len(files)        # 4 叶 + 4 编导言 + 16 章
assert sum(1 for t in toc if t["type"] == "part") == 5
assert idx == 24

# ---- 校验 ----
total_chars = 0
for i in sorted(files):
    nc = sum(len(b.get("value", "")) for b in files[i]["content"])
    total_chars += nc
    print(f"  {i:2d} {files[i]['title'][:44]:46s} {nc:7d} 字")
print(f"总: {len(files)} 章 + 5 part, {total_chars} 字符（EPUB 全量, 旧 21 文件 {0} 参照下）")
old_total = 0
if os.path.isdir(SRC):
    for fn in os.listdir(SRC):
        if fn.endswith(".json") and fn != "meta.json":
            ch = json.load(open(os.path.join(SRC, fn), encoding="utf-8"))
            old_total += sum(len(b.get("value", "")) for b in ch["content"] if b.get("type") == "text")
print(f"旧数据总字数: {old_total}（旧目录章 15792 字 = 导言错位, 已由 EPUB 导言 17230 字全量替换）")
for t in toc:
    ind = "  " * t.get("level", 1)
    print(f"{ind}[{t['type']}] {t['title'][:44]}")
print("首:", files[0]["title"], "| 末:", files[23]["title"])

if "--dry" in sys.argv:
    title_norms = {norm(t["title"]) for t in toc if t["type"] == "chapter"}
    n_res = 0
    for i, ch in files.items():
        if ch["title"] == "目录":
            continue   # 目录章正文含全部章名，跳过
        for k, b in enumerate(ch["content"]):
            if "value" not in b or not b["value"]:
                continue
            nv = norm(b["value"])
            prev = ch["content"][k - 1] if k > 0 else {}
            if len(nv) <= 14 and nv in title_norms and prev.get("type") != "image":
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
    "title": old_meta.get("title") or "时代的精神状况",
    "author": old_meta.get("author") or "卡尔·雅斯贝尔斯",
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
