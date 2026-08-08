# -*- coding: utf-8 -*-
"""#141 民主主义与教育（约翰·杜威，王承绪译）efdfdda23776 修复
病因（CHKLIST ✗M 缺章 + 重复内容）:
  源 EPUB（F:/philosophy/西方/约翰·杜威/民主主义与教育.epub）为博客转载版：
  ① 缺第二十二章（个人和世界）、第二十五章（认识论）——转载即残缺；
  ② 第二十一章标题重复两次（转载翻页重复），旧数据把第一段（8798字）归入
     第二十章尾（旧20章 18641 = 9827+8798），第二十一章 = 重复段（8805字）。
旧数据其余 23 章逐章字数与源吻合（差异 ≤23 字）→ 内容完整，保留。
修复:
  旧 23 章（序+第一~十九+二十三+二十四+二十六）原样保留；
  第二十/二十一章从源 EPUB 按标题行重新切分（丢弃重复段）；
  第二十二/二十五章用爱思想网单章全文（逐字人工修正 OCR 错字：
  22 章 ~25 处、25 章 ~60 处，修正版存 _xr_mzyjy_ch22/25_fixed.txt）。
  26 章 + 序 = 27 章，无 section（与旧数据一致）。
用法: python _xr_mzyjy_rebuild.py [--dry]
"""
import json, os, re, sys, shutil, zipfile
from bs4 import BeautifulSoup

BID = "efdfdda23776"
EPUB = "F:/philosophy/西方/约翰·杜威/民主主义与教育.epub"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"
CH22_TXT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_xr_mzyjy_ch22_fixed.txt")
CH25_TXT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_xr_mzyjy_ch25_fixed.txt")

def norm(s):
    return re.sub(r"\s+", "", s or "")

# ---- 1) 源 EPUB 提取第二十/二十一章 ----
z = zipfile.ZipFile(EPUB)
def lines_of(fn):
    soup = BeautifulSoup(z.read(fn).decode("utf-8", "ignore"), "html.parser")
    return [l.strip() for l in soup.get_text("\n").split("\n") if l.strip()]

CH_RE = re.compile(r"^第[一二三四五六七八九十百\d]+章")
def extract_chap(filenames, title_prefix, skip_dupes):
    """从标题行后收集到下一个章标题前，每行一块；跳过重复标题行"""
    lines = []
    for fn in filenames:
        lines += lines_of(fn)
    i = next(k for k, l in enumerate(lines) if l.startswith(title_prefix))
    j = i + 1
    blocks = []
    while j < len(lines):
        l = lines[j]
        if CH_RE.match(l):
            # 重复标题行（转载翻页重复）→ 其后的重复正文应整体丢弃
            if skip_dupes and norm(l) == norm(lines[i]):
                break
            break
        if l:
            blocks.append({"type": "text", "value": l})
        j += 1
    return blocks

# split_002: 第二十章→第二十一章→(重复)→第二十三章; split_003: 第二十一章尾部+第二十三章起
blocks_20 = extract_chap(["index_split_002.html"], "第二十章", False)
blocks_21 = extract_chap(["index_split_002.html", "index_split_003.html"], "第二十一章", True)

# ---- 2) 修正后第二十二/二十五章 ----
def txt_blocks(path):
    lines = [l.strip() for l in open(path, encoding="utf-8").read().split("\n") if l.strip()]
    return [{"type": "text", "value": l} for l in lines]

blocks_22 = txt_blocks(CH22_TXT)
blocks_25 = txt_blocks(CH25_TXT)

# ---- 3) 组装 27 章 ----
files = {}
MAP = {**{i: i for i in range(20)}, 22: 23, 23: 24, 24: 26}  # 旧→新序号（旧20/21弃用）
for i, n in MAP.items():
    files[n] = json.load(open(os.path.join(SRC, f"{i}.json"), encoding="utf-8"))
for n, blocks in ((20, blocks_20), (21, blocks_21), (22, blocks_22), (25, blocks_25)):
    files[n] = {"index": n, "title": None, "content": blocks}
TITLES = {
    20: "第二十章 知识科目和实用科目",
    21: "第二十一章 自然科目和社会科目",
    22: "第二十二章 个人和世界",
    25: "第二十五章 认识论",
}
for n in (20, 21, 22, 25):
    files[n]["title"] = TITLES[n]

assert len(files) == 27, len(files)      # 序+26 章
assert [files[i]["title"] for i in range(27)][-1] == "第二十六章 道德论"

toc = [{"type": "chapter", "title": files[i]["title"], "index": i, "level": 1}
       for i in range(27)]
meta_new = {"chapterCount": 27, "chapterTitles": [files[i]["title"] for i in range(27)], "toc": toc}

# ---- 校验 ----
print("=== 27 章字数 ===")
total = 0
for i in sorted(files):
    nc = sum(len(b.get("value", "")) for b in files[i]["content"])
    total += nc
    mark = ""
    if i in (20, 21):
        mark = f"  (源: {9827 if i == 20 else 8798})"
    elif i in (22, 25):
        mark = f"  (爱思想修正: {11088 if i == 22 else 9247})"
    print(f"  [{i:2d}] {files[i]['title'][:30]:32s} {nc:6d} 字{mark}")
print(f"新总: {total}")
old_total = 0
if os.path.isdir(SRC):
    for fn in os.listdir(SRC):
        if fn.endswith(".json") and fn != "meta.json":
            ch = json.load(open(os.path.join(SRC, fn), encoding="utf-8"))
            old_total += sum(len(b.get("value", "")) for b in ch["content"] if b.get("type") == "text")
print(f"旧总: {old_total}（去重复段+补2章）")
# 20 章尾应为第二十章提 要（内容含"知识和行动"类词）——人工核对
print("新20章首块:", files[20]["content"][0]["value"][:50])
print("新20章末块:", files[20]["content"][-1]["value"][:50])
print("新21章首块:", files[21]["content"][0]["value"][:50])
print("新21章末块:", files[21]["content"][-1]["value"][:50])
print("新22章首块:", files[22]["content"][0]["value"][:40])
print("新22章末块:", files[22]["content"][-1]["value"][:40])
print("新25章首块:", files[25]["content"][0]["value"][:40])
print("新25章末块:", files[25]["content"][-1]["value"][:40])

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
    print(f"备份旧数据 → {os.path.basename(SRC) + suf}")
os.makedirs(SRC)
old_meta = {}
old_bid = SRC + "_old_bad"
if os.path.isdir(old_bid) and os.path.exists(os.path.join(old_bid, "meta.json")):
    old_meta = json.load(open(os.path.join(old_bid, "meta.json"), encoding="utf-8"))
for i, ch in files.items():
    json.dump(ch, open(os.path.join(SRC, f"{i}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
meta = {
    "bookId": old_meta.get("bookId") or BID,
    "title": old_meta.get("title") or "民主主义与教育",
    "author": old_meta.get("author") or "约翰·杜威",
    "toc": toc,
    "cover": old_meta.get("cover"),
    "chapterCount": 27,
    "chapterTitles": meta_new["chapterTitles"],
}
json.dump(meta, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print(f"✓ 写入 {SRC}: 27 章 + meta.json")

shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
print("✓ 同步 DP chapters")

for p in (DETAIL_SRC, DETAIL_DST):
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))
        d["toc"] = toc
        d["chapterCount"] = 27
        d["chapterTitles"] = meta_new["chapterTitles"]
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
        print(f"✓ book_detail 更新: {p}")

if os.path.exists(BOOKS_JSON):
    bj = json.load(open(BOOKS_JSON, encoding="utf-8"))
    bl = bj if isinstance(bj, list) else bj.get("books", [])
    hit = False
    for b in bl:
        if b.get("id") == BID:
            b["chapterCount"] = 27
            hit = True
    if hit:
        with open(BOOKS_JSON, "w", encoding="utf-8") as f:
            json.dump(bl if isinstance(bj, list) else {**bj, "books": bl}, f, ensure_ascii=False, indent=None)
        print("✓ books.json chapterCount 更新")
    else:
        print("⚠ books.json 未找到该书")
