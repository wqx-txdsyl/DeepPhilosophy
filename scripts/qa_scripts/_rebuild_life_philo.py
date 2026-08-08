# -*- coding: utf-8 -*-
"""哲学与人生 (傅佩荣) epub 重建 (2026-08-08) — 整本单章(第 1 段/27008字) 拆为 3 章 + 小节 section
源: F:/philosophy/东方/傅佩荣/哲学与人生 (1).epub → index_split_003.html (唯一正文文件)
结构: 导言(L3) + 三章 (一/二/三) + 每章内 (一)~(二十四) 小节 → 3 章 + 小节 section
L134-136 署名(林宏华/二ＯＯ八年夏于清心斋) 不入库
用法: python _rebuild_life_philo.py [--write]
"""
import sys, os, re, json, shutil
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"f:\program\Python\PhiAgent\backend\tools")
import rebuild_auto as ra
import zipfile

WRITE = "--write" in sys.argv
EP = r"F:\philosophy\东方\傅佩荣\哲学与人生 (1).epub"
z = zipfile.ZipFile(EP)
h = z.read("index_split_003.html").decode("utf-8", errors="replace")
text = re.sub(r"<[^>]+>", "\n", h)
lines = [l.strip() for l in text.split("\n") if l.strip()]
print(f"共 {len(lines)} 行")

BOOKS = json.load(open(r"f:\program\Python\PhiAgent\app\public\books.json", encoding="utf-8"))
BID = next(b["id"] for b in BOOKS if b["title"] == "哲学与人生")
CH = ra.CH
D = os.path.join(CH, BID)
print("bid:", BID)

# ── 三章边界 (行号, 半开) ──
CH_SECTIONS = [
    ("一、哲学是什么？认识哲学。", 3, 44),     # L3 导言并入
    ("二、人是什么？认识你自己。", 44, 110),
    ("三、哲学引领你通往幸福快乐的人生。", 110, 134),  # L134 起署名不入库
]
SEC_RE = re.compile(r"^（([一二三四五六七八九十]+)）")

chapters = []
for title, lo, hi in CH_SECTIONS:
    paras, sec_marks = [], []
    for i in range(lo, hi):
        s = lines[i]
        if i == lo:
            continue  # 章标题行跳过 (已作 chapter title)
        m = SEC_RE.match(s)
        if m:
            # 小节标题行: 截取标题 (去掉句号/引号), 保留内容于段落
            sec_marks.append((len(paras), s))
            t = s.rstrip("。；；,，")
            paras.append(t)   # 标题行本身作为段落首 (内容少时含正文)
            continue
        paras.append(s)
    chapters.append({"title": title, "paras": paras, "secs": sec_marks, "page": lo})
    n = sum(len(x) for x in paras)
    print(f"  {title[:24]:<28} L{lo}-{hi} 段{len(paras)} 字{n} 小节{len(sec_marks)}")

# ── 校验 ──
print("\n=== 校验 ===")
for c in chapters:
    if not c["paras"]:
        print(f"  空章: {c['title']}")
        continue
    first, last = c["paras"][0], c["paras"][-1]
    if not re.match(r"^[\u4e00-\u9fff（《\"“0-9]", first[:1]):
        print(f"  首段异常开头: [{c['title'][:14]}] {first[:30]}")
    if last and last[-1] not in "。！？；…\"”)]）】·}":
        print(f"  尾段无句末标点: [{c['title'][:14]}] …{last[-35:]}")

# ── 写入 ──
if WRITE:
    BAK = os.path.join(CH, "_rebuild_bak", f"{BID}_v1")
    os.makedirs(BAK, exist_ok=True)
    if not os.listdir(BAK):
        for f in sorted(os.listdir(D)):
            shutil.copy2(os.path.join(D, f), os.path.join(BAK, f))
    for f in os.listdir(D):
        if f.endswith(".json") and f != "meta.json":
            os.remove(os.path.join(D, f))
    meta = {"bookId": BID, "title": "哲学与人生", "author": "傅佩荣",
            "toc": [], "cover": None, "chapterCount": len(chapters), "chapterTitles": []}
    for i, c in enumerate(chapters):
        fp = os.path.join(D, f"{i}.json")
        content = [{"type": "text", "value": x} for x in c["paras"]]
        json.dump({"title": c["title"], "content": content, "index": i},
                  open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        meta["toc"].append({"type": "chapter", "title": c["title"], "index": i, "level": 1})
        meta["chapterTitles"].append(c["title"])
        for sec_idx, (para_idx, s) in enumerate(c["secs"]):
            t = s.rstrip("。；；,，").rstrip("。；")
            meta["toc"].append({"type": "section", "title": t, "index": i, "sec": para_idx, "level": 2})
    json.dump(meta, open(os.path.join(D, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n写入完成: {len(chapters)} 章, toc {len(meta['toc'])} 条")
    ra.sync_three(BID)
    print("sync_three 完成")
