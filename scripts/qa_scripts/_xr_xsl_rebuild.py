# -*- coding: utf-8 -*-
"""#191 西塞罗（格里马尔）2321fab7e032 修复
病因（CHKLIST ✗D：'第一~八章在，但 i6/i8 两条 OCR 正文句当标题混入需删'，格式错位行）:
  ① detail toc 10 项 = 8 真实章 + idx6 '第二章 中，对话探讨了技术方面的问题…'、
     idx8 '第二章 由对斯多葛主义有精深研究的Q.卢齐利乌…' 两条 OCR 伪章标题
     （源 p102/p131 正文句，OCR 把'第二卷'误认成'第二章'拆成伪章）；
  ② 伪章无文件（6.json 缺失），删伪章时其正文丢失——p102 段属第六章、p131 段属第七章，
     现有 5/7.json 均搜不到 → 内容残缺；
  ③ idx3 标题残缺 '第四章 从“威勒斯案'（源 p53 为 '第四章从“威勒斯案”到执政官'，
     正文首块'到执政官…'即被吞掉的标题尾）；
  ④ 导言（p7-12，源目录第 1 项）未入章，丢失；
  ⑤ 注释（p152-176，〔1〕~〔256〕）被并入第八章尾。
源（F:/philosophy/西方/西塞罗/西塞罗.pdf，177 页，有完整文本层）:
  商务印书馆《我知道什么？》丛书，〔法〕皮埃尔·格里马尔著，董茂永译。
修复: 基于源全量重建 10 章（idx 连续 0-9，文件名 = toc idx）：
  0 导言（p7-12，章首'导言'标题行剔除）
  1 第一章 古老的家族（p13-20）｜2 第二章 神童（p21-36）｜3 第三章 暴力与战争（p37-52）
  4 第四章 从“威勒斯案”到执政官（p53-73，标题补全）
  5 第五章 从执政官到流放（p74-94）｜6 第六章 从流放归来到内战（p95-116）
  7 第七章 从内战到宣布不受法律保护（p117-141）｜8 第八章 历史面前的西塞罗（p142-151）
  9 注释（p152-176，〔1〕~〔256〕，独立章对齐 #183 索引惯例）
  段落: 每页 x0 众数=正文左缘，x0>左缘+15=段首；页间保守分段（跨页拆块）；
  纯数字行=页脚页码剔除；章首标题块剥离（strip_title_block：短块整删/长块剥标题）。
  验证: 第六章含'对话探讨了技术方面的问题'、第七章含'Q.卢齐利乌斯'（伪章正文归位）。
用法: python _xr_xsl_rebuild.py [--dry]
"""
import json, os, re, sys, shutil
import fitz

BID = "2321fab7e032"
PDF = "F:/philosophy/西方/西塞罗/西塞罗.pdf"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

# 章: (idx, 标题, 起始页, 结束页) — 页码 0 基
CH = [
    (0, "导言", 7, 12),
    (1, "第一章 古老的家族", 13, 20),
    (2, "第二章 神童", 21, 36),
    (3, "第三章 暴力与战争", 37, 52),
    (4, "第四章 从“威勒斯案”到执政官", 53, 73),
    (5, "第五章 从执政官到流放", 74, 94),
    (6, "第六章 从流放归来到内战", 95, 116),
    (7, "第七章 从内战到宣布不受法律保护", 117, 141),
    (8, "第八章 历史面前的西塞罗", 142, 151),
    (9, "注释", 152, 176),
]

def norm(s):
    return re.sub(r"\s+", "", s or "")

r = fitz.open(PDF)

def collect(pg_from, pg_to):
    """页区间 → 段落列表（#183 范式）。
    每页 x0 众数=正文左缘，x0 > 左缘+15 = 段首（段首缩进 +20~26pt）；
    页间保守分段（跨页段落拆两块，内容无损）；纯数字行=页脚页码剔除。"""
    from collections import Counter
    paras, buf = [], []
    for pg in range(pg_from, pg_to + 1):
        lines_x = []
        d = r[pg].get_text("dict")
        for blk in d["blocks"]:
            if blk.get("type") != 0:
                continue
            for ln in blk["lines"]:
                s = "".join(sp["text"] for sp in ln["spans"]).strip()
                if not s:
                    continue
                if re.fullmatch(r"\d{1,4}", s):  # 页脚页码（如 '170' '145'）
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
    """章首标题块处理（#183 范式）：
    短块（≤45 字）= 标题行 → 整块删；长块 = 标题与正文同行 → 剥离标题+注号。
    单字短标题（导言'导'？不，'导言'2 字；注释'注'1 字）只认 ≤20 字'标题行'形态。
    不匹配返回原块。"""
    n, t = norm(block), norm(title)
    if not n:
        return block
    if len(t) <= 2:
        if n.startswith(t) and len(n) <= 20:
            return None
        return block
    if t not in n[:30] and n[:20] not in t:
        return block
    if len(n) <= 45:
        return None
    rest = n[len(t):] if n.startswith(t) else n.split(t, 1)[1]
    rest = re.sub(r"^[\[（(]\d+[\]）)]?", "", rest)
    return rest or None

# ---- 逐章解析 ----
files = {}
for idx, title, p0, p1 in CH:
    paras = collect(p0, p1)
    if paras:
        stripped = strip_title_block(paras[0], title)
        if stripped is None:
            paras.pop(0)
            # 标题折行残块（如 '到执政官'/'西塞罗'，≤15 字 = 标题尾部）→ 一并删
            if paras and norm(title).endswith(norm(paras[0])) and len(norm(paras[0])) <= 15:
                paras.pop(0)
        elif stripped != paras[0]:
            paras[0] = stripped
    if not paras:
        print(f"⚠ 章{idx} {title!r}: 无内容")
    files[idx] = {"index": idx, "title": title,
                  "content": [{"type": "text", "value": p} for p in paras]}

assert len(files) == 10, len(files)

# ---- 字数对照 ----
total = 0
for idx in range(10):
    f = files[idx]
    nc = sum(len(norm(b["value"])) for b in f["content"])
    total += nc
    first = f["content"][0]["value"][:36] if f["content"] else "(空)"
    last = f["content"][-1]["value"][:24] if f["content"] else ""
    print(f"[{idx:2d}] {f['title'][:30]:<32s} {nc:6d}字 {len(f['content']):4d}块 | {first!r} … {last!r}")
print(f"新总净: {total}")
old_total = 0
for i in [0, 1, 2, 3, 4, 5, 7, 8]:
    p = os.path.join(SRC, f"{i}.json")
    if os.path.exists(p):
        ch = json.load(open(p, encoding="utf-8"))
        old_total += sum(len(norm(b.get("value", ""))) for b in ch["content"])
print(f"旧总净: {old_total}  差: {total - old_total:+d}（+导言/伪章正文归位）")

# ---- 伪章正文归位验证 ----
ch6 = "".join(norm(b["value"]) for b in files[6]["content"])
ch7 = "".join(norm(b["value"]) for b in files[7]["content"])
print("\n伪章正文归位:",
      "✓第六章" if "对话探讨了技术方面的问题" in ch6 else "✗第六章缺!",
      "✓第七章" if "卢齐利乌斯" in ch7 else "✗第七章缺!")
# idx4 标题补全验证
print("第四章标题:", files[4]["title"])

# ---- toc ----
toc = [{"type": "chapter", "title": files[i]["title"], "index": i, "level": 1} for i in range(10)]
print(f"\ntoc 项: {len(toc)}")
for t in toc:
    print(f"  {t['type']:8s} idx{t['index']} {t['title'][:36]}")

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
for idx in range(10):
    f = files[idx]
    json.dump({"index": idx, "title": f["title"], "content": f["content"]},
              open(os.path.join(SRC, f"{idx}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
meta = {
    "bookId": old_meta.get("bookId") or BID,
    "title": old_meta.get("title") or "西塞罗",
    "author": old_meta.get("author") or "皮埃尔·格里马尔",
    "toc": toc,
    "cover": old_meta.get("cover"),
    "chapterCount": 10,
    "chapterTitles": [files[i]["title"] for i in range(10)],
}
json.dump(meta, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print(f"✓ 写入 {SRC}: 10 章 + meta.json")

shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
print("✓ 同步 DP chapters")

for p in (DETAIL_SRC, DETAIL_DST):
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))
        d["toc"] = toc
        d["chapterCount"] = 10
        d["chapterTitles"] = meta["chapterTitles"]
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
        print(f"✓ book_detail 更新: {p}")

if os.path.exists(BOOKS_JSON):
    bj = json.load(open(BOOKS_JSON, encoding="utf-8"))
    bl = bj if isinstance(bj, list) else bj.get("books", [])
    hit = False
    for b in bl:
        if b.get("id") == BID:
            b["chapterCount"] = 10
            hit = True
    if hit:
        with open(BOOKS_JSON, "w", encoding="utf-8") as f:
            json.dump(bl if isinstance(bj, list) else {**bj, "books": bl}, f,
                      ensure_ascii=False, indent=None)
        print("✓ books.json chapterCount 更新")
    else:
        print("⚠ books.json 未找到该书")
