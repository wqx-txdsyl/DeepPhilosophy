# -*- coding: utf-8 -*-
"""#118 思辨与立场：生活中无处不在的批判性思维工具（理查德·保罗，人大社 2016）9fb1dbc22de1 重建
病因（CHKLIST ✗B 层级划分当章平铺）:
  旧数据 104 文件全部平铺为章（无 section），且标题与内容错位（旧 6"急速变化中的复杂世界"
  内容实为前言 text00006）、缺 15 章页 + 约 21 节正文（spine 138 vs 旧 104，222501 vs 205381 字）。
  ncx 127 条漏约 13 节且嵌套标记缺失 —— 重建不依赖 ncx，用 spine 顺序 + 文件 h 标题。
EPUB 源（F:/philosophy/西方/理查德·保罗/思辨与立场：生活中无处不在的批判性思维工具.epub）验证:
  全 138 文件 UTF-8。结构 = 7 叶（000 版权/001 目录/002 赞誉/003 推荐序1/004 推荐序2/005 译者序/
  006 前言）+ 15 章（h1 章页文件 007/012/015/025/030/035/053/066/072/081/089/098/109/119/127，
  其中 007/012/015/066 章页内含 h2 首节）+ 116 节文件（h2）+ 137 阅想·心理叶章。
  53 张图分布在 13 个 html（md5 内容[:10] 与 book_images 已有 54 个 webp 全部对应，0 缺失）。
重建:
  [ch] 7 叶（000-006，标题 = 文件 h1 原文）
  [ch] 15 章（标题 = 章页 h1 原文，如 "01 变化与危险加剧的世界中的思维"）
    [sec] 116 节（标题 = 节文件 h2 / 章页内 h2 原文；sec = 节标题块在章 content 的下标）
  [ch] 137 阅想·心理
  内容 = spine 顺序块流（BLOCK_TAGS 切分，同 rebuild_spine._body_to_blocks；img → image 块，
  src 重写为 /api/books/{bid}/image/{bid}_{hash}.webp，w/h 读 webp 实际尺寸）。h3 子标题自然保留为正文块。
  cc 104 → 23（22 章 + 1 阅想·心理叶章）+ 116 section。
用法: python _xr_sbylc_rebuild.py [--dry]
"""
import json, os, re, sys, shutil, hashlib, zipfile
from bs4 import BeautifulSoup, NavigableString

BID = "9fb1dbc22de1"
EPUB = "F:/philosophy/西方/理查德·保罗/思辨与立场：生活中无处不在的批判性思维工具.epub"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"
IMG_DIR = "f:/program/Python/PhiAgent/backend/data/book_images"

def norm(s):
    return re.sub(r"\s+", "", s or "")

# ---- EPUB 读取 ----
z = zipfile.ZipFile(EPUB)

def is_image(n):
    fn = n.split("/")[-1].lower()
    return fn.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp")) and "__MACOSX" not in n

# 图片映射: 文件名 → API src（md5 内容[:10]，与 rebuild_spine 同规则）
images = {}
for n in z.namelist():
    if is_image(n):
        data = z.read(n)
        ih = hashlib.md5(data).hexdigest()[:10]
        images[n.split("/")[-1]] = f"/api/books/{BID}/image/{BID}_{ih}.webp"

# spine 顺序（修复 item 属性顺序不定）
opf_txt = z.read("OEBPS/content.opf").decode("utf-8", "ignore")
manif = {}
for m in re.finditer(r"<item[^>]*?/?>", opf_txt):
    tag = m.group(0)
    mid = re.search(r'id="([^"]+)"', tag)
    mhref = re.search(r'href="([^"]+)"', tag)
    if mid and mhref:
        manif[mid.group(1)] = mhref.group(1)
spine = [manif[rid] for rid in re.findall(r'<itemref[^>]*?idref="([^"]+)"', opf_txt) if rid in manif]
assert len(spine) == 138, len(spine)

# webp 尺寸（小图内联判定用）
from PIL import Image
def img_wh(hash_name):
    p = os.path.join(IMG_DIR, hash_name)
    with Image.open(p) as im:
        return im.size

BLOCK_TAGS = {'p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
              'li', 'blockquote', 'pre', 'section', 'article', 'br', 'hr'}

def blocks_from_desc(desc):
    """同 rebuild_spine._body_to_blocks：段落级标签切分，img → image 块（src 重写 + alt 清洗 + w/h）"""
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
file_blocks = {}   # spine idx -> blocks
file_heads = {}    # spine idx -> [(tag, title), ...]
for si, href in enumerate(spine):
    raw = z.read("OEBPS/" + href).decode("utf-8", "ignore")
    soup = BeautifulSoup(raw, "html.parser")
    for t in soup(["script", "style", "nav", "head", "title"]):
        t.decompose()
    body = soup.body or soup
    file_blocks[si] = blocks_from_desc(body.descendants)
    heads = [(el.name, re.sub(r"\s+", " ", el.get_text()).strip())
             for el in soup.find_all(["h1", "h2"])]
    file_heads[si] = heads

# ---- 结构表（spine 驱动）----
LEAFS = [0, 1, 2, 3, 4, 5, 6]                            # 7 叶
FINAL_LEAF = 137                                          # 阅想·心理（spine 末位）
H1_FILES = [7, 12, 15, 25, 30, 35, 53, 66, 72, 81, 89, 98, 109, 119, 127]

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

# 叶章
for si in LEAFS:
    h1t = file_heads[si][0][1] if file_heads[si] else f"part{si}"
    push_ch(h1t, file_blocks[si], [])

# 15 章
sec_total = 0
for k, h1s in enumerate(H1_FILES):
    end = H1_FILES[k + 1] if k + 1 < len(H1_FILES) else FINAL_LEAF
    group = list(range(h1s, end))
    ch_heads = file_heads[h1s]
    ch_title = ch_heads[0][1] if ch_heads and ch_heads[0][0] == "h1" else f"第{k+1}章"
    blocks = list(file_blocks[h1s])
    secs = []
    # 章页内 h2 首节（若有）
    for htag, htitle in ch_heads[1:]:
        if htag == "h2":
            for bi, b in enumerate(blocks):
                if b.get("type") == "text" and norm(b["value"]) == norm(htitle):
                    secs.append((htitle, bi))
                    break
    # 节文件
    for si in group[1:]:
        hd = file_heads[si]
        stitle = hd[0][1] if hd and hd[0][0] == "h2" else (hd[0][1] if hd else f"节{si}")
        secs.append((stitle, len(blocks)))
        blocks.extend(file_blocks[si])
    sec_total += len(secs)
    push_ch(ch_title, blocks, secs)

# 阅想·心理（末位叶章）
h1t = file_heads[FINAL_LEAF][0][1] if file_heads[FINAL_LEAF] else "阅想·心理"
push_ch(h1t, file_blocks[FINAL_LEAF], [])

assert len(files) == 23, len(files)          # 7 叶 + 15 章 + 阅想·心理
assert sec_total == 119, sec_total          # 115 节文件 + 4 章页内 h2 首节
assert idx == 23

# ---- 校验 ----
total_chars = 0
for i in sorted(files):
    nc = sum(len(b.get("value", "")) for b in files[i]["content"])
    total_chars += nc
    n_sec = sum(1 for t in toc if t["type"] == "section" and t["index"] == i)
    print(f"  {i:2d} {files[i]['title'][:44]:46s} {nc:7d} 字 sec:{n_sec}")
print(f"总: {len(files)} 章 + {sec_total} section, {total_chars} 字符（EPUB 全量 222501, 旧 205381）")
print(f"图片块: {sum(1 for i in files for b in files[i]['content'] if b.get('type') == 'image')}（EPUB 53 img 引用）")
for t in toc:
    ind = "  " * t.get("level", 1)
    print(f"{ind}[{t['type']}] {t['title'][:40]}" + (f" sec:{t.get('sec')}" if t["type"] == "section" else ""))

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
    "title": old_meta.get("title") or "思辨与立场：生活中无处不在的批判性思维工具",
    "author": old_meta.get("author") or "理查德·保罗",
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
