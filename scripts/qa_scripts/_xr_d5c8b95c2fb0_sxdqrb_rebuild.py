# -*- coding: utf-8 -*-
"""#未入清单 学术的进展（d5c8b95c2fb0，培根）补录修复
病因: OCR 完成的 20 本未入清单书之一。books.json cc=0（从未章节化，
  book_chapters 无目录无数据，book_detail 仅有基础信息）。
源: F:/philosophy/西方/弗朗西斯·培根/学术的进展.pdf（208 页扫描版，
  刘运同译（上海人民出版社），checkpoint OCR 208 页 fail 3：0/1/64；
  书内页码 = PDF页 - 8（p63 页脚'55'、p207 页脚'199'））
结构（目录 p8 确认）:
  p0-1 fail 封面 ｜ p2 CIP ｜ p3 出版说明（标题+内容同页，书内无页码）
  p4-7 中文版前言（书内 1-4；p4 标题+内容同页；p7 尾'译者 2007年3月'）
  p8 目录（跳过）
  p9-63 第一卷 献给国王陛下（书内 1-55；p9 章前标题+正文同页；p63 尾页 13 行）
  p64 fail 第一卷尾/隔页（书内 56，缺，如实保留）
  p65-207 第二卷 献给国王陛下（书内 57-199；p65 章前标题+正文同页；p207 = PDF 末页）
  ⚠ PDF 残本：目录显示人名对照表（书内 204）/译后记（书内 210）——
    超出 PDF 208 页范围整体缺失（第二卷书内 200-203 尾亦缺），不补不编造
页眉系统: 奇数 PDF 页 = 书名页眉'学术的进展'（变体'学术的远展'）；
  偶数 PDF 页 = 章名页眉'第X卷献给国王X下'（变体 下/座下/隆下/陆下；
  p189 奇数页亦为'第二卷献给国王陛下'章名式——统一按模式剥）；
  页脚页码: 独立裸数字行（'55'/'142'）位于页末，剥尾行；
  章前页: '第一卷'+'献给国王陛下'（p9/p65 标题+正文同页）
修复: 新建 4 章（无旧数据）:
  页眉过滤: 书名页眉'^学术的(进展|远展)$' / 章名页眉'^第[一二]卷献给国王\S{0,2}下$'
  剥首行；页脚页码剥尾行（'^\d{1,3}$'）；章前标题行页内任意位置剔除；
  段落: 每页过滤后行拼接为一段（OCR 书范式）；
  fail 页缺内容如实保留（p0/1 封面、p64 第一卷尾页），不补不编造。
用法: python _xr_d5c8b95c2fb0_sxdqrb_rebuild.py [--dry]
"""
import json, os, re, sys, shutil, time

BID = "d5c8b95c2fb0"
CKPT = r"f:\program\Python\PhiAgent\backend\data\dp_pdf_import_ckpt.json"
SAFE = "西方_弗朗西斯_培根_学术的进展.pdf"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
# ⚠ 2026-08-08 事故修正：前端本地 dev 读 app/public/backend/data/book_chapters，必须双写
DST2 = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

def norm(s):
    return re.sub(r"\s+", "", s or "")

# 6 章: (idx, 标题, 起始页, 结束页) — PDF 页
CH = [
    (0, "出版说明", 3, 3),
    (1, "中文版前言", 4, 7),
    (2, "第一卷 献给国王陛下", 9, 63),
    (3, "第二卷 献给国王陛下", 65, 211),   # p208-211 第二卷注释页（脚注集中页，书内 200-203）
    (4, "人名对照表", 212, 217),           # 书内 204-209（OCR 队列新补）
    (5, "译后记", 218, 219),               # 书内 210-211（OCR 队列新补）；p220 版权页跳过
]
TOC_PAGES = {8}
# 奇数页书名页眉（变体'学术的远展'）
BOOK_HEADER_RE = re.compile(r"^学术的(进展|远展)$")
# 偶数页章名页眉（'第一卷献给国王下'/'第二卷献给国王陛下'，变体 下/座下/隆下/陆下；
# 含 p189 奇数页例外；副题'献给国王陛下'由 STRIP_TITLES 处理——此处只剥'第X卷'前缀式）
CH_HEADER_RE = re.compile(r"^第[一二]卷献给国王\S{0,2}下$")
# 人名对照表/译后记章名页眉（p212-219）
SECT_HEADER_RE = re.compile(r"^(人名对照表|译后记)$")
# 页脚页码（独立裸数字行，位于页末）
FOOT_NUM_RE = re.compile(r"^\d{1,3}$")
# 章前标题行（页内任意位置精确匹配剔除）
STRIP_TITLES = {"出版说明", "中文版前言", "第一卷", "第二卷", "献给国王陛下",
                "人名对照表", "译后记", "目录"}

# checkpoint 读重试（OCR 队列并发写 → 瞬时截断）
ckpt = None
for _try in range(5):
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
    """页 → 过滤页眉/标题/页脚页码后的行"""
    t = npages.get(i, "")
    if not t:
        return []
    ls = [ln.strip() for ln in t.split("\n") if ln.strip()]
    if not ls:
        return []
    while ls and (BOOK_HEADER_RE.match(ls[0]) or CH_HEADER_RE.match(ls[0])
                  or SECT_HEADER_RE.match(ls[0])):
        ls.pop(0)
    if ls and FOOT_NUM_RE.fullmatch(ls[-1]):
        ls.pop()
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
# 页眉清零：书名/章名页眉独立段不得残留
bad_h = [norm(b["value"]) for idx in range(6) for b in files[idx]["content"]
         if BOOK_HEADER_RE.match(norm(b["value"])) or CH_HEADER_RE.match(norm(b["value"]))
         or SECT_HEADER_RE.match(norm(b["value"]))]
print("页眉清零:", "✓" if not bad_h else f"✗ {bad_h[:4]}")
# 页脚页码清零：各段尾行不得是纯数字
bad_f = [norm(b["value"])[-6:] for idx in range(6) for b in files[idx]["content"]
         if FOOT_NUM_RE.fullmatch(norm(b["value"])[-4:])]
print("页脚页码清零:", "✓" if not bad_f else f"✗ {bad_f[:4]}")
# 章标题清零
pure_titles = [norm(b["value"]) for idx in range(6) for b in files[idx]["content"]
               if norm(b["value"]) in STRIP_TITLES]
print("章标题清零:", "✓" if not pure_titles else f"✗ {pure_titles[:5]}")
# 关键内容验证
ch = {idx: "".join(norm(b["value"]) for b in files[idx]["content"]) for idx in range(6)}
checks = [
    (0, "出版说明", "第一部学术著作"),
    (1, "中文版前言", "知识就是力量"),
    (2, "第一卷", "贤明的国王下"),
    (3, "第二卷", "陛下，那些生前子孙众多"),
    (3, "注释页", "圣经·雅各书"),
    (4, "人名对照表", "汉语拼音字母音序排列"),
    (5, "译后记", "如果培根地下有知"),
]
print("验证:", "  ".join(f"{'✓'+t if kw in ch[i] else '✗'+t+'!'}" for i, t, kw in checks))
# 残本确认：p64（书内 56）= 第一卷注释页仍缺（fail）
print("第二卷尾含'（25）':", "（25）" in ch[3])

# ---- toc ----
toc = [{"type": "chapter", "title": files[i]["title"], "index": i, "level": 1} for i in range(6)]
print(f"\ntoc 项: {len(toc)}")

if "--dry" in sys.argv:
    sys.exit(0)

# ---- 写入（无旧数据，不备份） ----
for p in (SRC, DST, DST2):
    shutil.rmtree(p, ignore_errors=True)
for p in (SRC, DST, DST2):
    os.makedirs(p)
for idx in range(6):
    f = files[idx]
    for p in (SRC, DST, DST2):
        json.dump({"index": idx, "title": f["title"], "content": f["content"]},
                  open(os.path.join(p, f"{idx}.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=None)
meta = {
    "bookId": BID, "title": "学术的进展", "author": "弗朗西斯·培根",
    "toc": toc, "cover": None, "chapterCount": 6,
    "chapterTitles": [files[i]["title"] for i in range(6)],
}
for p in (SRC, DST, DST2):
    json.dump(meta, open(os.path.join(p, "meta.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
print(f"✓ 写入三处: {len(os.listdir(SRC))} 文件/处（PhiAgent + DP backend + DP app/public）")

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
