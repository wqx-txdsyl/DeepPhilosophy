# -*- coding: utf-8 -*-
"""抽查19 v2：工具论（b471f41a78de）篇/卷分级（用户澄清：篇=chapter，卷=section）
原方案 7part+16chapter 错误（把篇当 part）→ 改 chapter(篇)+section(卷) 两级：
  chapter 序 / 范畴篇 / 解释篇 / 前分析篇 / 后分析篇 / 论题篇 / 辩谬篇（7 文件）
  section 前分析篇第一~二卷 / 后分析篇第一~二卷 / 论题篇第一~八卷（12 个，挂父章 idx）
内容合并: 卷文件内容并入父篇文件，每卷开头插卷标题锚点块（'前分析篇第一卷'）
toc: chapter idx0-6 + section lv1（index=父章 index）；旧 7-15.json 删除
同步: meta 三处 + detail 双端 + books.json
用法: python _xr_ck19_toolun_v2.py
"""
import json, os, shutil

bid = "b471f41a78de"
CHAP = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{bid}"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{bid}"
DST2 = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters/{bid}"
DA = "f:/program/Python/PhiAgent/app/public/book_detail"
DB = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail"
BOOKS = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

def load(p): return json.load(open(p, encoding="utf-8"))
def save(p, d): json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)

# 旧 16 文件：0 序 1 范畴篇 2 解释篇 3-4 前分析篇卷1/2 5-6 后分析篇卷1/2 7-14 论题篇卷1-8 15 辩谬篇
STAR = [(3, 4), (5, 6), (7, 14)]          # (旧首文件, 旧尾文件) 合并组
VOLS = [("前分析篇", "第一卷", "第二卷"),
        ("后分析篇", "第一卷", "第二卷"),
        ("论题篇", "第一卷", "第二卷", "第三卷", "第四卷", "第五卷", "第六卷", "第七卷", "第八卷")]
KEEP = {0, 1, 2, 15}                       # 不动文件

# 备份旧 toc
m0 = load(f"{CHAP}/meta.json")
save(f"{CHAP}/meta.json.bak_ck19", m0)

# 读旧文件
def rd(i): return load(f"{CHAP}/{i}.json")

# 构建新文件 3/4/5（新序），6 = 旧15；每卷开头插卷标题锚点块（'前分析篇第一卷'）
new_files = {}
for out_idx, ((p0, p1), vols) in enumerate(zip(STAR, VOLS), start=3):
    body = []
    for off, v in enumerate(vols):
        old = rd(p0 + off)
        body.append({"type": "text", "value": old["title"]})   # 卷标题锚点块
        body += old["content"]
    title = rd(p0)["title"]
    for v in ("第一卷", "第二卷", "第三卷", "第四卷", "第五卷", "第六卷", "第七卷", "第八卷"):
        title = title.replace(v, "")
    new_files[out_idx] = {"index": out_idx, "title": title, "content": body}
# 辩谬篇 6 = 旧15
old15 = rd(15)
new_files[6] = {"index": 6, "title": "辩谬篇", "content": old15["content"]}

# 写入 0-6（DP backend）
for i in range(7):
    json.dump(load(f"{CHAP}/{i}.json"), open(f"{CHAP}/{i}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=None)
for i, c in new_files.items():
    json.dump(c, open(f"{CHAP}/{i}.json", "w", encoding="utf-8"), ensure_ascii=False, indent=None)
# 删除旧 7-14（三处）
for i in range(7, 15):
    for d in (CHAP, SRC, DST2):
        p = f"{d}/{i}.json"
        if os.path.isfile(p):
            os.remove(p)
print("✓ 文件合并: 3=前分析篇(2卷) 4=后分析篇(2卷) 5=论题篇(8卷) 6=辩谬篇；旧 7-14 三处删除")

# toc: 7 chapter + 12 section
toc = []
chapters = ["序", "范畴篇", "解释篇", "前分析篇", "后分析篇", "论题篇", "辩谬篇"]
for ci, t in enumerate(chapters):
    toc.append({"type": "chapter", "title": t, "index": ci})
for ci, vols in ((3, VOLS[0]), (4, VOLS[1]), (5, VOLS[2])):
    for v in vols:
        toc.append({"type": "section", "title": f"{chapters[ci]}{v}", "index": ci, "level": 1})
m = load(f"{CHAP}/meta.json")
m["toc"] = toc
m["chapterCount"] = 7
m["chapterTitles"] = chapters
save(f"{CHAP}/meta.json", m)
print("✓ toc: 7 chapter + 12 section")

# ---- 同步三处 + detail 双端 + books.json ----
for p in (f"{SRC}/meta.json", f"{DST2}/meta.json"):
    save(p, m)
for i in range(7):
    c = load(f"{CHAP}/{i}.json")
    for p in (f"{SRC}/{i}.json", f"{DST2}/{i}.json"):
        save(p, c)
for p in (f"{DA}/{bid}.json", f"{DB}/{bid}.json"):
    d = load(p)
    d["toc"] = toc
    d["chapterCount"] = 7
    d["chapterTitles"] = chapters
    save(p, d)
books = load(BOOKS)
for x in books:
    if str(x.get("id")) == bid:
        x["chapterCount"] = 7
save(BOOKS, books)
print("✓ 同步: meta×3 + 文件×3 + detail×2 + books.json (cc=7)")
