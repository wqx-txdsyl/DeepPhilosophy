# -*- coding: utf-8 -*-
"""规训与惩罚 960c47f35066 修复（一次性，四部标题缺失 + [4] 重复内容裁剪）
旧数据 12 章 = 四部平铺（酷刑/惩罚/规训/监狱），part 标题缺失。
问题:
 1) [4] "第二章 惩罚的温和方式" 199 块 = 开头 106 块是第一部两章（犯人的肉体 58 块+
    "第二章 断头台的场面"标题+断头台的场面 47 块）的重复 → 裁剪保留 块107-198（93 块正文）
 2) [4] 标题"第二章"→"第一章 惩罚的温和方式"（第二部第一章）
 3) 加 4 部 part（第一部 酷刑/第二部 惩罚/第三部 规训/第四部 监狱）
 4) 删 [0] 封面（学术前沿总序/译者后记保留独立章）
用法: python _xr_guanxun_rebuild.py [--dry]
"""
import json, os, sys, shutil

SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters/960c47f35066"
DST = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/960c47f35066"

# 四部（原始 index 左闭右开）
PARTS = [
    (2, 4, "第一部　酷刑"),
    (4, 5, "第二部　惩罚"),
    (5, 8, "第三部　规训"),
    (8, 11, "第四部　监狱"),
]
DELETE = {0}  # 封面
CUT = 107  # [4] 裁剪点：块 107 起为真实正文（"第一章 普遍的惩罚"）

old = [json.load(open(os.path.join(SRC, f"{i}.json"), encoding="utf-8")) for i in range(12)]

# [4] 裁剪 + 标题修正
ch4 = old[4]
n_before = len(ch4['content'])
ch4['content'] = ch4['content'][CUT:]
ch4['title'] = "第一章　惩罚的温和方式"
print(f"[4] 裁剪: {n_before} → {len(ch4['content'])} 块（删前 {CUT} 块重复）| 标题 → {ch4['title']}")

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

print(f"旧章 12 → 新章 {len(files)}（删 {n_del} 封面）| toc {len(toc)}")
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
    "bookId": old_meta.get("bookId") or "960c47f35066",
    "title": old_meta.get("title") or "规训与惩罚",
    "author": old_meta.get("author") or "米歇尔·福柯",
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
