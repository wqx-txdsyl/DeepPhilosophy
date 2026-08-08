# -*- coding: utf-8 -*-
"""#131 方法论·情志论（勒内·笛卡尔）49c80096b16d 重建（一次性，旧数据重组）
病因（CHKLIST ✗B 两书合集标题缺失，"第一部分"重复编号）:
  旧数据 12 文件平铺 = 0 版权信息（纯元数据 99 字）+ 1 导读 + 2 序 + 3-8 第一~六部分
  （方法论）+ 9-11 第一~三部分（情志论）。两本书各有"第一部分"，书级标题缺失。
EPUB 源（F:/philosophy/西方/勒内·笛卡尔/方法论·情志论.epub）验证:
  spine 15 = 0 cover / 1 Copyright（h1 版权信息, 删）/ 2 导读（h1, 2670 字）/
  3 方法论分卷页（h1, 25 字, 过渡页跳）/ 4-10 序+第一~六部分（h2, 方法论）/
  11 情志论分卷页（h1"情志论[1]", 9 字, 过渡页跳）/ 12-14 第一~三部分（h2, 情志论）。
  字数与旧数据逐文件几乎一致（2688≈2670, 3718≈3723...）→ 旧数据即 EPUB 同源平铺。
重建:
  [ch] 导读
  [part l0] 方法论（序 + 第一~六部分 ×7）
  [part l0] 情志论（第一~三部分 ×3）
  内容 = spine 块流（BLOCK_TAGS 切分，同 rebuild_spine._body_to_blocks）。
  cc 12 → 11（删 0 版权页 + 2 分卷过渡页跳过）。
用法: python _xr_fflqz_rebuild.py [--dry]
"""
import json, os, re, sys, shutil, zipfile
from bs4 import BeautifulSoup, NavigableString

BID = "49c80096b16d"
EPUB = "F:/philosophy/西方/勒内·笛卡尔/方法论·情志论.epub"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

def norm(s):
    return re.sub(r"\s+", "", s or "")

# ---- EPUB 读取 ----
z = zipfile.ZipFile(EPUB)
opf_txt = z.read("OEBPS/content.opf").decode("utf-8", "ignore")
manif = {}
for m in re.finditer(r"<item[^>]*?/?>", opf_txt):
    tag = m.group(0)
    mid = re.search(r'id="([^"]+)"', tag)
    mhref = re.search(r'href="([^"]+)"', tag)
    if mid and mhref:
        manif[mid.group(1)] = mhref.group(1)
spine = [manif[rid] for rid in re.findall(r'<itemref[^>]*?idref="([^"]+)"', opf_txt) if rid in manif]
assert len(spine) == 15, len(spine)

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

file_blocks = {}   # spine idx -> blocks
file_heads = {}    # spine idx -> [(tag, title), ...]
for si, href in enumerate(spine):
    raw = read_file(href)
    soup = BeautifulSoup(raw, "html.parser")
    for t in soup(["script", "style", "nav", "head", "title"]):
        t.decompose()
    body = soup.body or soup
    file_blocks[si] = blocks_from_desc(body.descendants)
    heads = [(el.name, re.sub(r"\s+", " ", el.get_text()).strip())
             for el in soup.find_all(["h1", "h2"])]
    file_heads[si] = heads
    nc = sum(len(b.get("value", "")) for b in file_blocks[si])
    print(f"  {si:2d} {href.split('/')[-1]:28s} {nc:6d}字 {[t for _, t in heads]}")

# ---- 结构表（spine 驱动）----
# 0 cover 跳 / 1 Copyright 删 / 2 导读 / 3 方法论分卷页跳
# 4-10 序+第一~六部分(方法论) / 11 情志论分卷页跳 / 12-14 第一~三部分(情志论)
D_SCHEMA = [
    ("方法论", [4, 5, 6, 7, 8, 9, 10]),     # 序 + 第一~六部分
    ("情志论", [12, 13, 14]),                # 第一~三部分
]

toc = []
files = {}
idx = 0

def push_ch(title, blocks):
    global idx
    # 剥离章首标题块（EPUB 每章文件首个块 = h 标题文本，toc 已承载标题，避免正文重复）
    if blocks and blocks[0].get("type") == "text" and norm(blocks[0]["value"]) == norm(title):
        blocks = blocks[1:]
    files[idx] = {"index": idx, "title": title, "content": blocks}
    toc.append({"type": "chapter", "title": title, "index": idx, "level": 1})
    idx += 1

# 导读（spine 2）
h1t = file_heads[2][0][1] if file_heads[2] else "导读"
push_ch(h1t, file_blocks[2])

# 两书 part
for pt, si_list in D_SCHEMA:
    toc.append({"type": "part", "title": pt, "index": idx, "level": 0})
    for si in si_list:
        hd = file_heads[si]
        stitle = hd[0][1] if hd and hd[0][0] in ("h1", "h2") else f"部分{si}"
        push_ch(stitle, file_blocks[si])

assert len(files) == 11, len(files)        # 导读 + 7 + 3
assert sum(1 for t in toc if t["type"] == "part") == 2
assert idx == 11

# ---- 校验 ----
total_chars = 0
for i in sorted(files):
    nc = sum(len(b.get("value", "")) for b in files[i]["content"])
    total_chars += nc
    print(f"  {i:2d} {files[i]['title'][:44]:46s} {nc:7d} 字")
print(f"总: {len(files)} 章 + 2 part, {total_chars} 字符（EPUB 全量, 旧 12 文件 {sum(len(b.get('value','')) for b in []) and 0 or 0} 参照旧字数）")
old_total = 0
if os.path.isdir(SRC):
    for fn in os.listdir(SRC):
        if fn.endswith(".json") and fn != "meta.json":
            ch = json.load(open(os.path.join(SRC, fn), encoding="utf-8"))
            old_total += sum(len(b.get("value", "")) for b in ch["content"] if b.get("type") == "text")
print(f"旧数据总字数: {old_total}（删 0 版权页 99 字 + 跳过 2 分卷过渡页）")
for t in toc:
    ind = "  " * t.get("level", 1)
    print(f"{ind}[{t['type']}] {t['title'][:40]}")
print("首:", files[0]["title"], "| 末:", files[10]["title"])

if "--dry" in sys.argv:
    title_norms = {norm(t["title"]) for t in toc if t["type"] == "chapter"}
    n_res = 0
    for i, ch in files.items():
        for k, b in enumerate(ch["content"]):
            if "value" not in b or not b["value"]:
                continue
            nv = norm(b["value"])
            prev = ch["content"][k - 1] if k > 0 else {}
            if len(nv) <= 12 and nv in title_norms and prev.get("type") != "image":
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
    "title": old_meta.get("title") or "方法论·情志论",
    "author": old_meta.get("author") or "勒内·笛卡尔",
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
