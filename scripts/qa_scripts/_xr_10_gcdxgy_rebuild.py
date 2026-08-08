# -*- coding: utf-8 -*-
"""#10 共产党宣言（420f076ba733）修复
病因（CHKLIST ✗C：'段首文本当标题，章程条目混入'）:
  旧 25 章 toc 混乱：'附录'打头、段首文本当标题（'一、大资本家阶级…'=共产主义原理
  正文句）、末项为注释文本；章节边界完全错误。
源: F:/philosophy/西方/卡尔·马克思/共产党宣言.pdf（人民出版社 2018
   '纪念马克思诞辰200周年·马克思恩格斯著作特辑'单行本，211 页扫描版，
   checkpoint OCR 211 页 fail 3 页：p6/p24/p90——全部为插图页/标题页，不建章无碍；
   书内页码 = PDF页 - 22）
结构（目录 p21-22 确认）:
  p0-4 封面/CIP/编委会 ｜ p5-6 扉页(德文,图) ｜ p7-9 编辑说明 ｜ p10-20 编者引言
  p21-22 目录 ｜ p23-24 书名页+插图(1848德文版封面) ｜
  p25-26 1872年德文版序言 ｜ p27-28 1882年俄文版序言 ｜ p29-30 1883年德文版序言
  p31-36 1888年英文版序言 ｜ p37-42 1890年德文版序言 ｜ p43-44 1892年波兰文版序言
  p45-47 1893年意大利文版序言 ｜
  p48 正文《共产党宣言》导言（'一个幽灵…'） ｜ p49-62 一、资产者和无产者
  p63-73 二、无产者和共产党人 ｜ p74-85 三、社会主义的和共产主义的文献
  p86-88 四、共产党人对各种反对党派的态度 ｜ p89-90 附录标题页+插图 ｜
  p91-98 附录:共产主义信条草案(恩格斯) ｜ p99-116 附录:共产主义原理(恩格斯)
  p117-138 附录:关于共产主义者同盟的历史(恩格斯) ｜
  p139-160 附录:马克思恩格斯关于《共产党宣言》的重要论述摘编
  p161-166 附录:共产主义者同盟章程 ｜ p167-194 注释 ｜ p195-210 人名索引
修复: 全量重建 21 章 + part（附录）:
  页眉过滤: 首行精确匹配章名页眉集合（'共产党宣言'书名页眉/序言标题/章名/
   '编辑说明'/'编者引言'/'注释'/'人名索引'）或'附录'开头的章内页眉；
  页码过滤: 末行'·N·'/'·N.'格式；
  段落: 每页过滤后行拼接为一段（OCR 书范式，对齐 _rebuild_nicomachus.py）；
  章首页标题粘连行（p63'无产者和共产党人一…'/p91'弗·恩格斯共产主义信条草案'）
   保留（内容完整无损，标题在前缀）；
  part 附录 level0 idx=14（#197 范式：part.index = 其下首章 index）。
用法: python _xr_10_gcdxgy_rebuild.py [--dry]
"""
import json, os, re, sys, shutil

BID = "420f076ba733"
CKPT = r"f:\program\Python\PhiAgent\backend\data\dp_pdf_import_ckpt.json"
SAFE = "西方_卡尔_马克思_共产党宣言.pdf"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

def norm(s):
    return re.sub(r"\s+", "", s or "")

# 21 章: (idx, 标题, 起始页, 结束页)
CH = [
    (0, "编辑说明", 7, 9),
    (1, "编者引言", 10, 20),
    (2, "1872年德文版序言", 25, 26),
    (3, "1882年俄文版序言", 27, 28),
    (4, "1883年德文版序言", 29, 30),
    (5, "1888年英文版序言", 31, 36),
    (6, "1890年德文版序言", 37, 42),
    (7, "1892年波兰文版序言", 43, 44),
    (8, "1893年意大利文版序言", 45, 47),
    (9, "共产党宣言", 48, 48),
    (10, "一、资产者和无产者", 49, 62),
    (11, "二、无产者和共产党人", 63, 73),
    (12, "三、社会主义的和共产主义的文献", 74, 85),
    (13, "四、共产党人对各种反对党派的态度", 86, 88),
    (14, "附录：共产主义信条草案", 91, 98),
    (15, "附录：共产主义原理", 99, 116),
    (16, "附录：关于共产主义者同盟的历史", 117, 138),
    (17, "附录：马克思恩格斯关于《共产党宣言》的重要论述摘编", 139, 160),
    (18, "附录：共产主义者同盟章程", 161, 166),
    (19, "注释", 167, 194),
    (20, "人名索引", 195, 210),
]

ckpt = json.load(open(CKPT, encoding="utf-8"))
pages = ckpt["ocr"][SAFE]
npages = {int(k): v for k, v in pages.items() if v and v != "__FAILED__"}
print(f"OCR 页: {min(npages)}-{max(npages)} 共 {len(npages)} 页, fail: {[k for k,v in pages.items() if v=='__FAILED__']}")

# 页眉集合（精确匹配整行）
TITLE_HEADS = {
    "编辑说明", "编者引言", "共产党宣言", "注释", "人名索引",
    "1872年德文版序言", "1882年俄文版序言", "1883年德文版序言",
    "1888年英文版序言", "1890年德文版序言", "1892年波兰文版序言",
    "1893年意大利文版序言",
    "资产者和无产者", "二无产者和共产党人", "三社会主义的和共产主义的文献",
    "四共产党人对各种反对党派的态度",
}
PAGE_FOOT_RE = re.compile(r"^·\d{1,4}[·.]?$")

# 章首页标题粘连行剥除前缀（标题+正文同行的 OCR 粘连）
STRIP_PREFIXES = sorted(TITLE_HEADS | {
    "无产者和共产党人", "资产者和无产者",          # 章名变体（无数字前缀）
    "共产主义信条草案", "共产主义原理",            # 附录文件名（章标题去'附录：'）
    "关于共产主义者同盟的历史",
    "马克思恩格斯关于《共产党宣言》的重要论述摘编",
    "共产主义者同盟章程",
    "弗·恩格斯",                                  # 附录作者行
}, key=len, reverse=True)

def strip_head_join(lines):
    """章首页标题行清理（p63/p86/p91 等 OCR 拆行变体）：
    ① 标题独立行/标题+正文粘连行 → 循环剥前缀（作者行+文件名），剥净则整行删；
    ② 标题编号残片行（'一'）单独删；
    ③ 标题折行：行0（短、无标点、标题前缀）+ 行1 拼接 = 完整标题 → 两行同删"""
    while lines:
        n = norm(lines[0])
        if not n:
            lines.pop(0)
            continue
        # ② 标题编号残片（如 p63 行'一'）
        if re.fullmatch(r"[一二三四五六七八九十]{1,2}", n):
            lines.pop(0)
            continue
        hit = False
        for p in STRIP_PREFIXES:
            pn = norm(p)
            if len(n) >= len(pn) and n.startswith(pn):
                rest = n[len(pn):]
                rest = re.sub(r"^[一二三四五六七八九十]、?", "", rest)   # '二、'残片
                rest = re.sub(r"^\d{1,3}", "", rest)                    # 注号/页码残留（'12'）
                rest = re.sub(r"^[？?！!·…—\s]+", "", rest)              # OCR 噪声分隔符
                if rest:
                    lines[0] = rest
                else:
                    lines.pop(0)
                hit = True
                break
        if not hit:
            # ③ 标题折行（p86：'四共产党人对各种'+'反对党派的态度'）
            if len(n) <= 12 and len(lines) > 1 and not re.search(r"[，。；：！？]", n):
                joined = n + norm(lines[1])
                for p in STRIP_PREFIXES:
                    if joined == norm(p):
                        lines.pop(0)
                        lines.pop(0)
                        hit = True
                        break
        if not hit:
            return

def page_text(i):
    """页 → 过滤页眉/页码后的行"""
    t = npages.get(i, "")
    if not t:
        return []
    lines = [ln.strip() for ln in t.split("\n") if ln.strip()]
    if not lines:
        return []
    # 首行页眉：章名/书名/附录章内页眉（'附录共产主义信条草案'等）
    if lines[0] in TITLE_HEADS or lines[0].startswith("附录"):
        lines.pop(0)
    # 末行页码 ·N·/·N.
    if lines and PAGE_FOOT_RE.match(lines[-1]):
        lines.pop()
    return lines

# ---- 逐章解析（页级段落范式） ----
files = {}
for idx, title, p0, p1 in CH:
    paras = []
    for i in range(p0, p1 + 1):
        lines = page_text(i)
        if lines:
            # 章首页标题粘连行剥前缀（仅处理当前章区间首行，避免跨章误伤）
            if i == p0:
                strip_head_join(lines)
            paras.append("".join(lines))
    if not paras:
        print(f"⚠ 章{idx} {title!r}: 无内容")
    files[idx] = {"index": idx, "title": title,
                  "content": [{"type": "text", "value": p} for p in paras]}
    first = paras[0][:30] if paras else "(空)"
    nc = sum(len(norm(p)) for p in paras)
    print(f"[{idx:2d}] {title[:32]:<34s} {nc:6d}字 {len(paras):3d}段 | {first!r}")
assert len(files) == 21

# ---- 验证 ----
total = 0
for idx in range(21):
    total += sum(len(norm(b["value"])) for b in files[idx]["content"])
print(f"\n新总净: {total}")
old_total = 0
for i in range(25):
    p = os.path.join(SRC, f"{i}.json")
    if os.path.exists(p):
        ch = json.load(open(p, encoding="utf-8"))
        old_total += sum(len(norm(b.get("value", ""))) for b in ch["content"])
print(f"旧总净: {old_total}  差: {total - old_total:+d}")

all_text = "".join(norm(b["value"]) for idx in range(21) for b in files[idx]["content"])
# 页眉清零：书名页眉'共产党宣言'整行独立段、'资产者和无产者'独立段
pure_heads = [norm(b["value"]) for idx in range(21) for b in files[idx]["content"]
              if norm(b["value"]) in TITLE_HEADS or norm(b["value"]).startswith("附录")]
print("页眉清零:", "✓" if not pure_heads else f"✗ {pure_heads[:5]}")
pure_pages = [norm(b["value"]) for idx in range(21) for b in files[idx]["content"]
              if re.fullmatch(r"·?\d{1,4}·?[·.]?", norm(b["value"]))]
print("页码清零:", "✓" if not pure_pages else f"✗ {pure_pages[:5]}")
# 关键内容验证
ch9 = "".join(norm(b["value"]) for b in files[9]["content"])
ch10 = "".join(norm(b["value"]) for b in files[10]["content"])
ch11 = "".join(norm(b["value"]) for b in files[11]["content"])
ch15 = "".join(norm(b["value"]) for b in files[15]["content"])
print("验证:",
      "✓导言'幽灵'" if "共产主义的幽灵" in ch9 else "✗导言!",
      "✓一章'至今一切社会'" if "至今一切社会的历史" in ch10 else "✗一章!",
      "✓二章'共产党人'" if "共产党人同全体无产者" in ch11 else "✗二章!",
      "✓原理'大资本家'" if "大资本家" in ch15 else "✗原理!")

# ---- toc（21 章 + part 附录） ----
toc = ([{"type": "chapter", "title": files[i]["title"], "index": i, "level": 1} for i in range(14)]
       + [{"type": "part", "title": "附录", "index": 14, "level": 0}]
       + [{"type": "chapter", "title": files[i]["title"], "index": i, "level": 1} for i in range(14, 21)])
print(f"\ntoc 项: {len(toc)}")
for t in toc[:4] + toc[13:17] + toc[-2:]:
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
for idx in range(21):
    f = files[idx]
    json.dump({"index": idx, "title": f["title"], "content": f["content"]},
              open(os.path.join(SRC, f"{idx}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
meta = {
    "bookId": old_meta.get("bookId") or BID,
    "title": old_meta.get("title") or "共产党宣言",
    "author": old_meta.get("author") or "马克思、恩格斯",
    "toc": toc,
    "cover": old_meta.get("cover"),
    "chapterCount": 21,
    "chapterTitles": [files[i]["title"] for i in range(21)],
}
json.dump(meta, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print(f"✓ 写入 {SRC}: 21 章 + meta.json")

shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
print("✓ 同步 DP chapters")

for p in (DETAIL_SRC, DETAIL_DST):
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))
        d["toc"] = toc
        d["chapterCount"] = 21
        d["chapterTitles"] = meta["chapterTitles"]
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
        print(f"✓ book_detail 更新: {p}")

if os.path.exists(BOOKS_JSON):
    bj = json.load(open(BOOKS_JSON, encoding="utf-8"))
    bl = bj if isinstance(bj, list) else bj.get("books", [])
    hit = False
    for b in bl:
        if b.get("id") == BID:
            b["chapterCount"] = 21
            hit = True
    if hit:
        with open(BOOKS_JSON, "w", encoding="utf-8") as f:
            json.dump(bl if isinstance(bj, list) else {**bj, "books": bl}, f,
                      ensure_ascii=False, indent=None)
        print("✓ books.json chapterCount 更新")
    else:
        print("⚠ books.json 未找到该书")
