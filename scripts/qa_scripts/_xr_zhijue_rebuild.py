# -*- coding: utf-8 -*-
"""知觉现象学 5b827532ec8b 修复（一次性，四部分标题缺失 → 加 4 part + 删前置页）
旧数据 26 章 = 四部分平铺（导论/身体/被感知的世界/自为的存在），part 标题缺失。
修复: 删 5 个前置页章（目录/扉页/版权页/插页/出版说明）+ 4 part(level 0)
      前言/译后记/引用著作/主要译名对照 独立章保留
正文内容不动，只改结构
用法: python _xr_zhijue_rebuild.py [--dry]
"""
import json, os, sys, shutil

SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters/5b827532ec8b"
DST = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/5b827532ec8b"

DELETE = {0, 1, 2, 3, 4}  # 目录/扉页/版权页/插页/出版说明
# 四部分（原始 index 左闭右开）
PARTS = [
    (6, 10, "导论：传统偏见和现象学的还原"),
    (10, 16, "第一部分　身体"),
    (16, 20, "第二部分　被感知的世界"),
    (20, 23, "第三部分　自为的存在和存在在世界"),
]

old = [json.load(open(os.path.join(SRC, f"{i}.json"), encoding="utf-8")) for i in range(26)]

toc = []
files = {}
ch_index = 0
n_del = 0
for i, ch in enumerate(old):
    for a, b, title in PARTS:
        if i == a:
            toc.append({"type": "part", "title": title, "level": 0, "index": ch_index})
            break
    if i in DELETE:
        n_del += 1
        continue
    ch['index'] = ch_index
    toc.append({"type": "chapter", "title": ch['title'], "index": ch_index, "level": 1})
    files[ch_index] = ch
    ch_index += 1

print(f"旧章 26 → 新章 {len(files)}（删 {n_del} 前置页）| toc {len(toc)}")
for t in toc:
    if t['type'] == 'part':
        print("  ", t['title'])

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
    "bookId": old_meta.get("bookId") or "5b827532ec8b",
    "title": old_meta.get("title") or "知觉现象学",
    "author": old_meta.get("author") or "莫里斯·梅洛-庞蒂",
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
