# -*- coding: utf-8 -*-
"""#147 活出生命的意义（维克多·弗兰克尔）6226193b9dbb 修复
病因（CHKLIST ✗B 第二部分标题缺失 + 意义疗法各节当章平铺）:
  旧 26 章：① 缺"第二部分 意义疗法"标题章（旧 4 第一部分 在集中营的经历 43240 字
  尾部混入第二部分 h1 导言 908 字）；② 意义疗法 20 节（追求意义~为悲剧性的乐观主义
  辩护）当章平铺（旧 5-24）；③ 旧 1 Man's Search 页、旧 23 写在后面的话 较源略少
  内容（324 vs 338、59 vs 69 字）。
源（F:/philosophy/西方/维克多·弗兰克尔/活出生命的意义.epub，单文件 Section0001.xhtml）：
  h1×7（封面/Man's Search for Meaning/前言/自序/第一部分 在集中营的经历/
  第二部分 意义疗法/后记）+ h2×20（第二部分节）+ p×412；ePUBw.com 广告在 div（跳过）。
修复:
  基于源重建 7 章：0 封面（image 块沿用旧 webp）｜1 Man's Search for Meaning｜
  2 前言｜3 自序｜4 第一部分 在集中营的经历｜5 第二部分 意义疗法（h1 导言 908 字 +
  20 个 h2 节标题块为 section 锚点）｜6 后记；cc 26→7；
  广告 div（ePUBw.COM）不进入正文（div 非 h1/h2/p 天然跳过）。
用法: python _xr_hcsmyy_rebuild.py [--dry]
"""
import json, os, re, sys, shutil, zipfile
from bs4 import BeautifulSoup

BID = "6226193b9dbb"
EPUB = "F:/philosophy/西方/维克多·弗兰克尔/活出生命的意义.epub"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

NEW_TITLES = {
    0: "封面", 1: "Man's Search for Meaning", 2: "前言", 3: "自序",
    4: "第一部分 在集中营的经历", 5: "第二部分 意义疗法", 6: "后记",
}

# ---- 源解析：h1=章 h2=节标题块 p=正文块（含 img）----
z = zipfile.ZipFile(EPUB)
raw = z.read('OEBPS/Text/Section0001.xhtml').decode('utf-8', 'ignore')
soup = BeautifulSoup(raw, 'html.parser')

# 封面 image 块沿用旧数据（webp 已入库）
old0 = json.load(open(os.path.join(SRC, "0.json"), encoding="utf-8"))
COVER_IMG = [b for b in old0["content"] if b.get("type") == "image"][0]

def norm(s):
    return re.sub(r"\s+", "", s or "")

# 按标题名映射章 index
idx_of_title = {t: i for i, t in NEW_TITLES.items()}
files = {i: {"index": i, "title": t, "content": [], "sections": {}} for i, t in NEW_TITLES.items()}
cur = None
for el in soup.find_all(['h1', 'h2', 'p']):
    if el.name == 'h1':
        t = el.get_text(' ', strip=True)
        cur = idx_of_title.get(t)
        if cur is None:
            raise SystemExit(f"未识别章标题: {t!r}")
    elif el.name == 'h2':
        if cur != 5:
            raise SystemExit(f"h2 出现在章 {cur}: {el.get_text(' ', strip=True)!r}")
        t = el.get_text(' ', strip=True)
        files[5]["content"].append({"type": "text", "value": t})
        files[5]["sections"][t] = len(files[5]["content"]) - 1
    else:  # p
        img = el.find('img')
        if img is not None:
            files[cur]["content"].append(dict(COVER_IMG))  # 沿用旧 webp 块
        else:
            t = el.get_text('', strip=True)
            if not t or "ePUBw" in t:
                continue  # 空段/广告段
            files[cur]["content"].append({"type": "text", "value": t})

assert all(len(f["content"]) > 0 for f in files.values()), "有空章"

# ---- 逐块验证：重建 p 块 vs 源 p（剔除 section 标题块后逐对对比）----
src_groups = {}
_cur = None
for el in soup.find_all(['h1', 'h2', 'p']):
    if el.name == 'h1':
        _cur = el.get_text(' ', strip=True)
        src_groups.setdefault(_cur, [])
    elif el.name == 'p' and el.find('img') is None:
        src_groups[_cur].append(el.get_text('', strip=True))
bad = 0
for i, title in NEW_TITLES.items():
    ps = [b["value"] for b in files[i]["content"] if b.get("type") == "text" and b.get("value") not in files[5]["sections"]]
    sps = src_groups[title]
    if len(ps) != len(sps):
        print(f"[{i}] {title}: 重建 {len(ps)} p vs 源 {len(sps)} p *** 块数不同 ***")
        bad += 1
    for k, (b, s) in enumerate(zip(ps, sps)):
        if b != s:
            print(f"[{i}] 块{k} 不匹配:\n  重建({len(b)}): {b[:50]}\n  源  ({len(s)}): {s[:50]}")
            bad += 1
            if bad > 12:
                raise SystemExit("差异过多，终止")
print(f"逐块 diff: {0 if bad == 0 else bad} 处不匹配")
if bad:
    raise SystemExit("块级验证失败")

# ---- 验证 ----
print("=== 7 章重建对照（源净字数）===")
EXPECT = {  # 源按 h1/h2 统计的净字数
    0: 45, 1: 338, 2: 2241, 3: 1421, 4: 42337, 6: 4905,
    5: 908 + 648 + 198 + 1089 + 954 + 1025 + 427 + 942 + 293 + 1631 + 114
       + 955 + 837 + 719 + 3004 + 504 + 964 + 183 + 367 + 69 + 7286,
}
total = 0
for i in range(7):
    f = files[i]
    nc = sum(len(norm(b.get("value", ""))) for b in f["content"])
    total += nc
    print(f"[{i}] {f['title'][:24]:<26s} {nc:6d} 字净 {len(f['content']):4d}块  期望{EXPECT[i]:6d}  差{nc-EXPECT[i]:+6d}")
print(f"新总净: {total}（含封面图）")
for i, secs in files[5]["sections"].items():
    pass
print("章5 sections:", ", ".join(f"{t}@{s}" for t, s in files[5]["sections"].items()))
old_total = 0
for i in range(26):
    p = os.path.join(SRC, f"{i}.json")
    if os.path.exists(p):
        ch = json.load(open(p, encoding="utf-8"))
        old_total += sum(len(norm(b.get("value", ""))) for b in ch["content"])
print(f"旧总净: {old_total}  差: {total-old_total:+d}")
print("新0块:", files[0]["content"])
print("新5首块:", files[5]["content"][0]["value"][:40])
print("新5尾块:", files[5]["content"][-1]["value"][:40])
print("新6首块:", files[6]["content"][0]["value"][:40])

if "--dry" in sys.argv:
    sys.exit(0)

# ---- toc ----
toc = [{"type": "chapter", "title": t, "index": i, "level": 1} for i, t in NEW_TITLES.items()]
toc2 = []
for t in toc:
    toc2.append(t)
    if t["index"] == 5:
        for st, sec in files[5]["sections"].items():
            toc2.append({"type": "section", "title": st, "index": 5, "sec": sec, "level": 2})
toc = toc2
meta_new = {"chapterCount": 7, "chapterTitles": [NEW_TITLES[i] for i in range(7)], "toc": toc}
print("\n=== toc ===")
for t in toc:
    print(f"  {t['type']:8s} idx{t['index']} lv{t.get('level')} sec={t.get('sec')!r} {t['title'][:36]}")

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
for i in range(7):
    f = files[i]
    json.dump({"index": i, "title": f["title"], "content": f["content"]},
              open(os.path.join(SRC, f"{i}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
meta = {
    "bookId": old_meta.get("bookId") or BID,
    "title": old_meta.get("title") or "活出生命的意义",
    "author": old_meta.get("author") or "维克多·弗兰克尔",
    "toc": toc,
    "cover": old_meta.get("cover"),
    "chapterCount": 7,
    "chapterTitles": meta_new["chapterTitles"],
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
        d["chapterTitles"] = meta_new["chapterTitles"]
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
