# -*- coding: utf-8 -*-
"""#183 自然辩证法（恩格斯）aa21ac425e87 修复
病因（CHKLIST ✗C 章节化失败：标题为正文首句+乱码，编号乱）:
  旧 15 章 277714 字，章标题全部错乱（'第4章 ）'、'第61节 节）中可以看到…'，
  标题 = 正文首句 + 乱编号；巨章 63110 字与碎章 308 字并存。
源（F:/philosophy/西方/弗里德里希·恩格斯/自然辩证法.pdf，406 页）:
  **有完整文本层**（pymupdf 提取，全书 295767 字符，无页眉页码），
  书签 47 条（lv1 部 / lv2 章 / lv3 节，锚点页个别偏差 ≤1 页）。
修复:
  基于源文本层全量重建 36 章 + 7 part（#144 part 模式，part 不入文件）：
  0 编者引言｜1 ［1878年的计划］（计划草案部，正文+注释合并）
  ｜历史导论部：2 ［历史］ 3 ［导言］ 4 ［札记和片断］
  ｜黑格尔部：5 《反杜林论》旧序。论辩证法 6 神灵世界中的自然研究 7 ［札记和片断］
  ｜辩证法作为科学部：8 辩证法 9 ［札记和片断］ 10 ［规律和范畴］ 11 ［认识］
  ｜12 ［物质的运动形式以及各门科学的联系］（独立部级章）
  ｜各门科学的辩证内容部：13 ［1880年的计划］ 14 运动的基本形式 15 ［札记和片断］
  16 运动的量度——功 17 ［札记和片断］ 18 ［数学］ 19 ［力学和天文学］
  20 热（书签"物理学"父标题锚点=热标题页，物理学并入热，剔除'热 [157]'标题行）
  21 电（剔除'电 (1) [159]'标题行） 22 ［札记和片断］ 23 ［化学］ 24 ［生物学］
  ｜自然界和社会部：25 劳动在从猿到人的转变中的作用 26 ［四束手稿目录］
  ｜附录 恩格斯有关书信选编部：27 致马克思（1858年7月14日）28 致马克思（1873年
  5月30日）29 致马克思（1874年9月21日）30 致彼得·拉甫罗维奇·拉甫罗夫（1875年
  11月12—17日）31 致马克思（1876年5月28日）——5 封信按正文标题行精确切分
  ｜32 人名索引 33 《自然辩证法》细目（按手稿写作时间编排）
  34 《自然辩证法》细目（按手稿内容编排）35 《自然辩证法》四束手稿内容索引
  （版权页 p405 空页不建章）。
  块级：章区间内逐页行合并（页间无空行=同段跨页合并），空行分段；
  章首标题行剔除（norm==标题 或 标题 in 首行<30字；20/21 特判）。
用法: python _xr_zrbzfx_rebuild.py [--dry]
"""
import json, os, re, sys, shutil
import fitz

BID = "aa21ac425e87"
PDF = "F:/philosophy/西方/弗里德里希·恩格斯/自然辩证法.pdf"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

# 章: (标题, 起始页, 结束页) — 页码 0 基（PDF p1 = 索引 0）
CH = [
    (0, "编者引言", 1, 7),
    (1, "［1878年的计划］", 8, 12),
    (2, "［历史］", 13, 16),
    (3, "［导言］", 17, 35),
    (4, "［札记和片断］", 36, 46),
    (5, "《反杜林论》旧序。论辩证法", 47, 56),
    (6, "神灵世界中的自然研究", 57, 68),
    (7, "［札记和片断］", 69, 84),
    (8, "辩证法", 85, 92),
    (9, "［札记和片断］", 93, 93),
    (10, "［规律和范畴］", 94, 110),
    (11, "［认识］", 111, 129),
    (12, "［物质的运动形式以及各门科学的联系］", 130, 138),
    (13, "［1880年的计划］", 139, 140),
    (14, "运动的基本形式", 141, 156),
    (15, "［札记和片断］", 157, 165),
    (16, "运动的量度——功", 166, 180),
    (17, "［札记和片断］", 181, 186),
    (18, "［数学］", 187, 204),
    (19, "［力学和天文学］", 205, 215),
    (20, "热", 216, 219),  # p220 是电篇注释页（"23日给马克思的信…"），归电章
    (21, "电", 220, 270),  # 首块为电篇注释，随后'电 (1) [159]'标题行剔除
    (22, "［札记和片断］", 271, 280),
    (23, "［化学］", 281, 282),
    (24, "［生物学］", 283, 301),
    (25, "劳动在从猿到人的转变中的作用", 302, 315),
    (26, "［四束手稿目录］", 316, 317),
    (27, "致马克思（1858年7月14日）", 320, 321),
    (28, "致马克思（1873年5月30日）", 322, 323),
    (29, "致马克思（1874年9月21日）", 324, 324),
    (30, "致彼得·拉甫罗维奇·拉甫罗夫（1875年11月12—17日）", 325, 328),
    (31, "致马克思（1876年5月28日）", 329, 329),
    (32, "人名索引", 330, 359),  # p360 起是《细目（按手稿写作时间编排）》标题页
    (33, "《自然辩证法》细目（按手稿写作时间编排）", 360, 374),  # 书签锚 p361 但标题在 p360
    (34, "《自然辩证法》细目（按手稿内容编排）", 375, 389),  # 书签锚 p376 但标题页在 p375
    (35, "《自然辩证法》四束手稿内容索引", 390, 403),  # p404 版权页排除
]
# part: (其下首章 idx, 标题)
PARTS = [
    (1, "［计划草案］"),
    (2, "［历史导论］"),
    (5, "［黑格尔以来的理论发展进程。哲学和自然科学］"),
    (8, "［辩证法作为科学］"),
    (13, "［各门科学的辩证内容］"),
    (25, "［自然界和社会］"),
    (27, "附录 恩格斯有关书信选编"),
]

def norm(s):
    return re.sub(r"\s+", "", s or "")

r = fitz.open(PDF)

def collect(pg_from, pg_to):
    """页区间 → 段落列表。
    正文行 x0 相同（72），段首行缩进（x0=102，+30pt）；段间无空行。
    每页取 x0 众数为正文左缘，x0 > 左缘+15 的缩进行 = 段首；
    页间保守分段（跨页段落拆两块，内容无损）。"""
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
                if s:
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
    """章首标题块处理：标题在前 30 字内。
    短块（≤45 字）= 标题行 → 整块删（返回 None）；
    长块 = 标题与正文同行（章首页）→ 剥离标题 + [N]/(N) 注号，返回剩余正文。
    不匹配返回原块。单字短标题（如'热''电'）只认"标题行+注号"形态（≤20 字，
    以标题开头），避免误删含该字的正文段。"""
    n, t = norm(block), norm(title)
    if not n:
        return block
    if len(t) <= 2:
        if n.startswith(t) and len(n) <= 20:
            return None
        return block
    if t not in n[:30] and n[:20] not in t:  # n[:20] in t = 标题行行尾拆分的残块
        return block
    if len(n) <= 45:
        return None
    rest = n[len(t):] if n.startswith(t) else n.split(t, 1)[1]
    rest = re.sub(r"^[\[（(]\d+[\]）)]?", "", rest)  # 注号 [1] / (1)
    return rest or None

# ---- 逐章解析 ----
files = {}
for idx, title, p0, p1 in CH:
    paras = collect(p0, p1)
    # 章首标题块剔除/剥离（28 章 1873 信标题含 [211] 注号，特判）
    if paras:
        first = paras[0]
        if idx == 28 and "1873年5月30日" in norm(first)[:30]:
            nf = norm(first)
            m = re.match(r"^致马克思[\[（(]\d+[\]）)]?（1873年5月30日）", nf)
            if m:
                rest = nf[m.end():]
                if rest:
                    paras[0] = rest
                else:
                    paras.pop(0)
        else:
            stripped = strip_title_block(first, title)
            if stripped is None:
                paras.pop(0)
                # 标题行行尾拆分的残块（如'排） (1)'，≤12 字含注号）→ 一并删
                if paras and re.match(r"^.{0,10}[)）](?:\s*\(\d+\))?$", paras[0]):
                    paras.pop(0)
            elif stripped != first:
                paras[0] = stripped
    if not paras:
        print(f"⚠ 章{idx} {title!r}: 无内容")
    files[idx] = {"index": idx, "title": title, "content": [{"type": "text", "value": p} for p in paras]}

assert len(files) == 36, len(files)

# ---- 字数对照 ----
total = 0
for idx in range(36):
    f = files[idx]
    nc = sum(len(norm(b["value"])) for b in f["content"])
    total += nc
    first = f["content"][0]["value"][:32] if f["content"] else "(空)"
    last = f["content"][-1]["value"][:24] if f["content"] else ""
    print(f"[{idx:2d}] {f['title'][:34]:<36s} {nc:6d}字 {len(f['content']):4d}块 | {first!r} … {last!r}")
print(f"新总净: {total}")
old_total = 0
for i in range(15):
    p = os.path.join(SRC, f"{i}.json")
    if os.path.exists(p):
        ch = json.load(open(p, encoding="utf-8"))
        old_total += sum(len(norm(b.get("value", ""))) for b in ch["content"])
print(f"旧总净: {old_total}  差: {total - old_total:+d}（+编者引言/索引/细目/书信精切）")

# ---- toc ----
toc = []
pit = iter(PARTS)
next_part = next(pit, None)
for idx in range(36):
    if next_part and idx == next_part[0]:
        toc.append({"type": "part", "title": next_part[1], "index": idx, "level": 0})
        next_part = next(pit, None)
    toc.append({"type": "chapter", "title": files[idx]["title"], "index": idx, "level": 1})
print(f"\ntoc 项: {len(toc)}（36 章 + {len(PARTS)} part）")
for t in toc:
    print(f"  {t['type']:8s} idx{t['index']:2d} {t['title'][:40]}")

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
for idx in range(36):
    f = files[idx]
    json.dump({"index": idx, "title": f["title"], "content": f["content"]},
              open(os.path.join(SRC, f"{idx}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
meta = {
    "bookId": old_meta.get("bookId") or BID,
    "title": old_meta.get("title") or "自然辩证法",
    "author": old_meta.get("author") or "弗里德里希·恩格斯",
    "toc": toc,
    "cover": old_meta.get("cover"),
    "chapterCount": 36,
    "chapterTitles": [files[i]["title"] for i in range(36)],
}
json.dump(meta, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print(f"✓ 写入 {SRC}: 36 章 + meta.json")

shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
print("✓ 同步 DP chapters")

for p in (DETAIL_SRC, DETAIL_DST):
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))
        d["toc"] = toc
        d["chapterCount"] = 36
        d["chapterTitles"] = meta["chapterTitles"]
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
        print(f"✓ book_detail 更新: {p}")

if os.path.exists(BOOKS_JSON):
    bj = json.load(open(BOOKS_JSON, encoding="utf-8"))
    bl = bj if isinstance(bj, list) else bj.get("books", [])
    hit = False
    for b in bl:
        if b.get("id") == BID:
            b["chapterCount"] = 36
            hit = True
    if hit:
        with open(BOOKS_JSON, "w", encoding="utf-8") as f:
            json.dump(bl if isinstance(bj, list) else {**bj, "books": bl}, f,
                      ensure_ascii=False, indent=None)
        print("✓ books.json chapterCount 更新")
    else:
        print("⚠ books.json 未找到该书")
