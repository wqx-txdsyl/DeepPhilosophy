# -*- coding: utf-8 -*-
"""#197 西西弗神话（c80947d011a6）修复
病因（CHKLIST ✗D：'《卡利古拉》第一~三幕无篇标题'）:
  ① book_detail toc 缺 part 卡利古拉（meta 有、detail 无）→ 前端渲染三幕无篇标题；
  ② part.index=13 错：惯例 part.index = 其下首章 index（#190 附录/#193/#198 均如此），
     卡利古拉首章=第一幕 idx14，应为 14（现 13 指向卡夫卡附录章）；
  ③ idx0 版权页（CIP 数据 21 块）+ idx1 目录（86 块含 17 张目录页插图）作为章残留，
     #196 范式：书级页/目录不建章 → 剔除；
  ④ 正文 12 章 + 卡利古拉 3 幕内容完好（含图片块），原样保留。
源: F:/philosophy/西方/阿尔贝·加缪/西西弗神话.epub（杜小真译本）。
修复: 重排章节文件（2-13 → 0-11 正文；14-16 → 12-14 卡利古拉三幕）+ toc 重建:
  0-11 正文 12 章 chapter level1（荒诞与自杀 ~ 弗兰茨·卡夫卡作品中的希望与荒诞）
  12 part 卡利古拉（剧本）level0（idx=其下首章 12）
  13/14 第二幕/第三幕 chapter level1
  chapterCount 17→15；双端 meta/book_detail/books.json 同步。
用法: python _xr_197_xxfs_rebuild.py [--dry]
"""
import json, os, re, sys, shutil

BID = "c80947d011a6"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

def norm(s):
    return re.sub(r"\s+", "", s or "")

# 旧 idx → 新 idx 映射（旧 0/1 版权页/目录剔除）
MOVE = {2: 0, 3: 1, 4: 2, 5: 3, 6: 4, 7: 5, 8: 6, 9: 7, 10: 8, 11: 9, 12: 10, 13: 11,
        14: 12, 15: 13, 16: 14}
TITLES = ["荒诞与自杀", "荒诞之壁", "哲学式自杀", "荒诞的自由", "唐璜主义", "戏剧",
          "征服", "哲学与小说", "基里洛夫", "没有前途的创作", "西西弗神话",
          "弗兰茨·卡夫卡作品中的希望与荒诞", "第一幕", "第二幕", "第三幕"]

# ---- 读旧章（内容原样保留，仅重编号） ----
files = {}
for old, new in MOVE.items():
    ch = json.load(open(os.path.join(SRC, f"{old}.json"), encoding="utf-8"))
    ch["index"] = new
    ch["title"] = TITLES[new]
    files[new] = ch
    assert len(ch["content"]) > 0, f"旧{old} 空章!"
    imgs = sum(1 for b in ch["content"] if b.get("type") == "image")
    nc = sum(len(norm(b.get("value", ""))) for b in ch["content"])
    print(f"[{new:2d}] ← 旧{old:2d} {ch['title'][:22]:<24s} {nc:6d}字 {len(ch['content']):4d}块 (图{imgs}) | 首: {ch['content'][0].get('value','(图)')[:26]!r}")
assert len(files) == 15

# ---- toc 重建 ----
toc = ([{"type": "chapter", "title": TITLES[i], "index": i, "level": 1} for i in range(12)]
       + [{"type": "part", "title": "卡利古拉（剧本）", "index": 12, "level": 0}]
       + [{"type": "chapter", "title": TITLES[i], "index": i, "level": 1} for i in range(13, 15)])
print(f"\ntoc 项: {len(toc)}")
for t in toc:
    print(f"  {t['type']:8s} level{t.get('level')} idx{t['index']} | {t['title'][:36]}")

# ---- 字数对照 ----
total = 0
for i in range(15):
    total += sum(len(norm(b.get("value", ""))) for b in files[i]["content"])
print(f"\n新总净: {total}")
old_total = 0
for i in [0, 1] + list(MOVE):
    ch = json.load(open(os.path.join(SRC, f"{i}.json"), encoding="utf-8"))
    old_total += sum(len(norm(b.get("value", ""))) for b in ch["content"])
print(f"旧总净(含版权页/目录): {old_total}  新净为正文 12 章+卡利古拉 3 幕")

# ---- 验证: 卡利古拉三幕内容完整 ----
for i in (12, 13, 14):
    c = files[i]["content"]
    txt = "".join(norm(b.get("value", "")) for b in c)
    assert "幕落" in txt or "剧终" in txt, f"idx{i} 缺幕落/剧终!"
print("\n✓ 卡利古拉三幕含幕落/剧终")

# ---- 验证: 正文关键句保留（杜小真译本实际译法） ----
ch0 = "".join(norm(b.get("value", "")) for b in files[0]["content"])
ch10 = "".join(norm(b.get("value", "")) for b in files[10]["content"])
ch11 = "".join(norm(b.get("value", "")) for b in files[11]["content"])
print("✓ 正文:",
      "荒诞与自杀含'真正严肃的哲学命题'" if "真正严肃的哲学命题" in ch0 else "✗!",
      "| 西西弗神话含'西西弗无声的喜悦'" if "西西弗无声的喜悦" in ch10 else "✗!",
      "| 卡夫卡附录含'原著编者按语'" if "原著编者按语" in ch11 else "✗!")

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
for new in range(15):
    ch = files[new]
    json.dump({"index": new, "title": ch["title"], "content": ch["content"]},
              open(os.path.join(SRC, f"{new}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
meta = {
    "bookId": old_meta.get("bookId") or BID,
    "title": old_meta.get("title") or "西西弗神话",
    "author": old_meta.get("author") or "阿尔贝·加缪",
    "toc": toc,
    "cover": old_meta.get("cover"),
    "chapterCount": 15,
    "chapterTitles": TITLES,
}
json.dump(meta, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print(f"✓ 写入 {SRC}: 15 章 + meta.json")

shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
print("✓ 同步 DP chapters")

for p in (DETAIL_SRC, DETAIL_DST):
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))
        d["toc"] = toc
        d["chapterCount"] = 15
        d["chapterTitles"] = TITLES
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
        print(f"✓ book_detail 更新: {p}")

if os.path.exists(BOOKS_JSON):
    bj = json.load(open(BOOKS_JSON, encoding="utf-8"))
    bl = bj if isinstance(bj, list) else bj.get("books", [])
    hit = False
    for b in bl:
        if b.get("id") == BID:
            b["chapterCount"] = 15
            hit = True
    if hit:
        with open(BOOKS_JSON, "w", encoding="utf-8") as f:
            json.dump(bl if isinstance(bj, list) else {**bj, "books": bl}, f,
                      ensure_ascii=False, indent=None)
        print("✓ books.json chapterCount 更新")
    else:
        print("⚠ books.json 未找到该书")
