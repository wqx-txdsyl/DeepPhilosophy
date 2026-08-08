# -*- coding: utf-8 -*-
"""临时: 抽查 section 锚点 → 目标块内容 + 前后文"""
import json, sys

sys.stdout.reconfigure(encoding="utf-8")
DIR = r"f:/program/Python/PhiAgent/backend/data/book_chapters/8c0c6955c793"
meta = json.load(open(f"{DIR}/meta.json", encoding="utf-8"))
chs = {}
for i in range(meta["chapterCount"]):
    d = json.load(open(f"{DIR}/{i}.json", encoding="utf-8"))
    chs[i] = d

# 关键抽查点: (章索引, 节标题)
SPOTS = [
    (5, "Ⅰ.纯粹知识和经验性知识的区别"),
    (5, "Ⅶ.在纯粹理性批判名下的一门特殊科学的理念和划分"),
    (6, "第一节空间"),
    (6, "先验感性论的结论"),
    (9, "导言"),
    (9, "先验辩证论附录"),
    (11, "第一节纯粹理性在独断运用中的训练"),
    (11, "第二节对纯粹理性在其论争上的运用的训练"),
    (12, "第一节我们理性的纯粹运用之最后目的"),
    (12, "第三节意见、知识和信念"),
]
for ci, sec_title in SPOTS:
    ch = chs[ci]
    sec = next(t for t in meta["toc"] if t.get("type") == "section" and t["title"] == sec_title and t["index"] == ci)
    at = sec["sec"]
    blocks = ch["content"]
    prev = blocks[at - 1]["value"][-25:] if at > 0 else "(无前块)"
    cur = blocks[at]["value"][:50]
    nxt = blocks[at + 1]["value"][:35] if at + 1 < len(blocks) else "(无后块)"
    print(f"== [{ch['title']}] {sec_title} @块{at} ({len(blocks)}块)")
    print(f"  前: …{prev!r}")
    print(f"  本: {cur!r}")
    print(f"  后: {nxt!r}")
    print()
