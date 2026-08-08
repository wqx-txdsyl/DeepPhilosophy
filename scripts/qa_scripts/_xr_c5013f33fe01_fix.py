# -*- coding: utf-8 -*-
"""存在与时间（c5013f33fe01）抽查1修复：删除假章节 '如何阅读本书'（=epub Chapter_1 重复内容）
病因: epub 自动切章把封面+导论第一章开头切成 Chapter_1（toc 误标 '如何阅读本书'），
  与 Chapter_2（导论完整版）90% 重复——epub 源 toc 仅 13 项（书名+Chapter_1~12），无导读篇。
验证: 章0 段与章1 全部 1.00 相似（'第一章存在问题的必要性'/'第一节…'），末段为导论中间——
  章0 ⊂ 章1，删除无损失。
修复: 删 0.json（Chapter_1）→ 原 1-13 → 0-12；toc 重排（part 导论 index 0 / 第一篇 index 1 /
  第二篇 index 7）；chapterCount 14→13；section 的 index 章号 -1、sec 段索引不变。
"""
import json, os, re, sys, shutil

BID = "c5013f33fe01"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DST2 = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

meta0 = json.load(open(os.path.join(SRC, "meta.json"), encoding="utf-8"))
assert meta0["chapterCount"] == 14
chs = [json.load(open(os.path.join(SRC, f"{i}.json"), encoding="utf-8")) for i in range(14)]
# 章0 确认是 Chapter_1 重复
assert chs[0]["title"] == "Chapter_1", chs[0]["title"]
print(f"旧: {meta0['chapterCount']} 章, 章0 = {chs[0]['title']!r} ({len(chs[0]['content'])}段) 待删")
print("toc 项数:", len(meta0["toc"]))

# 1-13 → 0-12
new_chs = []
for i, c in enumerate(chs[1:]):
    c = dict(c)
    c["index"] = i
    new_chs.append(c)
print(f"新: {len(new_chs)} 章（原 1-13 重排为 0-12）")

# toc 重排: part index 平移 -1; section index -1, sec 不变
new_toc = []
for t in meta0["toc"]:
    if t.get("type") == "part":
        t = dict(t)
        t["index"] = t["index"] - 1
        new_toc.append(t)
    elif t.get("type") == "section":
        t = dict(t)
        t["index"] = t["index"] - 1
        new_toc.append(t)
    else:
        if t["index"] == 0:
            continue  # 删 '如何阅读本书' 章项
        t = dict(t)
        t["index"] = t["index"] - 1
        new_toc.append(t)
print(f"新 toc 项数: {len(new_toc)}")
for t in new_toc:
    print(f"  {t['type']:8s} idx{t['index']:2d} {t['title'][:36]}")

# 章节标题列表（toc 里 chapter 项标题）
new_titles = [t["title"] for t in new_toc if t["type"] == "chapter"]
print("新 chapterTitles:", len(new_titles))

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
for c in new_chs:
    json.dump({"index": c["index"], "title": c["title"], "content": c["content"]},
              open(os.path.join(SRC, f"{c['index']}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
meta = {"bookId": BID, "title": "存在与时间", "author": "马丁·海德格尔",
        "toc": new_toc, "cover": None, "chapterCount": len(new_chs),
        "chapterTitles": new_titles}
json.dump(meta, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print(f"✓ 写入 {SRC}: {len(new_chs)} 章 + meta.json")

shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
print("✓ 同步 DP backend chapters")
shutil.rmtree(DST2, ignore_errors=True)
shutil.copytree(SRC, DST2)
print("✓ 同步 DP app/public chapters")

for p in (DETAIL_SRC, DETAIL_DST):
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))
        d["toc"] = new_toc
        d["chapterCount"] = len(new_chs)
        d["chapterTitles"] = new_titles
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
        print(f"✓ book_detail 更新: {p}")

if os.path.exists(BOOKS_JSON):
    bj = json.load(open(BOOKS_JSON, encoding="utf-8"))
    bl = bj if isinstance(bj, list) else bj.get("books", [])
    hit = False
    for b in bl:
        if b.get("id") == BID:
            b["chapterCount"] = len(new_chs)
            hit = True
    if hit:
        with open(BOOKS_JSON, "w", encoding="utf-8") as f:
            json.dump(bl if isinstance(bj, list) else {**bj, "books": bl}, f,
                      ensure_ascii=False, indent=None)
        print("✓ books.json chapterCount 更新")
    else:
        print("⚠ books.json 未找到该书")
