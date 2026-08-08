# -*- coding: utf-8 -*-
"""《王阳明全集：简体注释版》（909e887aac01）重建（一次性）
问题: book_detail/meta 的 chapterTitles 在 i11 多插一个"版权页"导致整体错位一位
（点 i11"版权页"实际打开 11.json = 年谱一）；文件层标题/内容正确。
真实结构（按卷首版权页 CIP 分册名）:
  [part] 传习录、书信     i1-25  25 章（传习录上中下+附录/书一~六/年谱一二三+附录一二/传志 10 篇）
  [part] 诗赋、墓志、祭文  i27-44 18 章（赋骚七首~墓志祭文等）
  [part] 序记说、杂著     i46-49  4 章（序/记/说/杂著）
  [part] 奏疏、公移       i51-64 14 章（奏疏一~八/公移一~三+南赣/思田/征藩）
删 4 个卷首版权页章（i0/26/45/50，CIP 数据无正文价值，i0 尾还粘"传习录"标题行）
→ 61 章 + 4 part，重编号 0-60。文件内容逐 block 原样保留。
用法: python _xr_wymqj_rebuild.py [--dry]
"""
import json, os, re, sys, shutil

BID = "909e887aac01"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

# 旧 index 顺序（跳过 4 个版权页 0/26/45/50）
ORDER = list(range(1, 26)) + list(range(27, 45)) + list(range(46, 50)) + list(range(51, 65))
PARTS = [
    ("传习录、书信", 25),    # 25 章
    ("诗赋、墓志、祭文", 18),  # 18 章
    ("序记说、杂著", 4),      # 4 章
    ("奏疏、公移", 14),       # 14 章
]
assert sum(n for _, n in PARTS) == len(ORDER) == 61

old = {}
for i in ORDER:
    p = os.path.join(SRC, f"{i}.json")
    if not os.path.exists(p):
        print(f"!! 缺旧文件 {p}")
        sys.exit(1)
    old[i] = json.load(open(p, encoding="utf-8"))

# 新结构
toc = []
files = {}
idx = 0
pi = 0
for pname, n in PARTS:
    toc.append({"type": "part", "title": pname, "index": idx, "level": 0})
    for k in range(n):
        oi = ORDER[idx]
        ch = old[oi]
        toc.append({"type": "chapter", "title": ch["title"], "index": idx, "level": 1})
        files[idx] = {"index": idx, "title": ch["title"], "content": ch["content"]}
        idx += 1
    pi += 1

total_chars = 0
for i in sorted(files):
    nc = sum(len(b.get("value", "")) for b in files[i]["content"])
    total_chars += nc
    print(f"  {i:3d} {files[i]['title'][:40]:42s} {nc:7d} 字")
print(f"总: {len(files)} 章 + {len(PARTS)} part, {total_chars} 字符（旧 65 章含 4 版权页）")
for tt in toc:
    print(f"  [{'part' if tt['type']=='part' else 'chapter'}] {tt['title'][:44]}")
print("首:", files[0]["title"], "| 末:", files[60]["title"])

if "--dry" in sys.argv:
    # 校验: 无版权页残留、标题与旧文件一致
    n_res = 0
    for i, ch in files.items():
        if "版权" in ch["title"]:
            print(f"⚠ 版权标题残留: {i}")
            n_res += 1
        if re.search(r"[①-⑩].*[年谱]", ch["title"]):
            print(f"⚠ 疑似残留 [{i}]: {ch['title'][:30]}")
            n_res += 1
    print(f"残留: {n_res}")
    sys.exit(0)

# 备份旧数据
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
    "title": old_meta.get("title") or "王阳明全集：简体注释版",
    "author": old_meta.get("author") or "王阳明",
    "toc": toc,
    "cover": old_meta.get("cover"),
    "chapterCount": len(files),
    "chapterTitles": [ch["title"] for ch in files.values()],
}
json.dump(meta, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print(f"✓ 写入 {SRC}: {len(files)} 章 + meta.json")

shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
print("✓ 同步 DP chapters")

# book_detail 双端: 替换 toc/chapterCount/chapterTitles，其余字段保留
for p in (DETAIL_SRC, DETAIL_DST):
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))
        d["toc"] = toc
        d["chapterCount"] = len(files)
        d["chapterTitles"] = [ch["title"] for ch in files.values()]
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
        print(f"✓ book_detail 更新: {p}")

# books.json cc 更新（DP 端）
if os.path.exists(BOOKS_JSON):
    bj = json.load(open(BOOKS_JSON, encoding="utf-8"))
    bl = bj if isinstance(bj, list) else bj.get("books", [])
    hit = False
    for b in bl:
        if b.get("id") == BID:
            b["chapterCount"] = len(files)
            hit = True
    if hit:
        with open(BOOKS_JSON, "w", encoding="utf-8") as f:
            json.dump(bl if isinstance(bj, list) else {**bj, "books": bl}, f, ensure_ascii=False, indent=None)
        print("✓ books.json chapterCount 更新")
    else:
        print("⚠ books.json 未找到该书")
