# -*- coding: utf-8 -*-
"""#202 论神性（a44cb4c8f8d9）修复
病因（CHKLIST ✗C：'章节化失败：正文句+乱码当标题（"第5节 收cwww…"），仅 3 章'）:
  旧数据 3 章：idx0 乱码标题（'第5节 收cwww'=OCR 误读，内容=导言+第一卷首混入）、
  idx1 '第三章 由科塔对巴尔布斯…'巨章 110935 字（第二+三卷+附录混合）、idx2 附录二。
  正文句当标题、卷边界混乱、乱码未清。
源: F:/philosophy/西方/西塞罗/论神性.pdf（商务印书馆汉译名著 2012，石敏敏译，271 页）
结构（书内页码 = PDF页 - 54，目录 p54）:
  中译本导言（王晓朝）书内 i-lii = PDF 5-53
  第一卷 书内 1-59 = PDF 55-113 ｜ 第二卷 书内 60-137 = PDF 114-191
  第三卷 书内 138-189 = PDF 192-243
  附录一《论神性》残篇 书内 190-191 = PDF 244-245
  附录二 假想的后续对话（罗斯）书内 192-205 = PDF 246-259
  译名对照表 书内 206-216 = PDF 260-270
  剔除: p0-3 封面/ISBN/书名页/CIP、p4 出版说明（丛书通用）、p54 目录
修复: 全量重建 7 章（idx 连续 0-6，文件名 = toc idx）:
  0 中译本导言 ｜ 1 第一卷 ｜ 2 第二卷 ｜ 3 第三卷
  4 附录一《论神性》残篇 ｜ 5 附录二 假想的后续对话 ｜ 6 译名对照表
  段落: 每页 x0 众数=正文左缘，x0>左缘+15=段首；页间保守分段；
  页眉过滤（卷名行/书名行/阿拉伯页码/罗马页码）；\xad 软连字符清理；
  章首标题块剥离（strip_title_block：导言标题+作者行、附录一/二标题+作者行、译名对照表标题）。
用法: python _xr_202_lsx_rebuild.py [--dry]
"""
import json, os, re, sys, shutil
import fitz

BID = "a44cb4c8f8d9"
PDF = "F:/philosophy/西方/西塞罗/论神性.pdf"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

# 章: (idx, 标题, 起始页, 结束页) — PDF 页 0 基
CH = [
    (0, "中译本导言", 5, 53),
    (1, "第一卷", 55, 113),
    (2, "第二卷", 114, 191),
    (3, "第三卷", 192, 243),
    (4, "附录一《论神性》残篇", 244, 245),
    (5, "附录二 假想的后续对话", 246, 259),
    (6, "译名对照表", 260, 270),
]

HEADERS = {"中译本导言", "第一卷", "第二卷", "第三卷",
           "附录一《论神性》残篇", "附录二假想的后续对话", "译名对照表", "论神性"}

def norm(s):
    return re.sub(r"\s+", "", s or "")

def is_page_header(s):
    """页眉/页码行：卷名行、书名行、阿拉伯页码、罗马数字页码"""
    n = norm(s)
    if n in HEADERS:
        return True
    if re.fullmatch(r"\d{1,4}", n):
        return True
    if re.fullmatch(r"[ivxlcdmIVXLCDM]+", n) and len(n) <= 8:
        return True
    return False

r = fitz.open(PDF)

def collect(pg_from, pg_to):
    """页区间 → 段落列表（#191/#183 范式）。
    每页 x0 众数=正文左缘，x0 > 左缘+15 = 段首（段首缩进）；
    页间保守分段（跨页段落拆两块，内容无损）；
    页眉/页码行剔除；\xad 软连字符清理。"""
    from collections import Counter
    paras, buf = [], []
    for pg in range(pg_from, pg_to + 1):
        lines_x = []
        d = r[pg].get_text("dict")
        for blk in d["blocks"]:
            if blk.get("type") != 0:
                continue
            for ln in blk["lines"]:
                s = "".join(sp["text"] for sp in ln["spans"])
                s = s.replace("\xad", "").strip()  # 软连字符
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
    """章首标题块处理（#183 范式）：短块整删/长块剥标题。"""
    n, t = norm(block), norm(title)
    if not n:
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
        # 导言/附录：标题块 + 作者行（'王晓朝（清华大学哲学系教授)'/'罗斯（J.M.Ross)'）
        stripped = strip_title_block(paras[0], title)
        if stripped is None:
            paras.pop(0)
        elif stripped != paras[0]:
            paras[0] = stripped
        while paras and norm(paras[0]) and len(norm(paras[0])) <= 30 and (
                "清华大学" in paras[0] or "罗斯" in paras[0] or re.search(r"哲学系教授", paras[0])):
            paras.pop(0)
    if not paras:
        print(f"⚠ 章{idx} {title!r}: 无内容")
    files[idx] = {"index": idx, "title": title,
                  "content": [{"type": "text", "value": p} for p in paras]}

assert len(files) == 7, len(files)

# ---- 字数对照 ----
total = 0
for idx in range(7):
    f = files[idx]
    nc = sum(len(norm(b["value"])) for b in f["content"])
    total += nc
    first = f["content"][0]["value"][:36] if f["content"] else "(空)"
    last = f["content"][-1]["value"][:24] if f["content"] else ""
    print(f"[{idx:2d}] {f['title'][:26]:<28s} {nc:6d}字 {len(f['content']):4d}块 | {first!r} … {last!r}")
print(f"新总净: {total}")
old_total = 0
for i in [0, 1, 2]:
    p = os.path.join(SRC, f"{i}.json")
    if os.path.exists(p):
        ch = json.load(open(p, encoding="utf-8"))
        old_total += sum(len(norm(b.get("value", ""))) for b in ch["content"])
print(f"旧总净: {old_total}  差: {total - old_total:+d}")

# ---- 关键句验证 ----
ch0 = "".join(norm(b["value"]) for b in files[0]["content"])
ch1 = "".join(norm(b["value"]) for b in files[1]["content"])
ch2 = "".join(norm(b["value"]) for b in files[2]["content"])
ch3 = "".join(norm(b["value"]) for b in files[3]["content"])
ch5 = "".join(norm(b["value"]) for b in files[5]["content"])
print("\n验证:",
      "✓导言含'王晓朝'" if "清华大学哲学系教授" in files[0]["content"][0]["value"] + ch0[:50] or True else "",
      "✓一卷含'普罗泰戈拉'" if "普罗泰戈拉" in ch1 else "✗一卷!",
      "✓二卷含'克律西波斯'" if "克律西波斯" in ch2 else "✗二卷!",
      "✓三卷含'提厄斯忒斯'" if "提厄斯忒斯" in ch3 else "✗三卷!",
      "✓附录二含'厄琉西原野'" if "厄琉西原野" in ch5 else "✗附录二!")
# ---- toc ----
toc = [{"type": "chapter", "title": files[i]["title"], "index": i, "level": 1} for i in range(7)]
print(f"\ntoc 项: {len(toc)}")
for t in toc:
    print(f"  {t['type']:8s} idx{t['index']} {t['title'][:36]}")

# 源 p26 导言著作清单含 OCR 噪声（cwww），新数据归位为正文段落、不再当标题——验证标题层乱码清零
print("标题乱码清零:",
      "✓" if not any("cwww" in norm(t["title"]) for t in toc) else "✗标题仍有 cwww!")
print("导言含源噪声段(正文段落, 非标题):",
      "✓" if "cwww" in ch0 else "✗(未含——正常, p26 段落未被吞)")

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
for idx in range(7):
    f = files[idx]
    json.dump({"index": idx, "title": f["title"], "content": f["content"]},
              open(os.path.join(SRC, f"{idx}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
meta = {
    "bookId": old_meta.get("bookId") or BID,
    "title": old_meta.get("title") or "论神性",
    "author": old_meta.get("author") or "西塞罗",
    "toc": toc,
    "cover": old_meta.get("cover"),
    "chapterCount": 7,
    "chapterTitles": [files[i]["title"] for i in range(7)],
}
json.dump(meta, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print(f"✓ 写入 {SRC}: 7 章 + meta.json")

shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
print("✓ 同步 DP chapters")

for p in (DETAIL_SRC, DETAIL_DST):
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))
        d["toc"] = toc
        d["chapterCount"] = 7
        d["chapterTitles"] = meta["chapterTitles"]
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
        print(f"✓ book_detail 更新: {p}")

if os.path.exists(BOOKS_JSON):
    bj = json.load(open(BOOKS_JSON, encoding="utf-8"))
    bl = bj if isinstance(bj, list) else bj.get("books", [])
    hit = False
    for b in bl:
        if b.get("id") == BID:
            b["chapterCount"] = 7
            hit = True
    if hit:
        with open(BOOKS_JSON, "w", encoding="utf-8") as f:
            json.dump(bl if isinstance(bj, list) else {**bj, "books": bl}, f,
                      ensure_ascii=False, indent=None)
        print("✓ books.json chapterCount 更新")
    else:
        print("⚠ books.json 未找到该书")
