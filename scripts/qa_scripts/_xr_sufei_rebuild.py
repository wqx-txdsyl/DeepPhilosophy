# -*- coding: utf-8 -*-
"""苏菲的世界（贾德名作系列三部曲）46736478a11d 修复（一次性，三部曲平铺 → 书/部双层 part）
旧数据 107 章 = 3 本书平铺（苏菲的世界/纸牌的秘密/橙子女孩），无书级。
修复: 删 4 个目录/封面章 + 剥 4 个部标题页块 + 3 书 part(level 0) +
      纸牌秘密五部 part(level 1)（黑桃牌/梅花牌/丑角牌/方块牌/红心牌）
正文内容不动，只改结构
用法: python _xr_sufei_rebuild.py [--dry]
"""
import json, os, sys, shutil

SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters/46736478a11d"
DST = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/46736478a11d"

DELETE = {0, 1, 37, 91}  # [0]封面页 [1]苏菲目录 [37]纸牌目录 [91]橙子目录
# 书级 part（原始 index 左闭右开）
BOOKS = [
    (2, 37, "苏菲的世界"),
    (38, 91, "纸牌的秘密"),
    (92, 107, "橙子女孩"),
]
# 纸牌秘密五部（原始 index 左闭右开）——部标题页块混在上一部末章章尾
PARTS5 = [
    (38, 51, "黑桃牌"),
    (51, 64, "梅花牌"),
    (64, 65, "丑角牌"),
    (65, 78, "方块牌"),
    (78, 91, "红心牌"),
]
# 要剥离的部标题页块（精确匹配，所在章尾）
PART_BLOCKS = {"第二部 梅花牌", "第三部 丑角牌", "第四部 方块牌", "第五部 红心牌"}

old = [json.load(open(os.path.join(SRC, f"{i}.json"), encoding="utf-8")) for i in range(107)]

# 剥离部标题页块（4 处：K 牌章尾）
n_strip = 0
for i, ch in enumerate(old):
    if i not in DELETE:
        kept = [b for b in ch['content'] if b.get('value') not in PART_BLOCKS]
        if len(kept) != len(ch['content']):
            n_strip += len(ch['content']) - len(kept)
        ch['content'] = kept

toc = []
files = {}
ch_index = 0
n_del = 0
for i, ch in enumerate(old):
    # 书 part
    for a, b, title in BOOKS:
        if i == a:
            toc.append({"type": "part", "title": title, "level": 0, "index": ch_index})
            break
    # 纸牌五部 part（仅纸牌区间内）
    if 38 <= i < 91:
        for a, b, title in PARTS5:
            if i == a:
                toc.append({"type": "part", "title": title, "level": 1, "index": ch_index})
                break
    if i in DELETE:
        n_del += 1
        continue
    ch['index'] = ch_index
    toc.append({"type": "chapter", "title": ch['title'], "index": ch_index, "level": 1})
    files[ch_index] = ch
    ch_index += 1

print(f"旧章 107 → 新章 {len(files)}（删 {n_del} 目录/封面章，剥 {n_strip} 个部标题页块）| toc {len(toc)}")
for t in toc:
    if t['type'] == 'part':
        print(("  " if t['level'] else "") + t['title'])

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
    "bookId": old_meta.get("bookId") or "46736478a11d",
    "title": old_meta.get("title") or "苏菲的世界（贾德名作系列三部曲）",
    "author": old_meta.get("author") or "乔斯坦·贾德",
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
