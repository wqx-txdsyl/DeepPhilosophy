# -*- coding: utf-8 -*-
"""#182 自然科学的形而上学基础（e29d0f5e550c）修复
病因（CHKLIST ✗C：'旧 str 格式 toc：目录页条目混入（带页码），正文只拆出四部分无章'）:
  旧 7 章 toc 是字符串数组（'第一部分：动量学的形而上学基础·……·20' 目录条目带页码），
  正文只拆出四部分，前言/附篇全丢。
源: F:/philosophy/西方/伊曼努尔·康德/自然科学的形而上学基础.pdf（185 页扫描版，
  邓晓芒译，生活·读书·新知三联书店'新知文库'，checkpoint OCR 185 页无 fail；
  书内页码 = PDF页 - 15）
结构（目录 p15 确认，9 段）:
  p0-2 封面/CIP/德文书名（书级页） ｜ p3-13 译序 ｜ p14 编委会页（书级页，跳过）
  p15 目录（OCR 混排，弃用） ｜ p16-34 前言 ｜
  p35-63 第一部分：动量学的形而上学基础（界说1.物质是在空间中的运动物）
  p64-110 第二部分：动力学的形而上学基础（界说1.物质当它充满一个空间时就是运动物）
  p111 页内切割：前半二部尾（'我还要声明一点'）+ 后半 附I：对动力学的总附释 起
  p112 页内切割：前半附I尾 + 后半 附Ⅱ：对动力学的总说明 起（p112-134）
  p135-159 第三部分：机械学的形而上学基础（界说1.当运动物作为运动物而具有动力时）
  p160 页内切割：前半三部尾 + 后半 附I：对机械学的总说明 起（p160-164）
  p165-171 第四部分：现象学的形而上学基础（界说当运动物作为运动物可以成为经验的对象时）
  p172 页内切割：前半四部尾 + 后半 附I：对现象学的总说明 起（p172-184，书末）
修复: 全量重建 10 章（idx 连续 0-9，toc 忠实目录条目原文）:
  页码过滤: 末行裸数字 '^\d{1,4}$'（无 ·N· 装饰）；
  无书眉（首行无重复固定串）；
  段落: 每页过滤后行拼接为一段（OCR 书范式，对齐 _rebuild_nicomachus.py）；
  附篇页内切割: p111/p112/p160/p172 四个边界页按标题行切两半
   （前段归前章、后段归附篇章，标题行剔除）——页级段落+页内切割，内容无跨章错位；
  章首标题块剥离: ① 折行标题（'第一部分'+'动量学的形而上学基础' 拼接==去冒号标题 → 两行同删）
   ② 前缀剥离（'译序在18一-19世纪…'→剥'译序'；'前言'独立行→整行删）。
用法: python _xr_182_zrkxdxjxjc_rebuild.py [--dry]
"""
import json, os, re, sys, shutil

BID = "e29d0f5e550c"
CKPT = r"f:\program\Python\PhiAgent\backend\data\dp_pdf_import_ckpt.json"
SAFE = "西方_伊曼努尔_康德_自然科学的形而上学基础.pdf"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

def norm(s):
    return re.sub(r"\s+", "", s or "")

# 10 章: (idx, 标题, 起始页, 结束页) — PDF 页
CH = [
    (0, "译序", 3, 13),
    (1, "前言", 16, 34),
    (2, "第一部分：动量学的形而上学基础", 35, 63),
    (3, "第二部分：动力学的形而上学基础", 64, 110),
    (4, "附I：对动力学的总附释", 111, 111),
    (5, "附Ⅱ：对动力学的总说明", 112, 134),
    (6, "第三部分：机械学的形而上学基础", 135, 159),
    (7, "附I：对机械学的总说明", 160, 164),
    (8, "第四部分：现象学的形而上学基础", 165, 171),
    (9, "附I：对现象学的总说明", 172, 184),
]
# 页内切割: 页号 -> (标题行, 所属章idx)
SPLITS = {
    111: ("附I：对动力学的总附释", 4),
    112: ("附Ⅱ：对动力学的总说明", 5),
    160: ("附I：对机械学的总说明", 7),
    172: ("附I：对现象学的总说明", 9),
}
SKIP_PAGES = {14, 15}   # 编委会页/目录页（书级页不建章）

ckpt = json.load(open(CKPT, encoding="utf-8"))
pages = ckpt["ocr"][SAFE]
npages = {int(k): v for k, v in pages.items() if v and v != "__FAILED__"}
print(f"OCR 页: {min(npages)}-{max(npages)} 共 {len(npages)} 页, fail: {[k for k,v in pages.items() if v=='__FAILED__']}")

PAGE_FOOT_RE = re.compile(r"^\d{1,4}$")   # 末行裸数字页码
# 章首标题处理
JOINED_TITLES = {norm(t).replace("：", "") for _, t, _, _ in CH}   # 折行拼接 == 去冒号标题
PREFIXES = sorted(["第一部分", "第二部分", "第三部分", "第四部分", "译序", "前言"],
                  key=len, reverse=True)

def strip_head(lines):
    """章首标题块剥离：①折行标题两行同删 ②前缀剥（剥净则删行）"""
    while lines:
        n = norm(lines[0])
        if not n:
            lines.pop(0)
            continue
        # ① 折行: 行0+行1 拼接 == 去冒号标题（'第一部分'+'动量学的形而上学基础'）
        if len(lines) > 1:
            joined = n + norm(lines[1])
            if joined in JOINED_TITLES:
                lines.pop(0)
                lines.pop(0)
                continue
        # ② 前缀剥（'译序在18一-19世纪…' / 独立行'前言'）
        hit = False
        for pfx in PREFIXES:
            if n.startswith(pfx):
                rest = n[len(pfx):]
                rest = re.sub(r"^[？?！!·…—\s]+", "", rest)
                if rest:
                    lines[0] = rest
                else:
                    lines.pop(0)
                hit = True
                break
        if not hit:
            return

def page_lines(i):
    """页 → 过滤页码后的行（无书眉；末行裸数字页码剔除）"""
    t = npages.get(i, "")
    if not t:
        return []
    ls = [ln.strip() for ln in t.split("\n") if ln.strip()]
    if not ls:
        return []
    if PAGE_FOOT_RE.match(ls[-1]):
        ls.pop()
    return ls

# ---- 逐章解析（页级段落 + 页内切割） ----
paras = [[] for _ in range(10)]
cur = 0
CH_P0 = [p0 for _, _, p0, _ in CH]
for p in range(3, 185):
    if p in SKIP_PAGES:
        continue
    ls = page_lines(p)
    if not ls:
        continue
    if p not in SPLITS:
        # 非切割页: 章切换（附篇章首已由切割接管）
        if p in CH_P0:
            cur = CH_P0.index(p)
            strip_head(ls)   # 章首页行级标题剥离（译序/前言/第X部分+部分名折行）
        paras[cur].append("".join(ls))
    else:
        title, k = SPLITS[p]
        cut = None
        for j, l in enumerate(ls):
            if l == title:
                cut = j
                break
        if cut is None:
            print(f"⚠ 切割页 p{p} 未找到标题行 {title!r} → 整页归章{k}")
            cur = k
            paras[cur].append("".join(ls))
        else:
            pre, post = "".join(ls[:cut]), "".join(ls[cut + 1:])
            if pre:
                paras[cur].append(pre)
            if post:
                paras[k].append(post)
            cur = k

files = {}
for idx, title, p0, p1 in CH:
    pl = paras[idx]
    if not pl:
        print(f"⚠ 章{idx} {title!r}: 无内容")
    files[idx] = {"index": idx, "title": title,
                  "content": [{"type": "text", "value": p} for p in pl]}
    nc = sum(len(norm(p)) for p in pl)
    first = pl[0][:34] if pl else "(空)"
    last = pl[-1][:22] if pl else ""
    print(f"[{idx:2d}] {title[:26]:<28s} {nc:6d}字 {len(pl):3d}段 | {first!r} … {last!r}")
assert len(files) == 10

# ---- 验证 ----
total = 0
for idx in range(10):
    total += sum(len(norm(b["value"])) for b in files[idx]["content"])
print(f"\n新总净: {total}")
old_total = 0
for i in range(7):
    p = os.path.join(SRC, f"{i}.json")
    if os.path.exists(p):
        ch = json.load(open(p, encoding="utf-8"))
        old_total += sum(len(norm(b.get("value", ""))) for b in ch["content"])
print(f"旧总净: {old_total}  差: {total - old_total:+d}")

all_text = "".join(norm(b["value"]) for idx in range(10) for b in files[idx]["content"])
# 页码清零：无独立裸数字段
pure_pages = [norm(b["value"]) for idx in range(10) for b in files[idx]["content"]
              if re.fullmatch(r"\d{1,4}", norm(b["value"]))]
print("页码清零:", "✓" if not pure_pages else f"✗ {pure_pages[:5]}")
# 目录页混排清零：无 '·……·数字' 目录残影（正文省略号如'不是··…·就是'为自然脚注，不算）
print("目录残影清零:", "✓" if not re.search(r"·+……+·+\d", all_text) else "✗")
# 关键内容验证（各章锚点）
ch = {idx: "".join(norm(b["value"]) for b in files[idx]["content"]) for idx in range(10)}
checks = [
    (0, "译序", "牛顿的物理学体系"),
    (1, "前言", "如果单从自然一词"),
    (2, "第一部", "物质是在空间中的运动物"),
    (3, "第二部", "物质，当它充满一个空间时"),
    (4, "附I总附释", "当我们回顾所有这一切动力"),
    (5, "附Ⅱ总说明", "物质自然的一般动力学原则是"),
    (6, "第三部", "当运动物作为运动物而具有动力时"),
    (7, "附I机械学", "运动的传递只有借这样一种"),
    (8, "第四部", "可以成为经验的对象时"),
    (9, "附I现象学", "形而上学的物体学说就以虚空"),
]
print("验证:", "  ".join(f"{'✓' + t if kw in ch[i] else '✗' + t + '!'}" for i, t, kw in checks))

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
    "title": old_meta.get("title") or "自然科学的形而上学基础",
    "author": old_meta.get("author") or "康德",
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
