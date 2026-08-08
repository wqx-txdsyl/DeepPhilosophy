# -*- coding: utf-8 -*-
"""尼采文集（尼采著作集九册）bedc9c78dfdf 修复（一次性，9 书拼合 = 9 part）
旧数据 616 章 = 9 本书平铺（无书级），每本含版权页/目录前置页章。
修复: 删 20 个前置页章（版权页/总目录/目录）+ toc 加 9 个 part + 重编号
九册: 查拉图斯特拉如是说(注释本)/悲剧的诞生(注释本)/权力意志(科利版)/
      快乐的科学(注释本)/曙光(朝霞)/偶像的黄昏/瓦格纳事件·尼采反瓦格纳/
      论道德的谱系/不合时宜的沉思
正文内容不动（171 万字完整），只改结构
用法: python _xr_nietzchewenji_rebuild.py [--dry]
"""
import json, os, sys, shutil

SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters/bedc9c78dfdf"
DST = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/bedc9c78dfdf"

# 前置页章（原始 index）——版权页/总目录/目录
DELETE = {0, 1, 2, 3, 14, 15, 51, 53, 60, 64, 515, 518, 524, 528, 540, 542, 563, 567, 572, 573}
# 九册边界（原始 index 左闭右开）
PARTS = [
    (0, 14, "查拉图斯特拉如是说（注释本）"),
    (14, 51, "悲剧的诞生（注释本）"),
    (51, 60, "权力意志（科利版）"),
    (60, 515, "快乐的科学（注释本）"),
    (515, 524, "曙光（朝霞）"),
    (524, 540, "偶像的黄昏"),
    (540, 563, "瓦格纳事件·尼采反瓦格纳（注释本）"),
    (563, 572, "论道德的谱系"),
    (572, 616, "不合时宜的沉思"),
]

# 读取全部旧章
old = []
for i in range(616):
    old.append(json.load(open(os.path.join(SRC, f"{i}.json"), encoding="utf-8")))

toc = []
files = {}
ch_index = 0
n_del = 0
for i, ch in enumerate(old):
    # part 边界必须先挂（9 个边界恰好都是待删的每书首章前置页）
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

print(f"旧章 616 → 新章 {len(files)}（删 {n_del} 个前置页）| toc {len(toc)} = {9} part + {len(files)} chapter")
print("part 序列:")
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
    "bookId": old_meta.get("bookId") or "bedc9c78dfdf",
    "title": old_meta.get("title") or "尼采文集",
    "author": old_meta.get("author") or "弗里德里希·尼采",
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
