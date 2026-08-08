# -*- coding: utf-8 -*-
"""判断力批判独立本 f08c1ead3164 最终清理（元数据修正，内容不动）
PDF OCR 入库（dp_pdf_import.py），章节结构已完整（2 part + 11 chapter + 113 section），
缺陷: ① 两个"第一章"重名（审美/目的论分析论）——目的论部分实为卷级
      ② section.sec 是页面偏移非序号（1,10,24,34…跳号；180/189 等乱序）
      ③ 附录方法论 chapter 下重复 section（sec=0, 标题=章标题）
      ④ book_detail 双端与 meta 脱节（cc=10 旧 toc）
修法:
  ① chapter 改名: 第一章 审美判断力的分析论→第一卷 审美判断力的分析论; 第二章 审美判断力的辩证论→第二卷 审美判断力的辩证论;
                  第一章 目的论判断力的分析论→第一卷 目的论判断力的分析论; 第二章 目的论判断力的辩证论→第二卷 目的论判断力的辩证论
  ② section.sec 每章内重排 1..n 连续（按 toc 出现顺序）
  ③ 删重复 section（标题 == 所属章标题）
  ④ book_detail 双端覆盖 toc/chapterCount/chapterTitles
  ⑤ books.json 该书 chapterCount 更新
用法: python _xr_panduanli_clean.py [--dry]
"""
import json, os, sys, shutil

BID = "f08c1ead3164"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"

RENAME = {
    "第一章 审美判断力的分析论": "第一卷 审美判断力的分析论",
    "第二章 审美判断力的辩证论": "第二卷 审美判断力的辩证论",
    "第一章 目的论判断力的分析论": "第一卷 目的论判断力的分析论",
    "第二章 目的论判断力的辩证论": "第二卷 目的论判断力的辩证论",
}

meta = json.load(open(os.path.join(SRC, "meta.json"), encoding="utf-8"))
old_toc = meta["toc"]

new_toc = []
sec_seq = {}
dropped_dup = []
for tt in old_toc:
    if tt["type"] == "chapter":
        t2 = dict(tt)
        if tt["title"] in RENAME:
            t2["title"] = RENAME[tt["title"]]
        new_toc.append(t2)
    elif tt["type"] == "section":
        # 所属章 index 连续区段内计数
        if tt["title"] == new_toc[-1]["title"] and new_toc[-1]["type"] == "chapter":
            dropped_dup.append(tt["title"])
            continue
        idx = tt["index"]
        sec_seq[idx] = sec_seq.get(idx, 0) + 1
        t2 = dict(tt)
        t2["sec"] = sec_seq[idx]
        new_toc.append(t2)
    else:
        new_toc.append(dict(tt))

# 章标题文件同步
for idx, ch_name in enumerate(meta.get("chapterTitles", [])):
    if ch_name in RENAME:
        p = os.path.join(SRC, f"{idx}.json")
        ch = json.load(open(p, encoding="utf-8"))
        ch["title"] = RENAME[ch_name]
        if not sys.argv.count("--dry"):
            json.dump(ch, open(p, "w", encoding="utf-8"), ensure_ascii=False)

meta["toc"] = new_toc
meta["chapterTitles"] = [RENAME.get(t, t) for t in meta.get("chapterTitles", [])]

print(f"toc: {len(old_toc)} → {len(new_toc)}（删重复 section {len(dropped_dup)}）")
for d in dropped_dup:
    print(f"  删重复: {d!r}")
for tt in new_toc:
    ind = "  " * tt.get("level", 1)
    print(f"{ind}[{tt['type']} {tt.get('sec','')}] {tt['title'][:52]}")
print("\n章节文件:")
for i, t in enumerate(meta["chapterTitles"]):
    print(f"  {i}. {t}")

if "--dry" in sys.argv:
    sys.exit(0)

json.dump(meta, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print("✓ meta.json 写入")
shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
print("✓ 同步 DP")

# book_detail 双端覆盖
for p in (
    f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json",
    f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json",
):
    d = json.load(open(p, encoding="utf-8"))
    d["toc"] = meta["toc"]
    d["chapterCount"] = meta["chapterCount"]
    d["chapterTitles"] = meta["chapterTitles"]
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"✓ book_detail 同步: {p.split('Python')[-1][:20]} cc={d['chapterCount']}")

# books.json 该书 chapterCount
bp = r"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"
books = json.load(open(bp, encoding="utf-8"))
n = 0
for b in books:
    if b.get("title") == "判断力批判" and b.get("author") == "伊曼努尔·康德":
        b["chapterCount"] = meta["chapterCount"]
        b["bookId"] = BID  # 字段缺失补上
        n += 1
json.dump(books, open(bp, "w", encoding="utf-8"), ensure_ascii=False)
print(f"✓ books.json 更新 {n} 条")
