# -*- coding: utf-8 -*-
"""#176 罪与罚（陀思妥耶夫斯基）aa614e2cf92d 修复
病因（CHKLIST ✗B 部级未拆）:
  41 章平铺（第一部 第一章~尾声 第二章），"第X部 第X章"合并为章标题，
  无部级层级。
源（F:/philosophy/西方/费奥多尔·陀思妥耶夫斯基/罪与罚.pdf，无 epub）。
修复:
  章节内容不动（41 章内容完整：章首序号+正文、[N] 脚注块保留章尾），
  toc 插入 7 个 part（#144 模式，part.index=其下首章 index）：
  part 第一部 idx0（第一~七章）｜part 第二部 idx7（7 章）｜part 第三部 idx14（6）
  ｜part 第四部 idx20（6）｜part 第五部 idx26（5）｜part 第六部 idx31（8）
  ｜part 尾声 idx39（2）；cc 41 不变；book_detail 双端+books.json 同步。
用法: python _xr_zyf_rebuild.py [--dry]
"""
import json, os, re, sys, shutil

BID = "aa614e2cf92d"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

# part 标题 → 其下首章 index（41 章 = 7+7+6+6+5+8+2）
PARTS = [
    (0, "第一部"), (7, "第二部"), (14, "第三部"), (20, "第四部"),
    (26, "第五部"), (31, "第六部"), (39, "尾声"),
]

# ---- 读现有 toc ----
m = json.load(open(os.path.join(SRC, "meta.json"), encoding="utf-8"))
toc = m["toc"]
assert len(toc) == 41 and all(t["type"] == "chapter" for t in toc), f"toc 异常: {len(toc)}"

def norm(s):
    return re.sub(r"\s+", "", s or "")

# 校验每部边界与章标题一致
for idx, title in PARTS:
    expect = f"{title} 第一章"
    got = toc[idx]["title"]
    if not got.startswith(expect.replace("部 第一章", "部 第一章")):
        print(f"⚠ part {title} 首章标题 {got!r}（期望 {expect!r}）")
    else:
        print(f"✓ {title}: 首章 {got!r}（idx{idx}）")
# 末章核对
last = toc[-1]["title"]
print(f"✓ 末章: {last!r}")
assert last == "尾声 第二章", last

# ---- 插入 part ----
new_toc = []
pit = iter(PARTS)
next_part = next(pit, None)
for t in toc:
    if next_part and t["type"] == "chapter" and t["index"] == next_part[0]:
        new_toc.append({"type": "part", "title": next_part[1], "index": next_part[0], "level": 0})
        next_part = next(pit, None)
    new_toc.append(t)
toc = new_toc

print("\n=== 新 toc（part 位置）===")
for t in toc:
    if t["type"] == "part":
        print(f"  part  idx{t['index']} lv0 {t['title']}")
print(f"toc 项: {len(toc)}（41 章 + 7 part）")
assert len(toc) == 48

if "--dry" in sys.argv:
    sys.exit(0)

# ---- 写入 ----
m["toc"] = toc
json.dump(m, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print("✓ 写入 meta (PhiAgent)")
shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
print("✓ 同步 DP chapters")

for p in (DETAIL_SRC, DETAIL_DST):
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))
        d["toc"] = toc
        d["chapterCount"] = 41
        d["chapterTitles"] = m.get("chapterTitles", [t["title"] for t in toc if t["type"] == "chapter"])
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
        print(f"✓ book_detail 更新: {p}")

if os.path.exists(BOOKS_JSON):
    bj = json.load(open(BOOKS_JSON, encoding="utf-8"))
    bl = bj if isinstance(bj, list) else bj.get("books", [])
    hit = False
    for b in bl:
        if b.get("id") == BID:
            b["chapterCount"] = 41
            hit = True
    if hit:
        with open(BOOKS_JSON, "w", encoding="utf-8") as f:
            json.dump(bl if isinstance(bj, list) else {**bj, "books": bl}, f,
                      ensure_ascii=False, indent=None)
        print("✓ books.json chapterCount 更新")
    else:
        print("⚠ books.json 未找到该书")
