# -*- coding: utf-8 -*-
"""#未入清单 现象学的观念（e2a4c4f78c40）补录修复
病因: OCR 完成的 20 本未入清单书之一。旧 28 章 toc 是字符串数组（混杂异书内容：
  '第一章绪论5'/'一、研究内容'/'第二章，员工建言行为…' + 胡塞尔内容），
  章节化完全错误：异书夹页被建章，第一讲至第五讲正文几乎全丢（旧 69763 字）。
源: F:/philosophy/西方/埃德蒙德·胡塞尔/现象学的观念.pdf（154 页扫描版，
  倪梁康译，商务印书馆'胡塞尔文集'，checkpoint OCR 154 页 fail 11：
  18/42/54/68/80/82/94/106/108/116/118；书内页码 = PDF页 - 16）
结构（目录 p14-16 确认）:
  p0-3 封面/CIP/德文原书页（书级页） ｜ p4-5 《胡塞尔文集》总序（目录无，跳过）
  p6-12 编者引论（书内 VII-XII，p6 行1='VII' 罗马页码） ｜ p13 关于第二版（书内 XII）
  p14-16 目录 ｜ p17 书名页 ｜ p18 fail 空白（书名页背面）
  p19 讲座的思路（书内 11，章前+正文起） ｜ p20-27 ⚠异书夹页（博士论文
    '中国情境下的员工建言行为影响因素研究'页眉'第一章绪论4-11'连续 8 页——
    PDF 源缺陷插入/替换，跳过不建章；p19 尾与 p28 首正文衔接断裂，疑缺 1+ 页）
  p28-40 讲座的思路续（书内 12-24）
  p41 第一讲章前页（书内 25，跳过） ｜ p42 fail 空白（书内 26） ｜ p43-52 第一讲正文（书内 27-36）
  p53 第二讲章前（37） ｜ p54 fail 空白（38） ｜ p55-66 第二讲正文（书内 39-50）
  p67 第三讲章前（51） ｜ p68 fail 空白（52） ｜ p69-79 第三讲正文（书内 53-63） ｜ p80 fail 缺尾页（书内 64）
  p81 第四讲章前（65） ｜ p82 fail 空白（66） ｜ p83-92 第四讲正文（书内 67-76）
  p93 第五讲章前（77） ｜ p94 fail 空白（78） ｜ p95-105 第五讲正文（书内 79-89） ｜ p106 fail 缺尾页（书内 90）
  p107 附录章前（91） ｜ p108 fail 空白（92） ｜ p109-111 附录一（书内 93-95，p109 章前+正文同页）
  p112 附录二（书内 96，章前+正文同页，行0='81' 噪声） ｜ p113 附录二续（书内 97）
  p114-115 附录三（书内 98-99，章前+正文同页） ｜ p116 fail 缺尾页（书内 100）
  p117 文章的考证性补充章前（101） ｜ p118 fail 空白（102） ｜ p119-120 关于文章的构成（书内 103-104）
  p121-129 关于文章的考证性注释（书内 105-113） ｜ p130 人名索引（书内 114）
  p131-149 第一版译者引言（书内 115-133） ｜ p150-152 第二版译者后记（书内 134-136）
  ⚠ 第三版译者后记（目录 138）整篇缺失（PDF 缺页，p153 版权页直接结尾）
页眉系统: 奇数页章名页眉（'编者引论N'/'讲座的思路N'/'第X讲N'/'附录XN'/'第一版译者引言N'等，N 可无）
  偶数页粘连页眉（'N现象学的观念'，书内页码+书名）；章前页独立标题行（'第一讲'/'附录'/'附录二'等）；
  个别页眉/页脚裸数字行（'81'/'79'/'87'）；p13 罗马页码页眉（'XII'）
修复: 全量重建 16 章 + part 附录（idx=8）:
  页眉过滤: 奇数页章名页眉 / 偶数页粘连页眉 / 罗马页码页眉剥首行；
  章前标题独立行页内任意位置剔除（STRIP_TITLES）；
  页眉剥后首行裸数字剔除（'^\d{1,4}$'）；
  段落: 每页过滤后行拼接为一段（OCR 书范式）；
  fail 页缺内容如实保留（段数=页数-缺页），异书夹页/第三版译者后记缺失不补不编造。
用法: python _xr_e2a4c4f78c40_xxgdgn_rebuild.py [--dry]
"""
import json, os, re, sys, shutil

BID = "e2a4c4f78c40"
CKPT = r"f:\program\Python\PhiAgent\backend\data\dp_pdf_import_ckpt.json"
SAFE = "西方_埃德蒙德_胡塞尔_现象学的观念.pdf"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

def norm(s):
    return re.sub(r"\s+", "", s or "")

# 17 章: (idx, 标题, 起始页, 结束页) — PDF 页
CH = [
    (0, "编者引论", 6, 12),
    (1, "关于第二版", 13, 13),
    (2, "讲座的思路", 19, 40),      # p20-27 异书夹页跳过
    (3, "第一讲", 43, 52),
    (4, "第二讲", 55, 66),
    (5, "第三讲", 69, 79),          # p80 fail 缺尾
    (6, "第四讲", 83, 92),
    (7, "第五讲", 95, 105),         # p106 fail 缺尾
    (9, "附录一", 109, 111),
    (10, "附录二", 112, 113),
    (11, "附录三", 114, 116),       # p116 fail 缺尾
    (12, "关于文章的构成", 119, 120),
    (13, "关于文章的考证性注释", 121, 129),
    (14, "人名索引", 130, 130),
    (15, "第一版译者引言", 131, 149),
    (16, "第二版译者后记", 150, 152),
]
PART_APPENDIX = 8                    # part 附录（level0）
SKIP_PAGES = set(range(20, 28))      # ⚠ 异书夹页（博士论文页眉'第一章绪论4-11'）
# 章前标题独立行（页内任意位置精确匹配剔除）
STRIP_TITLES = {
    "讲座的思路", "第一讲", "第二讲", "第三讲", "第四讲", "第五讲",
    "附录", "附录一", "附录二", "附录三", "文章的考证性补充",
    "关于文章的构成", "关于文章的考证性注释", "人名索引",
    "第一版译者引言", "第二版译者后记", "编者引论", "关于第二版",
}
# 奇数页章名页眉（带/不带数字）
HEADER_RE = re.compile(r"^(编者引论|讲座的思路|第一讲|第二讲|第三讲|第四讲|第五讲|附录一|附录二|附录三|关于文章的构成|关于文章的考证性注释|人名索引|第一版译者引言|第二版译者后记)\d*$")
# 偶数页粘连页眉: 'N现象学的观念'（书内页码+书名）
EVEN_HEADER_RE = re.compile(r"^\d{1,4}现象学的观念$")
# 罗马页码页眉（p13 'XII'）
ROMAN_HEADER_RE = re.compile(r"^[IVXLCDM]{1,4}$")
# 页眉剥后首行裸数字页码（'81'/'79'/'87'）
BARE_NUM_RE = re.compile(r"^\d{1,4}$")

ckpt = json.load(open(CKPT, encoding="utf-8"))
pages = ckpt["ocr"][SAFE]
npages = {int(k): v for k, v in pages.items() if v and v != "__FAILED__"}
fails = sorted([int(k) for k, v in pages.items() if v == "__FAILED__"])
print(f"OCR 页: {min(npages)}-{max(npages)} 共 {len(npages)} 页, fail {len(fails)} 页: {fails}")

def page_lines(i):
    """页 → 过滤页眉/标题/裸数字后的行"""
    t = npages.get(i, "")
    if not t:
        return []
    ls = [ln.strip() for ln in t.split("\n") if ln.strip()]
    if not ls:
        return []
    # 页眉/罗马页码/裸数字逐层剥首行（章前页后可能连剥多行，如 p6 '编者引论'+'VII'）
    while ls and (HEADER_RE.match(ls[0]) or EVEN_HEADER_RE.match(ls[0])
                  or ROMAN_HEADER_RE.match(ls[0]) or BARE_NUM_RE.fullmatch(ls[0])):
        ls.pop(0)
    ls = [l for l in ls if l not in STRIP_TITLES]
    return ls

# ---- 逐章解析（页级段落范式） ----
files = {}
for idx, title, p0, p1 in CH:
    paras = []
    for i in range(p0, p1 + 1):
        if i in SKIP_PAGES:
            continue
        lss = page_lines(i)
        if lss:
            paras.append("".join(lss))
    if not paras:
        print(f"⚠ 章{idx} {title!r}: 无内容")
    files[idx] = {"index": idx, "title": title,
                  "content": [{"type": "text", "value": p} for p in paras]}
    nc = sum(len(norm(p)) for p in paras)
    first = paras[0][:28] if paras else "(空)"
    last = paras[-1][:20] if paras else ""
    print(f"[{idx:2d}] {title[:22]:<24s} {nc:6d}字 {len(paras):3d}段 | {first!r} … {last!r}")
assert len(files) == 16   # idx 0-7 + 9-16（8 = part 附录占位）

# ---- 验证 ----
total = 0
for idx in CH:
    total += sum(len(norm(b["value"])) for b in files[idx[0]]["content"])
print(f"\n新总净: {total}")
old_total = 0
for i in range(28):
    p = os.path.join(SRC, f"{i}.json")
    if os.path.exists(p):
        ch = json.load(open(p, encoding="utf-8"))
        old_total += sum(len(norm(b.get("value", ""))) for b in ch["content"])
print(f"旧总净: {old_total}  差: {total - old_total:+d}")

all_text = "".join(norm(b["value"]) for idx, _, _, _ in CH for b in files[idx]["content"])
# 页眉清零：粘连页眉（'N现象学的观念'）不得残留；正文引用书名《现象学的观念》不带数字前缀
print("页眉清零:", "✓" if not re.search(r"\d现象学的观念", all_text) else "✗")
# 章前标题清零：无独立'第X讲'/'附录'等段
pure_titles = [norm(b["value"]) for idx, _, _, _ in CH for b in files[idx]["content"]
               if norm(b["value"]) in STRIP_TITLES]
print("章标题清零:", "✓" if not pure_titles else f"✗ {pure_titles[:5]}")
# 异书页清零：'建言' 不得出现
print("异书页清零:", "✓" if "建言" not in all_text else "✗ 异书内容残留!")
# 关键内容验证
ch = {idx: "".join(norm(b["value"]) for b in files[idx]["content"]) for idx, _, _, _ in CH}
checks = [
    (0, "编者引论", "哥廷根"),
    (1, "关于第二版", "比梅尔"),
    (2, "讲座的思路", "漠不关心"),
    (3, "第一讲", "我在以往的讲座中曾区分自然科"),
    (4, "第二讲", "认识批判的开端"),
    (5, "第三讲", "根据以上阐述"),
    (6, "第四讲", "直接直观可指明"),
    (7, "第五讲", "思维的明见性"),
    (9, "附录一", "团体和文化事业"),
    (10, "附录二", "修改和补充的尝试"),
    (11, "附录三", "认识与超越之物的关系"),
    (12, "构成", "鲁汶"),
    (13, "考证性注释", "铅笔做的附加补充"),
    (14, "人名索引", "笛卡尔"),
    (15, "译者引言", "犹太血统"),
    (16, "译者后记", "屈指算来"),
]
print("验证:", "  ".join(f"{'✓'+t if kw in ch[i] else '✗'+t+'!'}" for i, t, kw in checks))

# ---- toc（16 章 + part 附录） ----
toc = ([{"type": "chapter", "title": files[i]["title"], "index": i, "level": 1}
        for i in range(0, 8)]
       + [{"type": "part", "title": "附录", "index": PART_APPENDIX, "level": 0}]
       + [{"type": "chapter", "title": files[i]["title"], "index": i, "level": 1}
          for i in range(9, 17)])
print(f"\ntoc 项: {len(toc)}")
for t in toc[:5] + toc[8:11] + toc[-3:]:
    print(f"  {t['type']:8s} level{t.get('level')} idx{t['index']} {t['title'][:34]}")

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
for idx, title, p0, p1 in CH:
    f = files[idx]
    json.dump({"index": idx, "title": f["title"], "content": f["content"]},
              open(os.path.join(SRC, f"{idx}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
meta = {
    "bookId": old_meta.get("bookId") or BID,
    "title": old_meta.get("title") or "现象学的观念",
    "author": old_meta.get("author") or "胡塞尔",
    "toc": toc,
    "cover": old_meta.get("cover"),
    "chapterCount": 16,
    "chapterTitles": [files[idx]["title"] for idx, _, _, _ in CH],
}
json.dump(meta, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print(f"✓ 写入 {SRC}: 16 章 + meta.json")

shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
print("✓ 同步 DP chapters")

for p in (DETAIL_SRC, DETAIL_DST):
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))
        d["toc"] = toc
        d["chapterCount"] = 16
        d["chapterTitles"] = meta["chapterTitles"]
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
        print(f"✓ book_detail 更新: {p}")

if os.path.exists(BOOKS_JSON):
    bj = json.load(open(BOOKS_JSON, encoding="utf-8"))
    bl = bj if isinstance(bj, list) else bj.get("books", [])
    hit = False
    for b in bl:
        if b.get("id") == BID:
            b["chapterCount"] = 16
            hit = True
    if hit:
        with open(BOOKS_JSON, "w", encoding="utf-8") as f:
            json.dump(bl if isinstance(bj, list) else {**bj, "books": bl}, f,
                      ensure_ascii=False, indent=None)
        print("✓ books.json chapterCount 更新")
    else:
        print("⚠ books.json 未找到该书")
