# -*- coding: utf-8 -*-
"""道德经 6ef2f18cfdc9 修复（一次性，道经/德经平铺缺 part + 垃圾页）
旧数据 83 章 = 关于本书/目录 + 81 章（道经·第一~三十七章/德经·第三十八~八十一章），
每章 1 块（标题前缀+正文合体）。
修复:
 1) 删 [0] 关于本书、[1] 目录
 2) 加 2 part(level 0)：道经 [2,39) / 德经 [39,83)
 3) 章标题去"道经·/德经·"前缀 → 第一章~第八十一章
 4) 正文块去"道经·第一章 "等前缀，保留正文
用法: python _xr_daodejing_rebuild.py [--dry]
"""
import json, os, sys, shutil, re

SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters/6ef2f18cfdc9"
DST = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/6ef2f18cfdc9"

DELETE = {0, 1}
PARTS = [
    (2, "道经"),
    (39, "德经"),
]
PREFIX_RE = re.compile(r'^道[经德]·第[一二三四五六七八九十]+章\s*')
TITLE_RE = re.compile(r'^道[经德]·')

old = [json.load(open(os.path.join(SRC, f"{i}.json"), encoding="utf-8")) for i in range(83)]

# 正文块去前缀
for i in range(2, 83):
    for b in old[i]['content']:
        v = b.get('value', '')
        if isinstance(v, str):
            b['value'] = PREFIX_RE.sub('', v, count=1)

toc = []
files = {}
ch_index = 0
n_del = 0
for i, ch in enumerate(old):
    for a, title in PARTS:
        if i == a:
            toc.append({"type": "part", "title": title, "level": 0, "index": ch_index})
    if i in DELETE:
        n_del += 1
        continue
    ch['title'] = TITLE_RE.sub('', ch['title'])
    ch['index'] = ch_index
    toc.append({"type": "chapter", "title": ch['title'], "index": ch_index, "level": 1})
    files[ch_index] = ch
    ch_index += 1

print(f"旧章 83 → 新章 {len(files)}（删 {n_del} 垃圾页）| toc {len(toc)}")
for t in toc:
    if t['type'] == 'part':
        print("  part:", t['title'])
print("示例: [2]", files[2]['title'], "| 首块:", files[2]['content'][0]['value'][:24])

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
    "bookId": old_meta.get("bookId") or "6ef2f18cfdc9",
    "title": old_meta.get("title") or "道德经",
    "author": old_meta.get("author") or "老子",
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
