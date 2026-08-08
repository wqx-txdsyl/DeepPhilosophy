# -*- coding: utf-8 -*-
"""#未入清单 生存哲学（05e1c5812784，雅斯贝尔斯）补录修复
病因: OCR 完成的 20 本未入清单书之一。books.json cc=0（从未章节化，
  book_chapters 无目录无数据，book_detail 仅有基础信息）。
源: F:/philosophy/西方/卡尔·雅斯贝尔斯/生存哲学.pdf（115 页扫描版，
  《二十世纪西方哲学译丛》（上海译文出版社），checkpoint OCR 115 页 fail 5：
  23/39/41/73/75；讲内页码 = PDF页 - 21（p44'第二讲真理论023'、p114'再版后记093'））
结构（章前页模式明确，目录 p19-21 弃用）:
  p0-3 封面/CIP ｜ p4-5 出版前言（书内 001-002） ｜ p6-18 导言 生存哲学之为哲学
  （书内 003-013；p6 章前页'导言'+副题'生存哲学之为哲学'）
  p19-21 目录（跳过）
  p22-38 第一讲 存在论（书内 014-029；p22 章前页'第一讲'+'存在论'；
    p23 fail = 书内 015 正文起页缺失；p24'对于大全的体验'起正文）
  p39 fail 章间页（第一讲尾/隔页，书内 030） ｜ p40-72 第二讲 真理论
  （书内 031-053；p40 章前页；p41 fail = 书内 032 正文起页缺失；p42'真实性问题'起正文）
  p73 fail 章间页（书内 052/53 之间） ｜ p74-109 第三讲 现实论（书内 053-089；
    p74 章前页；p75 fail = 书内 054 正文起页缺失；p76'现实问题'起正文；p109'088生存暂学'尾）
  p110-114 再版后记（书内 089-093；p110 标题+内容同页；p114 尾'1956年6月于巴塞尔'）
页眉系统: 奇数 PDF 页（书内偶数）= '页码+书名'粘连（'004生存暂学'，书名 OCR 变体
  无数：生存哲学/暂学/暂/暂单/首学/警/者/首擎/营/首/暂半/需半/首单/弃首单/营学——
  首字恒'生'）；偶数 PDF 页（书内奇数）= '章名+页码'粘连
  （'第一讲存在论005'/'第二讲真理论023'/'第三讲现实玲083'/'导言007'/'导005'/'号★003'/
  '号言011'/'蒋版后记091'）；p18 裸页码'013'行
修复: 新建 6 章（无旧数据）:
  页眉过滤: 奇数页'^\d{1,4}生'（页码+书名粘连）/ 偶数页章名+页码粘连
  （'^第[一二三四]讲'前缀 + 导言变体'导言?|号言|号★' + '再版后记|蒋版后记'）/ 裸数字逐层剥首行；
  章前页标题行（'导言'/'第一讲'/'存在论'/'生存哲学之为哲学'等）页内任意位置剔除；
  段落: 每页过滤后行拼接为一段（OCR 书范式）；
  fail 页缺内容如实保留（p23/p41/p75 正文起页、p39/p73 章间页），不补不编造。
用法: python _xr_05e1c5812784_czlsj_rebuild.py [--dry]
"""
import json, os, re, sys, shutil

BID = "05e1c5812784"
CKPT = r"f:\program\Python\PhiAgent\backend\data\dp_pdf_import_ckpt.json"
SAFE = "西方_卡尔_雅斯贝尔斯_生存哲学.pdf"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
# ⚠ 2026-08-08 事故修正：前端本地 dev 读 app/public/backend/data/book_chapters（原为 junction，已改真实副本），必须双写
DST2 = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

def norm(s):
    return re.sub(r"\s+", "", s or "")

# 6 章: (idx, 标题, 起始页, 结束页) — PDF 页
CH = [
    (0, "出版前言", 4, 5),
    (1, "导言 生存哲学之为哲学", 6, 18),
    (2, "第一讲 存在论", 22, 38),
    (3, "第二讲 真理论", 40, 72),
    (4, "第三讲 现实论", 74, 109),
    (5, "再版后记", 110, 114),
]
TOC_PAGES = {19, 20, 21}
# 奇数 PDF 页页眉: 'N生存X'（页码+书名粘连，书名 OCR 变体无数，首字恒'生'）
ODD_HEADER_RE = re.compile(r"^\d{1,4}生")
# 偶数 PDF 页页眉: 章名+页码粘连（'第一讲存在论005'/'导言007'/'导005'/'号★003'/
#   '蒋版后记091'；OCR 变体 真建论/现实玲/04S/07]——'第X讲'后跟 0-8 个非空白变体）
EVEN_HEADER_RE = re.compile(r"^(第[一二三四]讲\S{0,8}|导言?\d*|号言\d*|号★\d*|再版后记\d*|蒋版后记\d*)$")
# 裸数字页码残留（p18 '013'）
BARE_NUM_RE = re.compile(r"^\d{1,4}$")
# 章前页标题行（页内任意位置精确匹配剔除）
STRIP_TITLES = {
    "出版前言", "导言", "生存哲学之为哲学",
    "第一讲", "存在论", "第二讲", "真理论", "第三讲", "现实论", "再版后记",
}

import time
ckpt = None
for _try in range(5):                      # OCR 队列并发写 checkpoint → 瞬时截断，重试
    try:
        ckpt = json.load(open(CKPT, encoding="utf-8"))
        break
    except json.JSONDecodeError:
        time.sleep(2)
if ckpt is None:
    sys.exit("checkpoint 连续 5 次读失败，OCR 队列可能正在写入，稍后重试")
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
    while ls and (ODD_HEADER_RE.match(ls[0]) or EVEN_HEADER_RE.match(ls[0])
                  or BARE_NUM_RE.fullmatch(ls[0])):
        ls.pop(0)
    ls = [l for l in ls if l not in STRIP_TITLES]
    return ls

# ---- 逐章解析（页级段落范式） ----
files = {}
for idx, title, p0, p1 in CH:
    paras = []
    for i in range(p0, p1 + 1):
        if i in TOC_PAGES:
            continue
        lss = page_lines(i)
        if lss:
            paras.append("".join(lss))
    if not paras:
        print(f"⚠ 章{idx} {title!r}: 无内容")
    files[idx] = {"index": idx, "title": title,
                  "content": [{"type": "text", "value": p} for p in paras]}
    nc = sum(len(norm(p)) for p in paras)
    first = paras[0][:30] if paras else "(空)"
    last = paras[-1][:22] if paras else ""
    print(f"[{idx}] {title:<22s} {nc:6d}字 {len(paras):3d}段 | {first!r} … {last!r}")
assert len(files) == 6

# ---- 验证 ----
total = 0
for idx in range(6):
    total += sum(len(norm(b["value"])) for b in files[idx]["content"])
print(f"\n新总净: {total}  (旧无数据, books.json cc=0)")

all_text = "".join(norm(b["value"]) for idx in range(6) for b in files[idx]["content"])
# 页眉清零：'N生存X'粘连与'第X讲XXXN'粘连不得残留
bad_odd = re.findall(r"\d{1,4}生\S{1,3}", all_text)
bad_even = re.findall(r"(?:第[一二三四]讲|导言|号言|号★|再版后记)\S{0,6}\d", all_text)
print("页眉清零:", "✓" if not bad_odd and not bad_even else f"✗ odd:{bad_odd[:3]} even:{bad_even[:3]}")
# 章标题清零：无独立标题段
pure_titles = [norm(b["value"]) for idx in range(6) for b in files[idx]["content"]
               if norm(b["value"]) in STRIP_TITLES]
print("章标题清零:", "✓" if not pure_titles else f"✗ {pure_titles[:5]}")
# 目录清零：目录页关键词（'二十世纪西方哲学译丛'是封面丛书名，不查）
print("目录页清零:", "✓" if "目" not in all_text or not re.search(r"目\s*录", all_text) else "✗")
# 关键内容验证
ch = {idx: "".join(norm(b["value"]) for b in files[idx]["content"]) for idx in range(6)}
checks = [
    (0, "出版前言", "雅斯贝斯系20世纪著名的哲学家"),
    (1, "导言", "盼望"),
    (2, "第一讲", "对于大全的体验"),
    (3, "第二讲", "真理这个名词具有无比的魅力"),
    (4, "第三讲", "当我给我自己照亮了大全"),
    (5, "再版后记", "1956年6月于巴塞尔"),
]
print("验证:", "  ".join(f"{'✓'+t if kw in ch[i] else '✗'+t+'!'}" for i, t, kw in checks))

# ---- toc ----
toc = [{"type": "chapter", "title": files[i]["title"], "index": i, "level": 1} for i in range(6)]
print(f"\ntoc 项: {len(toc)}")

if "--dry" in sys.argv:
    sys.exit(0)

# ---- 写入（无旧数据，不备份） ----
if os.path.isdir(SRC):
    print("⚠ SRC 已存在，跳过（不应发生——本书无旧数据）")
else:
    os.makedirs(SRC)
for idx in range(6):
    f = files[idx]
    json.dump({"index": idx, "title": f["title"], "content": f["content"]},
              open(os.path.join(SRC, f"{idx}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
meta = {
    "bookId": BID, "title": "生存哲学", "author": "卡尔·雅斯贝尔斯",
    "toc": toc, "cover": None, "chapterCount": 6,
    "chapterTitles": [files[i]["title"] for i in range(6)],
}
json.dump(meta, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print(f"✓ 写入 {SRC}: 6 章 + meta.json")

shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
print("✓ 同步 DP backend chapters")
shutil.rmtree(DST2, ignore_errors=True)
shutil.copytree(SRC, DST2)
print("✓ 同步 DP app/public chapters（前端 dev 实际读取路径）")

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
