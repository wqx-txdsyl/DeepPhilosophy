# -*- coding: utf-8 -*-
"""#211 迫害与写作艺术（6bcbc6a5904f）修复
病因（CHKLIST ✗C：'标题 OCR 乱码：第二章拆成"第18迫害与写作艺术章"，i5 裸"第二章"缺标题，"斯宾诺莎"→"斯宾诺尊"'）:
  旧 7 章边界错乱：idx1/idx2 = 第二章被拆两半（标题含页眉'18迫害与写作艺术'乱码）；
  idx5 巨章 69708 字标题'第二章'错——实为第四章后半(p122-151)+第五章前半(p152-203)错合并
  （章节化把 p122 节标题'（二）方式'误认'第二章'）；idx4 仅第四章开头 16222 字；
  idx6 = 第五章后半+附录；'斯宾诺尊'《伸学一政治论'等 OCR 乱码标题。
源: F:/philosophy/西方/列奥·施特劳斯/迫害与写作艺术.pdf（239 页，p7-17 空白）
结构（华夏出版社，施特劳斯著）:
  第一章 导论 p18-32 ｜ 第二章 迫害与写作艺术 p33-47 ｜ 第三章《迷途指津》的文学特性 p48-104
  第四章《卡札尔人书》中的理性之法 p105-151 ｜ 第五章 如何研读斯宾诺莎的《神学一政治论》p152-213
  附录〈迫害与写作艺术〉中的隐微论（科钦撰 唐薇译）p214-238
修复: 全量重建 6 章（idx 连续 0-5，文件名 = toc idx）：
  段落: 每页 x0 众数=正文左缘，x0>左缘+15=段首；页间保守分段；
  页眉过滤（页码/罗马页码/混合页码符号'2!' 'III' '□'/书名行'迫害与写作艺术'/粘连'NN迫害与写作艺术'/'附W'）；
  章首标题块剥离（strip_title_block，标点归一：〈〉＜＞→《》）；附录另剥'科钦(Michael S. Kochin) 撰唐薇译'作者行。
用法: python _xr_211_pxzys_rebuild.py [--dry]
"""
import json, os, re, sys, shutil
import fitz

BID = "6bcbc6a5904f"
PDF = "F:/philosophy/西方/列奥·施特劳斯/迫害与写作艺术.pdf"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

# 章: (idx, 标题, 起始页, 结束页) — PDF 页 0 基
CH = [
    (0, "第一章 导论", 18, 32),
    (1, "第二章 迫害与写作艺术", 33, 47),
    (2, "第三章《迷途指津》的文学特性", 48, 104),
    (3, "第四章《卡札尔人书》中的理性之法", 105, 151),
    (4, "第五章 如何研读斯宾诺莎的《神学一政治论》", 152, 213),
    (5, "附录《迫害与写作艺术》中的隐微论", 214, 238),
]

def norm(s):
    return re.sub(r"\s+", "", s or "")

def norm_t(s):
    """标点归一（角书名号→书名号）用于标题匹配"""
    return norm(s).replace("〈", "《").replace("〉", "》").replace("＜", "《").replace("＞", "》")

def is_page_header(s):
    """页眉/页码行：阿拉伯页码、罗马页码、混合符号页码（'2!' 'III' '□'）、
    书名页眉（'迫害与写作艺术'）、粘连页眉（'18迫害与写作艺术'）、'附W'"""
    n = norm(s)
    if not n:
        return True
    if re.fullmatch(r"\d{1,4}", n):
        return True
    if re.fullmatch(r"[ivxlcdmIVXLCDM]{1,8}", n):
        return True
    if re.fullmatch(r"[0-9IVXLCDM□!.\-]{1,5}", n):
        return True
    if n == "迫害与写作艺术":
        return True
    if re.fullmatch(r"\d{1,3}迫害与写作艺术", n):
        return True
    if n == "附W":
        return True
    return False

r = fitz.open(PDF)

def collect(pg_from, pg_to):
    """页区间 → 段落列表（#191/#183 范式）。"""
    from collections import Counter
    paras, buf = [], []
    for pg in range(pg_from, pg_to + 1):
        lines_x = []
        d = r[pg].get_text("dict")
        for blk in d["blocks"]:
            if blk.get("type") != 0:
                continue
            for ln in blk["lines"]:
                s = "".join(sp["text"] for sp in ln["spans"]).replace("\xad", "").strip()
                if not s:
                    continue
                if is_page_header(s):
                    continue
                lines_x.append((ln["bbox"][0], s))
        if not lines_x:
            continue
        main_x = Counter(round(x) for x, _ in lines_x).most_common(1)[0][0]
        for x0, s in lines_x:
            if x0 > main_x + 15:
                if buf:
                    paras.append("".join(buf))
                    buf = []
            buf.append(s)
        if buf:
            paras.append("".join(buf))
            buf = []
    return paras

def strip_title_block(block, title):
    """章首标题块处理（#183 范式）：短块整删/长块剥标题（标点归一匹配）。"""
    n, t = norm_t(block), norm_t(title)
    if not n:
        return block
    if t not in n[:30] and n[:20] not in t:
        return block
    if len(n) <= 45:
        return None
    rest = n[len(t):] if n.startswith(t) else n.split(t, 1)[1]
    rest = re.sub(r"^[［\[（(]\d+[］\]）)]?", "", rest)  # 含全角方括号 [7]
    return rest or None

# ---- 逐章解析 ----
files = {}
for idx, title, p0, p1 in CH:
    paras = collect(p0, p1)
    if paras:
        stripped = strip_title_block(paras[0], title)
        if stripped is None:
            paras.pop(0)
            # 标题折行残块（如 '〈迫害与写作艺术〉中的隐微论' 单行 ≤30 字 = 标题尾部）→ 一并删
            if paras and len(norm(paras[0])) <= 30 and norm_t(paras[0]).startswith(("〈", "《")):
                paras.pop(0)
            # 标题独立成块被删后，新首块剥正文注号（如 [7]）
            if paras:
                nb = re.sub(r"^[［\[（(]\d+[］\]）)]?", "", norm(paras[0]))
                if nb != norm(paras[0]):
                    paras[0] = nb
        elif stripped != paras[0]:
            paras[0] = stripped
        # 附录作者行剥离（剥净则删块）
        if idx == 5:
            nb = norm(paras[0])
            nb = re.sub(r"^科钦\([^)]*\)撰唐[^，。]{0,3}译", "", nb)
            if nb != paras[0]:
                if nb:
                    paras[0] = nb
                else:
                    paras.pop(0)
    if not paras:
        print(f"⚠ 章{idx} {title!r}: 无内容")
    files[idx] = {"index": idx, "title": title,
                  "content": [{"type": "text", "value": p} for p in paras]}

assert len(files) == 6, len(files)

# ---- 字数对照（vs 源段字数） ----
EXPECT = {0: 11872, 1: 13585, 2: 48333, 3: 42592, 4: 52062, 5: 23188}
total = 0
for idx in range(6):
    f = files[idx]
    nc = sum(len(norm(b["value"])) for b in f["content"])
    total += nc
    first = f["content"][0]["value"][:36] if f["content"] else "(空)"
    last = f["content"][-1]["value"][:24] if f["content"] else ""
    diff = nc - EXPECT[idx]
    print(f"[{idx:2d}] {f['title'][:34]:<36s} {nc:6d}字 (源{EXPECT[idx]:6d} {diff:+d}) {len(f['content']):4d}块 | {first!r} … {last!r}")
print(f"新总净: {total}")
old_total = 0
for i in range(7):
    p = os.path.join(SRC, f"{i}.json")
    if os.path.exists(p):
        ch = json.load(open(p, encoding="utf-8"))
        old_total += sum(len(norm(b.get("value", ""))) for b in ch["content"])
print(f"旧总净: {old_total}  差: {total - old_total:+d}")

# ---- 关键句验证 ----
ch0 = "".join(norm(b["value"]) for b in files[0]["content"])
ch1 = "".join(norm(b["value"]) for b in files[1]["content"])
ch3 = "".join(norm(b["value"]) for b in files[3]["content"])
ch4 = "".join(norm(b["value"]) for b in files[4]["content"])
ch5 = "".join(norm(b["value"]) for b in files[5]["content"])
print("\n验证:",
      "✓导论" if "知识社会学" in ch0 else "✗导论!",
      "✓二章" if "解放心灵" in ch1 else "✗二章!",
      "✓四章含'(二)方式'(p122 误拆点)" if "方式" in ch3 and "隐微" in ch3 else "✗四章!",
      "✓五章" if "斯宾诺莎" in ch4 else "✗五章!",
      "✓附录" if "隐微写作" in ch5 else "✗附录!")
# 旧 idx5 巨章内容归位：p122-151 → 第四章，p152-203 → 第五章
print("误拆归位:",
      "✓四章含'神秘主义'标题讨论" if "神秘主义" in ch3 else "✗!",
      "✓五章含'斯宾诺莎在《神学一政治论》中用了整整一章'" if "整整一章" in ch4 else "✗!")
# 标题乱码清零
print("标题乱码清零:",
      "✓" if not any(("斯宾诺尊" in t["title"] or "伸学" in t["title"] or "迫窖" in t["title"] or "第18" in t["title"]) for t in files.values()) else "✗!")

# ---- toc ----
toc = [{"type": "chapter", "title": files[i]["title"], "index": i, "level": 1} for i in range(6)]
print(f"\ntoc 项: {len(toc)}")
for t in toc:
    print(f"  {t['type']:8s} idx{t['index']} {t['title'][:40]}")

if "--dry" in sys.argv:
    sys.exit(0)

# ---- 写入 ----
if os.path.isdir(SRC):
    suf = "_old_bad"
    i2 = 2
    while os.path.isdir(SRC + suf):
        suf = f"_old_bad{i2}"
        i2 += 1
    os.rename(SRC, SRC + suf)
    print(f"\n备份旧数据 → {os.path.basename(SRC) + suf}")
os.makedirs(SRC)
old_meta = {}
old_bid = SRC + "_old_bad"
if os.path.isdir(old_bid) and os.path.exists(os.path.join(old_bid, "meta.json")):
    old_meta = json.load(open(os.path.join(old_bid, "meta.json"), encoding="utf-8"))
for idx in range(6):
    f = files[idx]
    json.dump({"index": idx, "title": f["title"], "content": f["content"]},
              open(os.path.join(SRC, f"{idx}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
meta = {
    "bookId": old_meta.get("bookId") or BID,
    "title": old_meta.get("title") or "迫害与写作艺术",
    "author": old_meta.get("author") or "列奥·施特劳斯",
    "toc": toc,
    "cover": old_meta.get("cover"),
    "chapterCount": 6,
    "chapterTitles": [files[i]["title"] for i in range(6)],
}
json.dump(meta, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print(f"✓ 写入 {SRC}: 6 章 + meta.json")

shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
print("✓ 同步 DP chapters")

for p in (DETAIL_SRC, DETAIL_DST):
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))
        d["toc"] = toc
        d["chapterCount"] = 6
        d["chapterTitles"] = meta["chapterTitles"]
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
        print(f"✓ book_detail 更新: {p}")

if os.path.exists(BOOKS_JSON):
    bj = json.load(open(BOOKS_JSON, encoding="utf-8"))
    bl = bj if isinstance(bj, list) else bj.get("books", [])
    hit = False
    for b in bl:
        if b.get("id") == BID:
            b["chapterCount"] = 6
            hit = True
    if hit:
        with open(BOOKS_JSON, "w", encoding="utf-8") as f:
            json.dump(bl if isinstance(bj, list) else {**bj, "books": bl}, f,
                      ensure_ascii=False, indent=None)
        print("✓ books.json chapterCount 更新")
    else:
        print("⚠ books.json 未找到该书")
