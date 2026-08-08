# -*- coding: utf-8 -*-
"""#未入清单 信仰寻求理解（56bb065c1796，安瑟伦三篇合订）补录修复
病因: OCR 完成的 20 本未入清单书之一。旧 242 章 toc 是字符串数组
  （目录条目当标题：'第3章有着一种本性…'28字/'第4章续上一章'4字），结构全乱。
源: F:/philosophy/西方/安瑟伦/信仰寻求理解.pdf（425 页扫描版，
  '宗教学译丛'（华夏出版社），checkpoint OCR 425 页 fail 6：
  24/28/218/286/288/294）
结构（三篇合订，每篇内部无运行页眉，章 = 章前页'第N章'+提要 + 正文页）:
  p0-3 封面/CIP ｜ p4-24 《宗教学译丛》总序（目录无，跳过；p24 fail 缺尾）
  独白篇: p25-28 序（p28 fail 缺尾） ｜ p29-34 目录（跳过） ｜ p35-216 第1-80章
  宣讲篇: p217 扉页 ｜ p218 fail ｜ p219-220 序 ｜ p221-222 目录（跳过）
    ｜ p223-266 第1-26章 ｜ p267-272 附（一）（高尼罗《为愚人辩》）
    ｜ p273-286 附（二）（安瑟伦回答；p286 fail 缺尾）
  上帝何以化身为人: p287 扉页 ｜ p288 fail ｜ p289-290 序 ｜ p291-294 目录（跳过，p294 fail）
    ｜ p295-364 第一卷 第1-25章（p295 卷标记行'第'+'卷'） ｜ p365-424 第二卷 第1-23章
  （源目录另有 3 本分册 .txt：独白/宣讲/上帝何以化身为人，txt免查，本次不动）
修复: 全量重建 3 part + 158 章（part 独白篇/宣讲篇/上帝何以化身为人）:
  目录页硬编码跳过（'目○录'/'目◎录'变体，p29-34/p221-222/p291-294）；
  章标题行（'第N章'/'序'/'附（一）'/'附（二）'独立行）→ 切章并剔除；
  化身为人卷标记行（'第'/'卷'单字行）剔除，p295-364=第一卷、p365-424=第二卷；
  段落: 每页过滤后行拼接为一段（OCR 书范式）；
  fail 页缺内容如实保留（p28 序尾/p286 附二尾/p294 目录），不补不编造。
用法: python _xr_56bb065c1796_xyqwlj_rebuild.py [--dry]
"""
import json, os, re, sys, shutil

BID = "56bb065c1796"
CKPT = r"f:\program\Python\PhiAgent\backend\data\dp_pdf_import_ckpt.json"
SAFE = "西方_安瑟伦_信仰寻求理解.pdf"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

def norm(s):
    return re.sub(r"\s+", "", s or "")

# 三篇: (part标题, 起始页, 结束页, 目录页集合, 是否化身为人)
PARTS = [
    ("独白篇", 25, 216, {29, 30, 31, 32, 33, 34}, False),
    ("宣讲篇", 219, 286, {221, 222}, False),
    ("上帝何以化身为人", 289, 424, {291, 292, 293, 294}, True),
]
# 章标题行（独立行，页内任意位置精确匹配 → 切章）
CH_RE = re.compile(r"^第[一二三四五六七八九十百0-9]{1,3}章$")
ORDER_ALT = {"序", "附（一）", "附（二）"}
# 化身为人卷标记行（'第'+'卷'单字行，p295/p365 卷标题拆分）
CDH_STRIP = {"第", "卷"}

ckpt = json.load(open(CKPT, encoding="utf-8"))
pages = ckpt["ocr"][SAFE]
npages = {int(k): v for k, v in pages.items() if v and v != "__FAILED__"}
fails = sorted([int(k) for k, v in pages.items() if v == "__FAILED__"])
print(f"OCR 页: {min(npages)}-{max(npages)} 共 {len(npages)} 页, fail {len(fails)} 页: {fails}")

def page_lines(i, is_cdh):
    """页 → 行（空行去除 + 化身为人卷标记行剔除）"""
    t = npages.get(i, "")
    if not t:
        return []
    ls = [ln.strip() for ln in t.split("\n") if ln.strip()]
    if is_cdh:
        ls = [l for l in ls if l not in CDH_STRIP]
    return ls

# ---- 逐篇解析（自动切章） ----
all_files = []       # list of (part_idx, chapter)
all_toc = []
idx = 0
for pi, (ptitle, p0, p1, toc_pages, is_cdh) in enumerate(PARTS):
    chapters = []    # list of [title, [paras]]
    cur = None
    vol = 1
    for p in range(p0, p1 + 1):
        if p in toc_pages:
            continue
        ls = page_lines(p, is_cdh)
        if not ls:
            continue
        if CH_RE.match(ls[0]) or ls[0] in ORDER_ALT:
            title = ls[0]
            if is_cdh and CH_RE.match(title):
                # 化身为人分卷：p295-364 第一卷、p365-424 第二卷
                if p >= 365:
                    vol = 2
                title = f"第二卷 {title}" if vol == 2 else title
            chapters.append([title, []])
            ls = ls[1:]
        if cur is None and not chapters:
            print(f"⚠ part{pi} 页{p} 无章头，跳过首段")
            continue
        if ls:
            chapters[-1][1].append("".join(ls))
        cur = p
    for title, paras in chapters:
        if not paras:
            print(f"⚠ 空章 {title!r}（part {ptitle}）")
        all_files.append((pi, title, paras))
    print(f"part {pi} {ptitle}: {len(chapters)} 章, "
          f"{sum(sum(len(norm(x)) for x in c[1]) for c in chapters)} 字")

# ---- 写文件结构 ----
files = {}
toc = []
for pi, title, paras in all_files:
    files[idx] = {"index": idx, "title": title,
                  "content": [{"type": "text", "value": p} for p in paras]}
    if idx == 0 or (pi > 0 and all_files[idx - 1][0] != pi):
        toc.append({"type": "part", "title": PARTS[pi][0], "index": idx, "level": 0})
    toc.append({"type": "chapter", "title": title, "index": idx, "level": 1})
    idx += 1
print(f"\n总章数: {len(all_files)}, toc 项: {len(toc)}")

# ---- 验证 ----
total = sum(sum(len(norm(x)) for x in p[2]) for p in all_files)
old_total = 0
old_dir = SRC
if os.path.isdir(old_dir):
    for f in os.listdir(old_dir):
        if f.split(".")[0].isdigit():
            ch = json.load(open(os.path.join(old_dir, f), encoding="utf-8"))
            old_total += sum(len(norm(b.get("value", ""))) for b in ch.get("content", []))
print(f"新总净: {total}  旧总净: {old_total}  差: {total - old_total:+d}")

# 章序列验证
for pi, (ptitle, p0, p1, toc_pages, is_cdh) in enumerate(PARTS):
    ts = [t for i, t, p in all_files if i[0] == pi] if False else [t for pi2, t, p in all_files if pi2 == pi]
    chs = [t for t in ts if CH_RE.match(t)]
    print(f"part{pi} {ptitle}: 章序 {chs[:3]}…{chs[-2:] if len(chs) > 3 else chs} 共{len(chs)}章, 序/附: {[t for t in ts if not CH_RE.match(t)]}")
# 章标题清零：无段以'第N章'独立开头（剔除后）
bad = [norm(b["value"])[:12] for i, t, p in all_files for b in files[i]["content"]
       if CH_RE.match(norm(b["value"])) or norm(b["value"]) in ORDER_ALT]
print("章标题清零:", "✓" if not bad else f"✗ {bad[:4]}")
# 目录页清零：目录条目（'提要'除外）不得来自目录页——抽查目录关键词
all_text = "".join(norm(b["value"]) for i, t, p in all_files for b in files[i]["content"])
print("目录变体清零:", "✓" if "目○录" not in all_text and "目◎录" not in all_text else "✗")
# 关键锚点
def find(kw):
    return any(kw in norm(p) for _, _, paras in all_files for p in paras)
checks = [("独白序", "以沉思的方式"), ("独白1章", "一至高的本性"), ("宣讲1章", "振奋心灵静观上帝"),
          ("附一", "为愚人辩"), ("附二", "驳高尼罗"), ("化身序", "仔细校订"),
          ("化身1章", "口头以及书面的方式"), ("二卷1章", "施恩于" if find("施恩于") else "自愿地允诺")]
print("验证:", "  ".join(f"{'✓'+t if kw and find(kw) else '✗'+t+'!'}" for t, kw in checks))
# fail 缺页如实：段数抽查（宣讲篇 26 章 = 从第1章起 26 个'第N章'）
print("宣讲篇章数:", len([t for pi2, t, p in all_files if pi2 == 1 and CH_RE.match(t)]))

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
for i in range(len(all_files)):
    f = files[i]
    json.dump({"index": i, "title": f["title"], "content": f["content"]},
              open(os.path.join(SRC, f"{i}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
meta = {
    "bookId": old_meta.get("bookId") or BID,
    "title": old_meta.get("title") or "信仰寻求理解",
    "author": old_meta.get("author") or "安瑟伦",
    "toc": toc,
    "cover": old_meta.get("cover"),
    "chapterCount": len(all_files),
    "chapterTitles": [files[i]["title"] for i in range(len(all_files))],
}
json.dump(meta, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print(f"✓ 写入 {SRC}: {len(all_files)} 章 + meta.json")

shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
print("✓ 同步 DP chapters")

for p in (DETAIL_SRC, DETAIL_DST):
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))
        d["toc"] = toc
        d["chapterCount"] = len(all_files)
        d["chapterTitles"] = meta["chapterTitles"]
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
        print(f"✓ book_detail 更新: {p}")

if os.path.exists(BOOKS_JSON):
    bj = json.load(open(BOOKS_JSON, encoding="utf-8"))
    bl = bj if isinstance(bj, list) else bj.get("books", [])
    hit = False
    for b in bl:
        if b.get("id") == BID:
            b["chapterCount"] = len(all_files)
            hit = True
    if hit:
        with open(BOOKS_JSON, "w", encoding="utf-8") as f:
            json.dump(bl if isinstance(bj, list) else {**bj, "books": bl}, f,
                      ensure_ascii=False, indent=None)
        print("✓ books.json chapterCount 更新")
    else:
        print("⚠ books.json 未找到该书")
