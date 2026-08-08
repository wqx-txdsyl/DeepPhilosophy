# -*- coding: utf-8 -*-
"""#137 梅洛-庞蒂（莫里斯·梅洛-庞蒂，最伟大的思想家丛书）324c13db486e 重建
病因（CHKLIST ✗C 章节化失败）:
  旧数据 4 文件平铺且错位：0 序(640字)/1 第1章 早期著作/2 标题=正文首句乱码
  （"第三章 的任务是理解并且强调…"实为第3章正文首行）/3 参考书目——缺第 2、4 章，
  第 3 章标题乱码。
源 PDF（F:/philosophy/西方/莫里斯·梅洛-庞蒂/最伟大的思想家 - 梅洛-庞蒂.pdf）验证:
  131 页全文本层（pymupdf，无需 OCR）。P11 中文目录 + P12 英文原版目录确认结构：
  序(P13-14) / 1 早期著作(P15-56, 3 节) / 2 中期著作：政治介入(P57-71, 4 节) /
  3 最后的著作：可见的与不可见的(P72-114, 5 节) / 4 结语：梅洛－庞蒂的地位(P115-121) /
  参考书目(P122-130)。
重建:
  [ch] 序 + 第1~4章 + 参考书目（6 章）
    [sec] 12 节（目录节题独立行 = 节开始；节题块为 section 锚点）
  页眉滤除: 偶数页"On Merle…Ponty 梅洛－庞蒂"行（OCR 变体 Merleaz/Merleα）/
  奇数页章名页眉（章标题重复出现 = 页眉）/纯数字页码。
  内容 = 页为单位块（正文行拼接）。cc 4 → 6 + 12 section。
用法: python _xr_mlpd_rebuild.py [--dry]
"""
import json, os, re, sys, shutil
import fitz

BID = "324c13db486e"
PDF = "F:/philosophy/西方/莫里斯·梅洛-庞蒂/最伟大的思想家 - 梅洛-庞蒂.pdf"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

def norm(s):
    return re.sub(r"\s+", "", s or "")

doc = fitz.open(PDF)
assert len(doc) == 131, len(doc)

def clean(l):
    return re.sub(r"\s+", " ", l).strip()

# ---- 章/节标题表（目录 P11 核实）----
# 标题行形态: P15"1 早期著作"编号同行; P57/72/115"中期著作：政治介入"式编号独立行;
# 页眉行: 第2章不带号("中期著作：政治介入"), 第3章不带号, 第4章带号("4 结语：…")
CHS = ["序", "1 早期著作", "中期著作：政治介入", "最后的著作：可见的与不可见的",
       "结语：梅洛－庞蒂的地位", "参考书目"]
CH_FULL = ["序", "第1章 早期著作", "第2章 中期著作：政治介入",
           "第3章 最后的著作：可见的与不可见的", "第4章 结语：梅洛－庞蒂的地位", "参考书目"]
CH_NORMS = [norm(c) for c in CHS]
# 带编号页眉行（第 4 章页眉"4 结语：…"式）→ 滤
HEADER_NORMS = ["2中期著作：政治介入", "3最后的著作：可见的与不可见的",
                "4结语：梅洛－庞蒂的地位"]
SECS = ["成长的年代", "知觉的老师：胡塞尔对于梅洛－庞蒂哲学的启示",
        "知觉现象学：早期的意义理论", "梅洛－庞蒂和“介入的”、真正的哲学家",
        "身体政治", "哲学赞：真正的哲学家", "梅洛－庞蒂和萨特：辩证法的冒险",
        "胡塞尔最终目标的完成", "前反思领域", "知觉信念：接触世界必要的和充分的条件",
        "和胡塞尔的最终决裂", "梅洛－庞蒂大胆的分析：交织、交错"]
SEC_NORMS = [norm(s) for s in SECS]

def is_page_num(l):
    return re.fullmatch(r"\d{1,3}", l) is not None

def is_header(l):
    return re.match(r"^On\s*Merle", l) is not None or l == "梅洛－庞蒂"

# ---- 流式扫描（P13 序起）----
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
    # 缓存在 pending_secs，随所属章 flush 时追加（保证 toc 中 section 跟在 chapter 后）
    pending_secs.append({"type": "section", "title": title, "index": idx, "sec": sec_idx, "level": 2})

cur_ch = None        # (title, ch_title)
cur_blocks = []
pending = []
pending_secs = []    # 本章的 section 条目（随章 flush 追加, 保证 toc 顺序正确）
seen_chs = set()
seen_secs = set()

def flush_page():
    global pending
    if pending:
        cur_blocks.append({"type": "text", "value": "".join(pending)})
        pending = []

def flush_ch():
    global cur_ch, cur_blocks, pending_secs
    if cur_ch is not None:
        push_ch(cur_ch, cur_blocks)
        toc.extend(pending_secs)
        pending_secs = []
        cur_ch = None
        cur_blocks = []

for p in range(13, 131):
    lines = [clean(l) for l in doc[p].get_text().split("\n")]
    i = 0
    while i < len(lines):
        l = lines[i]
        i += 1
        if not l:
            continue
        if is_page_num(l) or is_header(l):
            continue
        ln = norm(l)
        # 带编号页眉行（"4 结语：…"式）→ 滤
        if any(ln.startswith(h) for h in HEADER_NORMS):
            continue
        # 章标题（首次=标题, 重复=页眉）
        if ln in CH_NORMS:
            if ln in seen_chs:
                continue
            seen_chs.add(ln)
            flush_page()
            flush_ch()
            cur_ch = CH_FULL[CH_NORMS.index(ln)]
            continue
        # 节标题（独立行精确匹配）
        if ln in SEC_NORMS:
            if ln not in seen_secs:
                seen_secs.add(ln)
                flush_page()
                cur_blocks.append({"type": "text", "value": l})
                add_sec(l, len(cur_blocks) - 1)
            continue
        pending.append(l)
    flush_page()
flush_ch()

assert idx == 6, idx                 # 序 + 4 章 + 参考书目
assert sec_total == 12, sec_total    # 3+4+5 节
assert len(seen_chs) == 6

# ---- 校验 ----
total_chars = 0
for i in sorted(files):
    nc = sum(len(b.get("value", "")) for b in files[i]["content"])
    total_chars += nc
    n_sec = sum(1 for t in toc if t["type"] == "section" and t["index"] == i)
    print(f"  {i} {files[i]['title'][:40]:42s} {nc:7d} 字 sec:{n_sec}")
print(f"总: {len(files)} 章 + {sec_total} section, {total_chars} 字符（PDF 文本层全量）")
old_total = 0
if os.path.isdir(SRC):
    for fn in os.listdir(SRC):
        if fn.endswith(".json") and fn != "meta.json":
            ch = json.load(open(os.path.join(SRC, fn), encoding="utf-8"))
            old_total += sum(len(b.get("value", "")) for b in ch["content"] if b.get("type") == "text")
print(f"旧数据总字数: {old_total}")
for t in toc:
    ind = "  " * t.get("level", 1)
    print(f"{ind}[{t['type']}] {t['title'][:44]}" + (f" sec:{t.get('sec')}" if t["type"] == "section" else ""))
print("首:", files[0]["title"], "| 末:", files[5]["title"])

if "--dry" in sys.argv:
    title_norms = {norm(t["title"]) for t in toc if t["type"] == "chapter"}
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
    "title": old_meta.get("title") or "梅洛-庞蒂",
    "author": old_meta.get("author") or "丹尼尔·托马斯·普里莫兹克",
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
