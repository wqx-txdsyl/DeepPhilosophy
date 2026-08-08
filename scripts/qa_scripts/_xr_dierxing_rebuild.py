# -*- coding: utf-8 -*-
"""第二性（合卷本）62503311b4e3 修复（一次性，部/卷标题缺失 + 神话章被拆两半）
旧数据 34 章 = 两卷四部平铺（第一卷：导言+命运+历史+神话；第二卷：导言+14章+结语+翻译后记）。
问题:
 1) 部/卷标题缺失 → 加 2 卷 part(level 0) + 3 部 part(level 1)
 2) [9] 第一章(神话) 267 块 = 神话章正文+章末注释(1)-(132)，尾部残留"第二章"+引言残块
 3) [16] 第三章 31 块 = 神话章被拆走的题词+中段正文+注释(1)-(7)（与 [9] 零重叠）
    → 合并 [9]+[16] 恢复完整神话章（题词→正文→中段→中段注→章末注）
    → "第二章"+引言残块归入 [10] 一 蒙泰朗 开头
正文内容保全，只改结构
用法: python _xr_dierxing_rebuild.py [--dry]
"""
import json, os, sys, shutil

SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters/62503311b4e3"
DST = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/62503311b4e3"

# 卷/部（原始 index 左闭右开, level）
PARTS = [
    (0, 16, "第一卷　事实与神话", 0),
    (1, 4, "第一部　命运", 1),
    (4, 9, "第二部　历史", 1),
    (9, 16, "第三部　神话", 1),
    (17, 34, "第二卷　实际体验", 0),
]
DEL16 = 16  # 被拆走的中段残章（内容并入 9 后删除）

old = [json.load(open(os.path.join(SRC, f"{i}.json"), encoding="utf-8")) for i in range(34)]
ch9 = old[9]['content']
ch16 = old[16]['content']

# [9] 重建：题词(16:27-30) → 正文(9:0-112) → 中段(16:0-18) → 中段注释(16:19-26) → 章末注释(9:113-264)
new9 = ch16[27:31] + ch9[0:113] + ch16[0:19] + ch16[19:27] + ch9[113:265]
# 残块（第二章标题+引言）→ 并入 [10] 开头
new10 = ch9[265:267] + old[10]['content']
old[9]['content'] = new9
old[10]['content'] = new10
print(f"[9] 神话章重建: {len(ch9)} → {len(new9)} 块（并入题词+中段+中段注释）")
print(f"[10] 开头插入 {len(ch9[265:267])} 个残块（第二章标题+引言）")

toc = []
files = {}
ch_index = 0
for i, ch in enumerate(old):
    if i == DEL16:
        continue
    for a, b, title, lv in PARTS:
        if i == a:
            toc.append({"type": "part", "title": title, "level": lv, "index": ch_index})
            break
    ch['index'] = ch_index
    toc.append({"type": "chapter", "title": ch['title'], "index": ch_index, "level": 1})
    files[ch_index] = ch
    ch_index += 1

print(f"旧章 34 → 新章 {len(files)}（删 [16] 残章）| toc {len(toc)}")
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
    "bookId": old_meta.get("bookId") or "62503311b4e3",
    "title": old_meta.get("title") or "第二性（合卷本）",
    "author": old_meta.get("author") or "西蒙娜·德·波伏瓦",
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
