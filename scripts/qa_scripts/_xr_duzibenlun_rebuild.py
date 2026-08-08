# -*- coding: utf-8 -*-
"""读《资本论》 b3219ec260ed 修复（一次性，两组"一~"编号重复缺 part）
旧数据 15 章 = 四部分平铺：致读者 / 从《资本论》到马克思的哲学 /
  巴里巴尔《关于历史唯物主义的基本概念》(一~九) / 阿尔都塞《资本论》的对象(一~四)。
问题: 两篇论文的章号各自从"一"起，无 part 层级区分。
修复: 加 2 个 part(level 0)，正文内容不动
  - 巴里巴尔：关于历史唯物主义的基本概念 → 原 [2,11)
  - 阿尔都塞：《资本论》的对象 → 原 [11,15)
用法: python _xr_duzibenlun_rebuild.py [--dry]
"""
import json, os, sys, shutil

SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters/b3219ec260ed"
DST = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/b3219ec260ed"

PARTS = [
    (2, "巴里巴尔：关于历史唯物主义的基本概念", 0),
    (11, "阿尔都塞：《资本论》的对象", 0),
]

old = [json.load(open(os.path.join(SRC, f"{i}.json"), encoding="utf-8")) for i in range(15)]

toc = []
files = {}
ch_index = 0
for i, ch in enumerate(old):
    for a, title, lv in PARTS:
        if i == a:
            toc.append({"type": "part", "title": title, "level": lv, "index": ch_index})
    ch['index'] = ch_index
    toc.append({"type": "chapter", "title": ch['title'], "index": ch_index, "level": 1})
    files[ch_index] = ch
    ch_index += 1

print(f"旧章 15 → 新章 {len(files)} | toc {len(toc)}")
for t in toc:
    if t['type'] == 'part':
        print("  part:", t['title'])

if '--dry' in sys.argv:
    sys.exit(0)

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
for idx, ch in files.items():
    json.dump(ch, open(os.path.join(SRC, f"{idx}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
meta = {
    "bookId": old_meta.get("bookId") or "b3219ec260ed",
    "title": old_meta.get("title") or "读《资本论》",
    "author": old_meta.get("author") or "路易·阿尔都塞 / 艾蒂安·巴里巴尔",
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
print("✓ 同步 DP")
