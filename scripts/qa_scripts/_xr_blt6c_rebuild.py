# -*- coding: utf-8 -*-
"""#135 柏拉图哲学作品集（套装6册）（柏拉图）e74dc59d508e 重建
病因（CHKLIST ✗B 套装册级缺失）:
  旧数据 43 文件平铺：理想国十卷(✓chapter)+游叙弗伦等篇平铺，无册级 part；
  且第二册缺 3 个篇名页（游叙弗伦/申辩/克力同），注（脚注集）并入正文章。
EPUB 源（F:/philosophy/西方/柏拉图/柏拉图哲学作品集（套装6册）.epub）验证（spine 61）:
  6 册以 Cover/frontcover 插页切分：
  第一册 理想国（3 册目录/4 版权/5 出版说明/6 译者引言/7-16 第一~十卷/17 索引/
    18-19 人名地名索引×2/20 版本简目）｜第二册 游叙弗伦·申辩·克力同（22-39：
    篇名页 24/29/33+译者序×2+提要×3+正文×3+译后话×3+译名对照表+年表）｜
  第三册 智者（41-45）｜第四册 泰阿泰德（47-50：正文+泰阿泰德注独立文件）｜
  第五册 斐德若篇（52-55：正文+题解+斐德若注）｜第六册 卡尔弥德篇·枚农篇（57-60：正文×2+注释）。
  与旧数据同源验证：理想国第一卷首尾逐字一致、注块数一致（11=11）。
重建:
  [part l0] 第一册 理想国 ×6 册（分册页/封面/册目录/版权/篇名页跳）
    [ch] 各文件（h1/文本标题剥离；人名地名索引标题+正文同块→字面前缀剥离）
  内容 = spine 块流（BLOCK_TAGS 切分，同 rebuild_spine._body_to_blocks）。
  cc 43 → 39 + 6 part。
用法: python _xr_blt6c_rebuild.py [--dry]
"""
import json, os, re, sys, shutil, zipfile
from bs4 import BeautifulSoup, NavigableString

BID = "e74dc59d508e"
EPUB = "F:/philosophy/西方/柏拉图/柏拉图哲学作品集（套装6册）.epub"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

def norm(s):
    return re.sub(r"\s+", "", s or "")

# ---- EPUB 读取 ----
z = zipfile.ZipFile(EPUB)
names = z.namelist()
opf_path = [n for n in names if n.endswith(".opf")][0]
opf_txt = z.read(opf_path).decode("utf-8", "ignore")
manif = {}
for m in re.finditer(r"<item[^>]*?/?>", opf_txt):
    tag = m.group(0)
    mid = re.search(r'id="([^"]+)"', tag)
    mhref = re.search(r'href="([^"]+)"', tag)
    if mid and mhref:
        manif[mid.group(1)] = mhref.group(1)
spine = [manif[rid] for rid in re.findall(r'<itemref[^>]*?idref="([^"]+)"', opf_txt) if rid in manif]
assert len(spine) == 61, len(spine)

def read_file(si):
    href = spine[si]
    cand = [n for n in names if n.split("/")[-1] == href.split("/")[-1]]
    assert cand, (si, href)
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
for si in range(61):
    raw = read_file(si)
    soup = BeautifulSoup(raw, "html.parser")
    for t in soup(["script", "style", "nav", "head", "title"]):
        t.decompose()
    body = soup.body or soup
    file_blocks[si] = blocks_from_desc(body.descendants)

# ---- 结构表（spine 驱动）----
# 每册: (part标题, [(章标题, spine, 字面前缀或None), ...])
VOLS = [
    ("第一册 理想国", [
        ("汉译世界学术名著丛书出版说明", 5, None),
        ("译者引言", 6, None),
        ("第一卷", 7, None), ("第二卷", 8, None), ("第三卷", 9, None),
        ("第四卷", 10, None), ("第五卷", 11, None), ("第六卷", 12, None),
        ("第七卷", 13, None), ("第八卷", 14, None), ("第九卷", 15, None),
        ("第十卷", 16, None),
        ("索引", 17, None),
        ("人名地名索引之一", 18, "人名地名索引之一"),
        ("人名地名索引之二", 19, "人名地名索引之二"),
        ("本书版本简目", 20, None),
    ]),
    ("第二册 游叙弗伦·苏格拉底的申辩·克力同", [
        ("译者序", 25, None),
        ("《游叙弗伦》提要", 26, None),
        ("游叙弗伦——论虔敬", 27, None),
        ("译后话", 28, None),
        ("《苏格拉底的申辩》提要", 30, None),
        ("苏格拉底的申辩", 31, None),
        ("译后话", 32, None),
        ("译者序", 34, None),
        ("《克力同》提要", 35, None),
        ("克力同〔或论义务——关于伦理的〕", 36, None),
        ("译后话", 37, None),
        ("译名对照表", 38, None),
        ("柏拉图生平和著作年表", 39, None),
    ]),
    ("第三册 智者", [
        ("译者前言", 43, None),
        ("智者", 44, None),
    ]),
    ("第四册 泰阿泰德", [
        ("译者前言", 48, None),
        ("泰阿泰德", 49, None),
        ("泰阿泰德注", 50, "泰阿泰德"),
    ]),
    ("第五册 斐德若篇", [
        ("斐德若篇", 53, None),
        ("附录：《斐德若篇》题解", 54, None),
        ("斐德若注", 55, "斐德若篇"),
    ]),
    ("第六册 卡尔弥德篇·枚农篇", [
        ("卡尔弥德篇", 58, "卡尔弥德篇 枚农篇"),
        ("枚农篇", 59, "卡尔弥德篇 枚农篇"),
        ("注释", 60, "卡尔弥德篇 枚农篇"),
    ]),
]

toc = []
files = {}
idx = 0

def strip_blocks(blocks, title, pfx):
    # 1) 完整标题块（h1/文本内标题行，含重复标题块）
    while blocks and blocks[0].get("type") == "text" and norm(blocks[0]["value"]) == norm(title):
        blocks = blocks[1:]
    # 2) 标题+正文同块 → 字面前缀剥离
    if pfx and blocks and blocks[0].get("type") == "text":
        v = blocks[0]["value"]
        if v.startswith(pfx):
            blocks[0] = {"type": "text", "value": v[len(pfx):].lstrip()}
    return blocks

for pt, chs in VOLS:
    toc.append({"type": "part", "title": pt, "index": idx, "level": 0})
    for t, si, pfx in chs:
        blocks = strip_blocks(file_blocks[si], t, pfx)
        files[idx] = {"index": idx, "title": t, "content": blocks}
        toc.append({"type": "chapter", "title": t, "index": idx, "level": 1})
        idx += 1

assert len(files) == 40, len(files)        # 16+13+2+3+3+3
assert sum(1 for t in toc if t["type"] == "part") == 6
assert idx == 40

# ---- 校验 ----
total_chars = 0
for i in sorted(files):
    nc = sum(len(b.get("value", "")) for b in files[i]["content"])
    total_chars += nc
    print(f"  {i:2d} {files[i]['title'][:46]:48s} {nc:7d} 字")
print(f"总: {len(files)} 章 + 6 part, {total_chars} 字符（EPUB 全量）")
old_total = 0
if os.path.isdir(SRC):
    for fn in os.listdir(SRC):
        if fn.endswith(".json") and fn != "meta.json":
            ch = json.load(open(os.path.join(SRC, fn), encoding="utf-8"))
            old_total += sum(len(b.get("value", "")) for b in ch["content"] if b.get("type") == "text")
print(f"旧数据总字数: {old_total}（删 7 导航/元数据页 + 注独立成章）")
for t in toc:
    ind = "  " * t.get("level", 1)
    print(f"{ind}[{t['type']}] {t['title'][:44]}")
print("首:", files[0]["title"], "| 末:", files[38]["title"])

if "--dry" in sys.argv:
    # "注释"排除: 理想国每卷尾注列表前的标题块是正文预期（与第六册"注释"章同名误报）
    title_norms = {norm(t["title"]) for t in toc if t["type"] == "chapter" and t["title"] != "注释"}
    n_res = 0
    for i, ch in files.items():
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
    "title": old_meta.get("title") or "柏拉图哲学作品集（套装6册）",
    "author": old_meta.get("author") or "柏拉图",
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
