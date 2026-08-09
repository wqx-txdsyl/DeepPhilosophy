# -*- coding: utf-8 -*-
"""抽查19 v3（最终版）：工具论（b471f41a78de）篇/卷分级——只降级 toc，文件不合并
用户指示: "篇就是chapter级的，但chapter之下不是还有一个级别吗，那个级别放卷" + "文件内容不必合并，只是降级而已"
结构（文件 0-15 原样不动，index 直接映射文件号）:
  chapter(7 篇):  序 idx0 / 范畴篇 idx1 / 解释篇 idx2 / 前分析篇 idx3(第一卷)
                   后分析篇 idx5(第一卷) / 论题篇 idx7(第一卷) / 辩谬篇 idx15
  section(12 卷): 前分析篇第一卷 idx3 第二卷 idx4 / 后分析篇第一卷 idx5 第二卷 idx6
                   论题篇第一卷 idx7 ~ 第八卷 idx14  (sec=0 滚到卷首块)
chapterCount 保持 16（textChapters 数组长度须 ≥ 最大 index+1，卷文件仍按 idx 加载）
用法: python _xr_ck19_toolun_v3.py
"""
import json

bid = "b471f41a78de"
META = [
    f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{bid}/meta.json",
    f"f:/program/Python/PhiAgent/backend/data/book_chapters/{bid}/meta.json",
    f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters/{bid}/meta.json",
]
DETAIL = [
    f"f:/program/Python/PhiAgent/app/public/book_detail/{bid}.json",
    f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{bid}.json",
]

# 7 篇 → (title, 挂卷文件号列表)
CHAPTERS = [("序", [0]), ("范畴篇", [1]), ("解释篇", [2]),
            ("前分析篇", [3, 4]), ("后分析篇", [5, 6]),
            ("论题篇", [7, 8, 9, 10, 11, 12, 13, 14]), ("辩谬篇", [15])]
VOLNAMES = ["第一卷", "第二卷", "第三卷", "第四卷", "第五卷", "第六卷", "第七卷", "第八卷"]

toc = []
for cname, files in CHAPTERS:
    toc.append({"type": "chapter", "title": cname, "index": files[0]})
    if len(files) > 1:
        for i, fidx in enumerate(files):
            toc.append({"type": "section", "title": f"{cname}{VOLNAMES[i]}",
                        "index": fidx, "level": 1, "sec": 0})

# 校验: 所有 index 在 0-15 内（chapter 与首卷 section 同指一文件是设计如此）
all_idx = [t["index"] for t in toc]
assert all(0 <= i <= 15 for i in all_idx), all_idx

for p in META:
    m = json.load(open(p, encoding="utf-8"))
    m["toc"] = toc
    json.dump(m, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
    print(f"✓ meta toc 降级: {p.split('book_chapters')[0].split('/')[-2] or p}")
for p in DETAIL:
    d = json.load(open(p, encoding="utf-8"))
    d["toc"] = toc
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
    print(f"✓ detail toc 降级: {p}")

print("\n结构:")
for t in toc:
    print(f"  {t['type']:<8} idx={t['index']:<2} {t['title']}")
print("✓ chapterCount/chapterTitles/books.json 不动（仍 16，文件不合并）")
