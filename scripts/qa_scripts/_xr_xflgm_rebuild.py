# -*- coding: utf-8 -*-
"""#129 新弗雷格主义的算术哲学（许涤非，中国社会科学出版社 2022）64056c6623ee 重建
病因（CHKLIST ✗B 节当章平铺，标题混入正文首句）:
  旧数据 16 文件平铺 = 节级（多"第1节"重复，标题=节题+正文首句拼接），无章/部分层级；
  author 错标"戈特洛布·弗雷格"（实为许涤非）。
源 PDF（F:/philosophy/西方/戈特洛布·弗雷格/新弗雷格主义的算术哲学.pdf）验证:
  385 页全文本层（pymupdf 直接提取，无需 OCR）。目录 P5-8 确认结构:
  导论 + 第一部分 弗雷格的算术哲学遗产（第1-3章）+ 第二部分 新弗雷格主义的本体论
  （第4-7章）+ 第三部分 新弗雷格主义的认识论（第8-13章）+ 参考文献 + 后记。
重建:
  [ch] 导论（0.1-0.2 节）
  [part l0] 第一部分/第二部分/第三部分（部分标题页"第X部分"+部分名）
    [ch] 第1-13章（"第X 章"标题行首次出现 = 章开始；重复 = 页眉滤除）
      [sec] 71 节（正文"X.Y"节编号行，节名 = 下一行）
  页眉滤除: 页码（阿拉伯/罗马）/书名"新弗雷格主义的算术哲学"/章标题页眉（"第X章"+章名行）/
  正文"第X章"引用行（rest 非章名）保留。
  内容 = 页为单位块（正文行直接拼接）；author 修正为许涤非。
  cc 16 → 16（1 导论 + 13 章 + 参考文献 + 后记）+ 3 part + 71 section。
用法: python _xr_xflgm_rebuild.py [--dry]
"""
import json, os, re, sys, shutil
import fitz

BID = "64056c6623ee"
PDF = "F:/philosophy/西方/戈特洛布·弗雷格/新弗雷格主义的算术哲学.pdf"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

def clean(l):
    return re.sub(r"\s+", " ", l).strip()

doc = fitz.open(PDF)

# ---- 目录提取（P5-8）: 章名/部分名 ----
CH_TITLES = {}     # 章号(数字) -> 章名
PART_TITLES = {}   # 部分号(中文) -> 部分名
toc_lines = []
for p in range(5, 9):
    for l in doc[p].get_text().split("\n"):
        l = re.sub(r"\.{3,}.*$", "", clean(l))
        if l:
            toc_lines.append(l)
for i, l in enumerate(toc_lines):
    l = re.sub(r"(?:\.\s*){3,}.*$", "", l)   # 去点线（". . . ."或"....."）
    m = re.match(r"^第([0-9]+)[ ]?章\s*(.+)$", l)
    if m:
        CH_TITLES[int(m.group(1))] = m.group(2)
        continue
    m = re.match(r"^第([一二三四五六七八九十]+)[ ]?部分$", l)
    if m:
        nxt = clean(toc_lines[i + 1]) if i + 1 < len(toc_lines) else ""
        PART_TITLES[m.group(1)] = nxt
assert len(CH_TITLES) == 13, CH_TITLES
assert len(PART_TITLES) == 3, PART_TITLES
CH_NAME_NORMS = {re.sub(r"\s+", "", v) for v in CH_TITLES.values()}

CN = {"一": 1, "二": 2, "三": 3}
PART_ORDER = {"一": 1, "二": 2, "三": 3}
# 章 -> 部分号
CH_PART = {}
for i in range(1, 14):
    CH_PART[i] = 1 if i <= 3 else (2 if i <= 7 else 3)

# ---- 流式扫描（P9 导论起）----
toc = []
files = {}
idx = 0
sec_total = 0

def push_ch(title, blocks):
    global idx
    files[idx] = {"index": idx, "title": title, "content": blocks}
    toc.append({"type": "chapter", "title": title, "index": idx, "level": 1})
    idx += 1

def add_sec(title, sec_idx):
    global sec_total
    sec_total += 1
    toc.append({"type": "section", "title": title, "index": idx,
                "sec": sec_idx, "level": 2})

def is_page_num(l):
    return re.fullmatch(r"\d{1,3}", l) or re.fullmatch(r"[ivxlcdm]{1,5}", l)

cur_ch = None          # 当前章标题
cur_blocks = []        # 当前章 content 块
pending = []           # 当前页累积正文行
started_parts = set()
started_chs = set()

def flush_page():
    global pending
    if pending:
        cur_blocks.append({"type": "text", "value": "".join(pending)})
        pending = []

def flush_ch():
    global cur_ch, cur_blocks
    if cur_ch is not None:
        push_ch(cur_ch, cur_blocks)
        cur_ch = None
        cur_blocks = []

seen_titles = set()
for p in range(9, 385):
    lines = [clean(l) for l in doc[p].get_text().split("\n")]
    i = 0
    while i < len(lines):
        l = lines[i]
        i += 1
        if not l:
            continue
        if is_page_num(l) or l == "新弗雷格主义的算术哲学":
            continue
        # 部分标题
        m = re.match(r"^第([一二三四五六七八九十]+)[ ]?部分\s*$", l)
        if m:
            pn = PART_ORDER.get(m.group(1))
            if pn and pn not in started_parts:
                started_parts.add(pn)
                flush_page()
                flush_ch()
                title = f"第{m.group(1)}部分 {PART_TITLES[m.group(1)]}"
                toc.append({"type": "part", "title": title, "index": idx, "level": 0})
                # 部分名行（下一行）
                if i < len(lines) and clean(lines[i]) == PART_TITLES[m.group(1)]:
                    i += 1
            continue
        # 章标题（"第X 章" 独立行 或 "第X 章 章名"同行）
        m = re.match(r"^第([0-9]+)[ ]?章\s*(.*)$", l)
        if m and m.group(1).isdigit():
            n = int(m.group(1))
            rest = m.group(2)
            rest_norm = re.sub(r"\s+", "", rest)
            if rest_norm and rest_norm not in CH_NAME_NORMS:
                pending.append(l)   # 正文引用（如"第11章解释定义的先天性。…"）
                continue
            if n in started_chs:
                # 页眉: 滤该行 + 章名行
                if not rest and i < len(lines) and re.sub(r"\s+", "", clean(lines[i])) in CH_NAME_NORMS:
                    i += 1
                continue
            started_chs.add(n)
            flush_page()
            flush_ch()
            # 章名: 同行 rest 或下一行（页眉章名）
            name = rest if rest else CH_TITLES.get(n, "")
            if not rest and i < len(lines) and re.sub(r"\s+", "", clean(lines[i])) in CH_NAME_NORMS:
                name = clean(lines[i])
                i += 1
            cur_ch = f"第{n}章 {name}"
            continue
        # 导论/参考文献/后记
        if l in ("导论", "参考文献", "后记"):
            if l in seen_titles:
                continue   # 页眉
            seen_titles.add(l)
            flush_page()
            flush_ch()
            cur_ch = l
            continue
        # 导论竖排"导/论"
        if l == "导" and i < len(lines) and lines[i] == "论":
            i += 1
            seen_titles.add("导论")
            flush_page()
            flush_ch()
            cur_ch = "导论"
            continue
        # 节标题 X.Y（独立行 或 同行标题）
        m = re.match(r"^(\d{1,2}\.\d{1,2})(?:\s+(.*))?$", l)
        if m:
            title = m.group(2)
            if not title and i < len(lines):
                title = clean(lines[i])
                if title and not re.match(r"^\d{1,2}\.\d{1,2}", title):
                    i += 1   # 节名行（并入标题块前不入正文）
                else:
                    title = ""
            flush_page()
            cur_blocks.append({"type": "text", "value": title})
            add_sec(title, len(cur_blocks) - 1)
            continue
        pending.append(l)
    flush_page()
flush_ch()

assert idx == 16, idx   # 导论 + 13 章 + 参考文献 + 后记
assert len(started_chs) == 13, started_chs
assert sum(1 for t in toc if t["type"] == "part") == 3
assert sec_total == 71, sec_total

# ---- 校验 ----
total_chars = 0
for i in sorted(files):
    nc = sum(len(b.get("value", "")) for b in files[i]["content"])
    total_chars += nc
    n_sec = sum(1 for t in toc if t["type"] == "section" and t["index"] == i)
    print(f"  {i:2d} {files[i]['title'][:46]:48s} {nc:7d} 字 sec:{n_sec}")
print(f"总: {len(files)} 章 + 3 part + {sec_total} section, {total_chars} 字符（旧数据 16 文件平铺）")
for t in toc:
    ind = "  " * t.get("level", 1)
    print(f"{ind}[{t['type']}] {t['title'][:44]}")

if "--dry" in sys.argv:
    ch_norms = {re.sub(r"\s+", "", t["title"]) for t in toc if t["type"] == "chapter"}
    n_res = 0
    for i, ch in files.items():
        for k, b in enumerate(ch["content"]):
            nv = re.sub(r"\s+", "", b.get("value", ""))
            prev = ch["content"][k - 1] if k > 0 else {}
            if len(nv) <= 14 and nv in ch_norms and prev.get("type") != "image":
                print(f"⚠ 疑似章题残留 [{i} {ch['title'][:12]}]: {b['value'][:34]!r}")
                n_res += 1
    print(f"章题残留: {n_res}")
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
    "title": old_meta.get("title") or "新弗雷格主义的算术哲学",
    "author": "许涤非",   # 修正: 封面"许涤非 著"，非文件夹名"戈特洛布·弗雷格"
    "toc": toc,
    "cover": old_meta.get("cover"),
    "chapterCount": len(files),
    "chapterTitles": [ch["title"] for ch in files.values()],
}
json.dump(meta, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print(f"✓ 写入 {SRC}: {len(files)} 章 + meta.json（author=许涤非）")

shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
print("✓ 同步 DP chapters")

for p in (DETAIL_SRC, DETAIL_DST):
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))
        d["toc"] = toc
        d["chapterCount"] = len(files)
        d["chapterTitles"] = [ch["title"] for ch in files.values()]
        d["author"] = "许涤非"
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
        print(f"✓ book_detail 更新: {p}")

if os.path.exists(BOOKS_JSON):
    bj = json.load(open(BOOKS_JSON, encoding="utf-8"))
    bl = bj if isinstance(bj, list) else bj.get("books", [])
    hit = False
    for b in bl:
        if b.get("id") == BID:
            b["chapterCount"] = len(files)
            if b.get("author"):
                b["author"] = "许涤非"
            hit = True
    if hit:
        with open(BOOKS_JSON, "w", encoding="utf-8") as f:
            json.dump(bl if isinstance(bj, list) else {**bj, "books": bl}, f, ensure_ascii=False, indent=None)
        print("✓ books.json chapterCount/author 更新")
    else:
        print("⚠ books.json 未找到该书")
