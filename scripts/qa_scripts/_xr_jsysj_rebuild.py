# -*- coding: utf-8 -*-
"""#123 技术与时间（斯蒂格勒，三卷合订）06e202800bb2 重建
病因（CHKLIST ✗M 缺第一章+章名全缺失）:
  旧数据 28 章平铺且标题全是"第N章"编号（无真实章名，编号从 2 起，对应 EPUB 003-030
  28 文件，一字不缺——实际内容完整，仅标题/层级缺失）。
EPUB 源（F:/philosophy/西方/伯纳德·斯蒂格勒/技术与时间.epub）验证:
  全 UTF-8。结构 = 003 主编的话 / 004 再版序言 / 第一卷（005 卷页+前言 / 006 导论 /
  第一部分 007 引论+第一章~第三章 / 第二部分 011 引论+第一章~第三章）/
  第二卷（015 前言 / 016-019 第一章~第四章）/ 第三卷（020 卷标题页含献词+名言 /
  021 告读者 / 022 导论 / 023-028 第一章~第六章）/ 029 后记 / 030 参考文献。
  18 张图全部已在 book_images（md5 内容[:10] 对上，0 缺失）。
重建:
  [ch] 主编的话 / 再版序言（h1 章）
  [part l0] 第一卷 / 第二卷 / 第三卷（h1 第X卷）
  [part l1] 第一部分 / 第二部分（h1 第X部分，卷内分组）
  [ch] 24 章 + 卷页章 + 后记 + 参考文献（h1/h2 标题原文）
  [sec] 237 节（h3 标题原文，如 "1.一般历史与技术史"）
  内容 = spine 顺序块流（同 rebuild_spine 规则；img → image 块 + w/h）。
  cc 28 → 29 + 4 part + 237 section。
用法: python _xr_jsysj_rebuild.py [--dry]
"""
import json, os, re, sys, shutil, hashlib, zipfile
from bs4 import BeautifulSoup, NavigableString

BID = "06e202800bb2"
EPUB = "F:/philosophy/西方/伯纳德·斯蒂格勒/技术与时间.epub"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"
IMG_DIR = "f:/program/Python/PhiAgent/backend/data/book_images"

def norm(s):
    return re.sub(r"\s+", "", s or "")

z = zipfile.ZipFile(EPUB)
names = z.namelist()

# 图片映射
images = {}
for n in names:
    fn = n.split("/")[-1].lower()
    if fn.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp")) and "__MACOSX" not in n \
            and "placeholder" not in fn and "data-uri" not in fn:
        ih = hashlib.md5(z.read(n)).hexdigest()[:10]
        images[n.split("/")[-1]] = f"/api/books/{BID}/image/{BID}_{ih}.webp"

# spine 顺序
opf_name = [n for n in names if n.endswith(".opf")][0]
opf = z.read(opf_name).decode("utf-8", "ignore")
manif = {}
for m in re.finditer(r"<item[^>]*?/?>", opf):
    tag = m.group(0)
    mid = re.search(r'id="([^"]+)"', tag)
    mhref = re.search(r'href="([^"]+)"', tag)
    if mid and mhref:
        manif[mid.group(1)] = mhref.group(1)
spine = [manif[r] for r in re.findall(r'<itemref[^>]*?idref="([^"]+)"', opf) if r in manif]
spine_files = []
for h in spine:
    cand = [n for n in names if n.split("/")[-1] == h.split("/")[-1]]
    if cand:
        spine_files.append(cand[0])
assert len(spine_files) == 30, len(spine_files)   # cover + 29

from PIL import Image
def img_wh(hash_name):
    with Image.open(os.path.join(IMG_DIR, hash_name)) as im:
        return im.size

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
        if getattr(el, "name", None) in ("img", "image"):
            flush()
            src = ""
            for attr in ("src", "href", "xlink:href", "{http://www.w3.org/1999/xlink}href"):
                v = el.get(attr, "")
                if v:
                    src = v
                    break
            if src:
                fn = src.split("/")[-1].split("?")[0]
                apisrc = images.get(fn)
                if not apisrc:
                    for k in images:
                        if k.endswith(fn) or fn.endswith(k):
                            apisrc = images[k]
                            break
                if apisrc:
                    _alt = (el.get("alt", "") or "").strip()
                    if _alt.lower() in ("alt", "image"):
                        _alt = ""
                    w, h = img_wh(apisrc.rsplit("/", 1)[-1])
                    blocks.append({"type": "image", "src": apisrc, "alt": _alt, "w": w, "h": h})
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

# ---- 每文件块流 + 标题 ----
file_blocks = {}
file_heads = {}
for si, fp in enumerate(spine_files):
    raw = z.read(fp).decode("utf-8", "ignore")
    soup = BeautifulSoup(raw, "html.parser")
    for t in soup(["script", "style", "nav", "head", "title"]):
        t.decompose()
    body = soup.body or soup
    file_blocks[si] = blocks_from_desc(body.descendants)
    heads = [(el.name, re.sub(r"\s+", " ", el.get_text()).strip())
             for el in soup.find_all(["h1", "h2", "h3"])]
    file_heads[si] = heads

# ---- 结构扫描（spine 驱动）----
# 规则: h1 第X卷 → part l0；h1 第X部分 → part l1；h1 其他 → 章；
#       h2 → 章（文件无 h1 时）或同文件章；h3 → section
def first_head(si, tag):
    for t, name in file_heads[si]:
        if t == tag:
            return name
    return None

toc = []
files = {}
idx = 0

def push_ch(title, blocks, secs):
    global idx
    files[idx] = {"index": idx, "title": title, "content": blocks}
    toc.append({"type": "chapter", "title": title, "index": idx, "level": 1})
    for st, sbi in secs:
        toc.append({"type": "section", "title": st, "index": idx, "sec": sbi, "level": 2})
    idx += 1

sec_total = 0
for si in range(1, len(spine_files)):   # 跳过 cover
    h1 = first_head(si, "h1")
    h2 = first_head(si, "h2")
    heads = file_heads[si]
    h3s = [(t, name) for t, name in heads if t == "h3"]
    if not h1 and not h2:
        continue   # nav.xhtml 等无标题文档
    if h1:
        if re.match(r"^第[一二三四五六七八九十]+卷", norm(h1)):
            # part 立即插入（在卷内第一章之前）
            toc.append({"type": "part", "title": h1, "index": idx, "level": 0})
            # 纯卷页（无 h2，如 020 第三卷标题页含献词+名言）→ 独立章
            if not h2:
                push_ch(h1, file_blocks[si], [])
                continue
        elif re.match(r"^第[一二三四五六七八九十]+部分", norm(h1)):
            toc.append({"type": "part", "title": h1, "index": idx, "level": 1})
            if not h2:
                push_ch(h1, file_blocks[si], [])
                continue
        elif not h2:
            # h1 章（主编的话/再版序言/后记/参考文献）
            secs = []
            for htag, htitle in h3s:
                for bi, b in enumerate(file_blocks[si]):
                    if b.get("type") == "text" and norm(b["value"]) == norm(htitle):
                        secs.append((htitle, bi))
                        break
            sec_total += len(secs)
            push_ch(h1, file_blocks[si], secs)
            continue
    # h2 章（含 h1 卷页内的 h2 前言/引论、纯 h2 文件）
    ch_title = h2 or h1
    blocks = list(file_blocks[si])
    secs = []
    for htag, htitle in h3s:
        for bi, b in enumerate(blocks):
            if b.get("type") == "text" and norm(b["value"]) == norm(htitle):
                secs.append((htitle, bi))
                break
    sec_total += len(secs)
    push_ch(ch_title, blocks, secs)

n_part0 = sum(1 for t in toc if t["type"] == "part" and t["level"] == 0)
n_part1 = sum(1 for t in toc if t["type"] == "part" and t["level"] == 1)
assert n_part0 == 3, n_part0          # 三卷
assert n_part1 == 2, n_part1          # 第一/第二部分
assert len(files) == 28, len(files)   # 2 前置 + 6 卷一 + 4 卷二 + 5 卷二卷 + 9 三卷 + 后记 + 参考文献
assert sec_total == 237, sec_total    # h3 节

# ---- 校验 ----
total_chars = 0
for i in sorted(files):
    nc = sum(len(b.get("value", "")) for b in files[i]["content"])
    total_chars += nc
    n_sec = sum(1 for t in toc if t["type"] == "section" and t["index"] == i)
    print(f"  {i:2d} {files[i]['title'][:46]:50s} {nc:7d} 字 sec:{n_sec}")
print(f"总: {len(files)} 章 + {n_part0}+{n_part1} part + {sec_total} section, {total_chars} 字符")
print(f"图片块: {sum(1 for i in files for b in files[i]['content'] if b.get('type') == 'image')}（EPUB 16 正文图）")
for t in toc:
    ind = "  " * t.get("level", 1)
    print(f"{ind}[{t['type']}] {t['title'][:44]}")

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
    "title": old_meta.get("title") or "技术与时间",
    "author": old_meta.get("author") or "贝尔纳·斯蒂格勒",
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
