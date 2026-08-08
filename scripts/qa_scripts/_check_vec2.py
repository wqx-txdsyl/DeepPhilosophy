# -*- coding: utf-8 -*-
"""向量库现状: index.json 结构/条目/尼采与哲学条数/重建书条数"""
import sys, os, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
OUT = r"f:/program/Python/PhiAgent/backend/data/embeddings"
ix_fp = os.path.join(OUT, "index.json")
print("index.json 存在:", os.path.exists(ix_fp))
if not os.path.exists(ix_fp):
    sys.exit(0)
idx = json.load(open(ix_fp, encoding="utf-8"))
print("类型:", type(idx).__name__)
if isinstance(idx, list):
    print("总条数:", len(idx))
    print("样例:", json.dumps(idx[:2], ensure_ascii=False)[:400])
elif isinstance(idx, dict):
    print("总条数:", len(idx))
    keys = list(idx)[:3]
    print("样例:", {k: idx[k] for k in keys})
# 尼采与哲学 + 最近重建书
CH = r"f:/program/Python/PhiAgent/backend/data/book_chapters"
tgt = {"e7c27b39a87c": "尼采与哲学", "5bdec4dbde50": "历史与阶级意识", "81218d6e1646": "走出唯一真理观",
       "efdfdda23776": "民主主义与教育", "e74dc59d508e": "柏拉图作品集", "e863b4cca50d": "增广贤文",
       "a8f6e375ccef": "哲学与人生", "274c59617693": "存在与虚无"}
def bid_of(e):
    if isinstance(e, dict):
        return str(e.get("bookId") or e.get("bid") or "")
    return ""
from collections import Counter
c = Counter(bid_of(e) for e in idx)
for b, t in tgt.items():
    print(f"  {b} {t}: 向量 {c.get(b, 0)} 条 | 章数", end=" ")
    mfp = os.path.join(CH, b, "meta.json")
    if os.path.exists(mfp):
        print(json.load(open(mfp, encoding="utf-8")).get("chapterCount"))
    else:
        print("?")
