# -*- coding: utf-8 -*-
"""自然辩证法 aa21ac425e87 修复后四步同步验证"""
import json, hashlib, os

BID = "aa21ac425e87"
DET_DA = f"f:/program/Python/PhiAgent/app/public/book_detail/{BID}.json"
DET_DB = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
CH_DA = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
CH_DB = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
CH_DB2 = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters/{BID}"
BOOKS = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"
BOOKS2 = "f:/program/Python/PhiAgent/app/public/books.json"

def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()[:8]

print("=== ① detail 双端 md5 ===")
m1, m2 = md5(DET_DA), md5(DET_DB)
print(f"  PhiAgent {m1} | DP {m2}  {'✓ 一致' if m1 == m2 else '✗ 不一致!'}")

print("=== ② chapterCount 一致性 ===")
d = json.load(open(DET_DA, encoding="utf-8"))
cc_detail = d["chapterCount"]
for p in (BOOKS, BOOKS2):
    books = json.load(open(p, encoding="utf-8"))
    for x in books:
        if str(x.get("id")) == BID:
            print(f"  {os.path.basename(os.path.dirname(p))}/books.json cc={x['chapterCount']} vs detail cc={cc_detail}  {'✓' if x['chapterCount'] == cc_detail else '✗ 不一致!'}")

print("=== ③ chapter meta 三处 md5 ===")
for p in (CH_DA, CH_DB, CH_DB2):
    m = md5(os.path.join(p, "meta.json"))
    cc = json.load(open(os.path.join(p, "meta.json"), encoding="utf-8"))["chapterCount"]
    print(f"  {os.path.relpath(p, 'f:/')} meta {m} cc={cc}")
m1 = md5(os.path.join(CH_DA, "meta.json")); m2 = md5(os.path.join(CH_DB, "meta.json")); m3 = md5(os.path.join(CH_DB2, "meta.json"))
print(f"  三处一致: {'✓' if m1 == m2 == m3 else '✗ 不一致!'}")

print("=== ④ toc index 集合 == 章节文件 ===")
meta = json.load(open(os.path.join(CH_DB, "meta.json"), encoding="utf-8"))
toc_idx = set(t["index"] for t in meta["toc"])
files = {int(f.split(".")[0]) for f in os.listdir(CH_DB) if f.endswith(".json") and f != "meta.json"}
print(f"  toc index {sorted(toc_idx)}")
print(f"  文件编号  {sorted(files)}")
print(f"  集合相等: {'✓' if toc_idx == files else '✗ 不一致!'}")
for i in sorted(toc_idx):
    if i >= cc_detail:
        print(f"  ✗ index {i} >= chapterCount {cc_detail}（阅读器越界风险!）")
print("  index 全部 < chapterCount: ✓" if all(i < cc_detail for i in toc_idx) else "  有越界!")

print("=== 章节文件完整性抽查（33/34/35 资料章 + 章3 导言）===")
for i in (0, 3, 33, 34, 35):
    c = json.load(open(os.path.join(CH_DB, f"{i}.json"), encoding="utf-8"))
    n = sum(len(b["value"]) for b in c["content"])
    print(f"  [{i}] {c['title'][:24]} {n}字 {len(c['content'])}段")
