# -*- coding: utf-8 -*-
"""#未入清单 导读德勒兹《差异与重复》（7f462a9750e8）补录修复
病因: OCR 完成的 20 本未入清单书之一。旧 19 章 toc 是字符串数组（摘要句当标题：
  '第1章描述了我们对差异的传统构想的局限。德勒兹指出，…'），章节化完全错误。
源: F:/philosophy/西方/吉尔·德勒兹/导读德勒兹_差异与重复_.pdf（282 页扫描版，
  Edinburgh Philosophical Guides 汉译（重庆大学出版社'拜德雅'导读系列），
  checkpoint OCR 282 页 fail 12 页：4/5/6/9/13/19/27/265/275/279/280/281；
  书内页码 = PDF页 - 19）
结构（目录 p10-11 确认）:
  p0-9 封面/CIP（书级页） ｜ p10-11 目录（弃用） ｜ p12-13 丛书编者前言（p13 fail 缺尾）
  p14-15 致谢 ｜ p16-19 书名缩写（p19 fail 缺尾） ｜ p20-27 导言（p27 fail 缺第8页）
  p28-45 文本导读·导论 重复与差异 ｜ p46-86 第1章 自在的差异
  p87-135 第2章 自为的重复 ｜ p136-171 第3章 思想的图像 ｜ p172-215 第4章 差异的理念综合
  p216-243 第5章 可感物的不对称综合 ｜ p244-257 研究帮助（术语表/进阶阅读书目/写作技巧）
  p258-265 参考文献（p265 fail 缺尾） ｜ p266-273 索引 ｜ p274-281 译后记（p275-281 fail 缺）
  书内页码偏移 +19（p20 导言1、p28 文本导读9、p46 第1章27…p216 第5章197）
修复: 全量重建 14 章 + part 文本导读（idx=4）:
  页眉过滤: 奇数页章名页眉（'导言N'/'文本导读N'/'研究帮助'/'参考文献'/'索引'，N 可无）
   偶数页粘连页眉（'N导读德勒兹（差异与重复）'，N=阿拉伯/罗马数字，OCR 变体'德勤兹'/'德勒益'）；
  章标题行（'第N章XXX'/'导论重复与差异'独立行）页内任意位置精确匹配剔除；
  无页脚页码（页码在页眉区）；
  段落: 每页过滤后行拼接为一段（OCR 书范式）；
  fail 页缺内容如实保留（段数=页数-缺页），不补不编造。
用法: python _xr_7f462a9750e8_dlddz_cyycf_rebuild.py [--dry]
"""
import json, os, re, sys, shutil

BID = "7f462a9750e8"
CKPT = r"f:\program\Python\PhiAgent\backend\data\dp_pdf_import_ckpt.json"
SAFE = "西方_吉尔_德勒兹_导读德勒兹_差异与重复_.pdf"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

def norm(s):
    return re.sub(r"\s+", "", s or "")

# 14 章: (idx, 标题, 起始页, 结束页) — PDF 页
CH = [
    (0, "丛书编者前言", 12, 13),
    (1, "致谢", 14, 15),
    (2, "书名缩写", 16, 19),
    (3, "导言", 20, 27),
    (4, "导论 重复与差异", 28, 45),
    (5, "第1章 自在的差异", 46, 86),
    (6, "第2章 自为的重复", 87, 135),
    (7, "第3章 思想的图像", 136, 171),
    (8, "第4章 差异的理念综合", 172, 215),
    (9, "第5章 可感物的不对称综合", 216, 243),
    (10, "研究帮助", 244, 257),
    (11, "参考文献", 258, 265),
    (12, "索引", 266, 273),
    (13, "译后记", 274, 281),
]
# 章标题独立行（页内任意位置精确匹配剔除）
STRIP_TITLES = {
    "导论重复与差异", "第1章自在的差异", "第2章自为的重复", "第3章思想的图像",
    "第4章差异的理念综合", "第5章可感物的不对称综合",
}
# 奇数页章名页眉（带/不带数字）
HEADER_RE = re.compile(r"^(丛书编者前言|致谢|书名缩写|导言|文本导读|研究帮助|参考文献|索引|译后记)\d*$")
# 偶数页粘连页眉: 'N导读德勒兹（差异与重复）'（N=阿拉伯/罗马数字/OCR噪声如'%'/'1%'，
# 变体 德勤兹/德勒益；前缀一律非中文且≤4字符）
EVEN_HEADER_RE = re.compile(r"^[^一-鿿]{0,4}导读德勒")

ckpt = json.load(open(CKPT, encoding="utf-8"))
pages = ckpt["ocr"][SAFE]
npages = {int(k): v for k, v in pages.items() if v and v != "__FAILED__"}
fails = sorted([int(k) for k, v in pages.items() if v == "__FAILED__"])
print(f"OCR 页: {min(npages)}-{max(npages)} 共 {len(npages)} 页, fail {len(fails)} 页: {fails}")

def page_lines(i):
    """页 → 过滤页眉/标题后的行"""
    t = npages.get(i, "")
    if not t:
        return []
    ls = [ln.strip() for ln in t.split("\n") if ln.strip()]
    if not ls:
        return []
    if HEADER_RE.match(ls[0]) or EVEN_HEADER_RE.match(ls[0]):
        ls.pop(0)
    # 页眉剥后首行裸数字页码残留（如 p244 '191'）剔除
    while ls and re.fullmatch(r"\d{1,4}", ls[0]):
        ls.pop(0)
    ls = [l for l in ls if l not in STRIP_TITLES]
    return ls

# ---- 逐章解析（页级段落范式） ----
files = {}
for idx, title, p0, p1 in CH:
    paras = []
    for i in range(p0, p1 + 1):
        ls = page_lines(i)
        if ls:
            paras.append("".join(ls))
    if not paras:
        print(f"⚠ 章{idx} {title!r}: 无内容")
    files[idx] = {"index": idx, "title": title,
                  "content": [{"type": "text", "value": p} for p in paras]}
    nc = sum(len(norm(p)) for p in paras)
    first = paras[0][:30] if paras else "(空)"
    print(f"[{idx:2d}] {title[:22]:<24s} {nc:6d}字 {len(paras):3d}段 | {first!r}")
assert len(files) == 14

# ---- 验证 ----
total = 0
for idx in range(14):
    total += sum(len(norm(b["value"])) for b in files[idx]["content"])
print(f"\n新总净: {total}")
old_total = 0
for i in range(19):
    p = os.path.join(SRC, f"{i}.json")
    if os.path.exists(p):
        ch = json.load(open(p, encoding="utf-8"))
        old_total += sum(len(norm(b.get("value", ""))) for b in ch["content"])
print(f"旧总净: {old_total}  差: {total - old_total:+d}")

all_text = "".join(norm(b["value"]) for idx in range(14) for b in files[idx]["content"])
# 页眉清零：粘连页眉（'N导读德勒兹/德勒益（差异与重复）'）全文不得残留
header_remains = re.findall(r"[^\n]{0,6}导读德勒[兹益勤]（差异与重复）", all_text)
print("页眉清零:", "✓" if not header_remains else f"✗ {header_remains[:5]}")
# 部分章名页眉（导言N/文本导读N）不剥会混入奇数页正文——检查各章首段
for i in (3, 4, 5):
    b0 = norm(files[i]["content"][0]["value"])[:60]
    print(f"  章{i} 首段: {b0!r}")
# 章标题清零：无独立'第N章XXX'段
pure_titles = [norm(b["value"]) for idx in range(14) for b in files[idx]["content"]
               if norm(b["value"]) in STRIP_TITLES]
print("章标题清零:", "✓" if not pure_titles else f"✗ {pure_titles}")
# 关键内容验证
ch = {idx: "".join(norm(b["value"]) for b in files[idx]["content"]) for idx in range(14)}
checks = [
    (0, "前言", "阅读/解读"),
    (1, "致谢", "曼彻斯特城市大学"),
    (3, "导言", "吉尔·德勒兹是"),
    (4, "导论", "重复不是一般性"),
    (5, "第1章", "波菲利"),
    (6, "第2章", "被动综合"),
    (7, "第3章", "样态或解决的公设"),
    (8, "第4章", "微积分"),
    (9, "第5章", "热力学"),
    (10, "研究帮助", "术语"),
    (11, "参考文献", "Adkins"),
    (12, "索引", "阿尔都塞"),
    (13, "译后记", "译者在翻译这些引文"),
]
print("验证:", "  ".join(f"{'✓'+t if kw in ch[i] else '✗'+t+'!'}" for i, t, kw in checks))

# ---- toc（14 章 + part 文本导读） ----
toc = ([{"type": "chapter", "title": files[i]["title"], "index": i, "level": 1} for i in range(4)]
       + [{"type": "part", "title": "文本导读", "index": 4, "level": 0}]
       + [{"type": "chapter", "title": files[i]["title"], "index": i, "level": 1} for i in range(4, 14)])
print(f"\ntoc 项: {len(toc)}")
for t in toc[:6] + toc[-3:]:
    print(f"  {t['type']:8s} level{t.get('level')} idx{t['index']} {t['title'][:36]}")

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
for idx in range(14):
    f = files[idx]
    json.dump({"index": idx, "title": f["title"], "content": f["content"]},
              open(os.path.join(SRC, f"{idx}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
meta = {
    "bookId": old_meta.get("bookId") or BID,
    "title": old_meta.get("title") or "导读德勒兹《差异与重复》",
    "author": old_meta.get("author") or "乔·休斯",
    "toc": toc,
    "cover": old_meta.get("cover"),
    "chapterCount": 14,
    "chapterTitles": [files[i]["title"] for i in range(14)],
}
json.dump(meta, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print(f"✓ 写入 {SRC}: 14 章 + meta.json")

shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
print("✓ 同步 DP chapters")

for p in (DETAIL_SRC, DETAIL_DST):
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))
        d["toc"] = toc
        d["chapterCount"] = 14
        d["chapterTitles"] = meta["chapterTitles"]
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
        print(f"✓ book_detail 更新: {p}")

if os.path.exists(BOOKS_JSON):
    bj = json.load(open(BOOKS_JSON, encoding="utf-8"))
    bl = bj if isinstance(bj, list) else bj.get("books", [])
    hit = False
    for b in bl:
        if b.get("id") == BID:
            b["chapterCount"] = 14
            hit = True
    if hit:
        with open(BOOKS_JSON, "w", encoding="utf-8") as f:
            json.dump(bl if isinstance(bj, list) else {**bj, "books": bl}, f,
                      ensure_ascii=False, indent=None)
        print("✓ books.json chapterCount 更新")
    else:
        print("⚠ books.json 未找到该书")
