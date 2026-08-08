# -*- coding: utf-8 -*-
"""全库复扫 (2026-08-08): 逐本验证 toc/文件/内容一致性, 标记问题书
检查项:
  A. toc 条目数与章节文件数一致, index 连续 0..N-1
  B. part 条目 index 对齐其下第一章; chapterCount == chapter 数
  C. 章非空 (text 段 >= 1)
  D. 章尾段 == 任一 toc 标题 norm (标题行污染, != 本章标题)
  E. 章首段 == 本章标题 norm (重复标题首段)
用法: python _rescan_all.py
"""
import sys, os, re, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CH = r"f:\program\Python\PhiAgent\backend\data\book_chapters"
BOOKS = json.load(open(r"f:\program\Python\PhiAgent\app\public\books.json", encoding="utf-8"))

def norm(s):
    return re.sub(r"\s+", "", s or "")

titles = {b["id"]: b["title"] for b in BOOKS}
flags = []
ndir = sorted(d for d in os.listdir(CH) if os.path.isdir(os.path.join(CH, d)) and not d.startswith("_"))
print(f"共 {len(ndir)} 本书目录\n")

for bid in ndir:
    D = os.path.join(CH, bid)
    mf = os.path.join(D, "meta.json")
    if not os.path.exists(mf):
        flags.append(f"{bid} 缺 meta.json")
        continue
    meta = json.load(open(mf, encoding="utf-8"))
    name = titles.get(bid, bid)
    toc = meta["toc"]
    if isinstance(toc, dict):
        toc = [t for i, t in sorted(toc.items(), key=lambda kv: int(kv[0]))]
    if not toc or not isinstance(toc[0], dict):
        flags.append(f"{name} ({bid}) :: toc 字符串列表（OCR 重建中）")
        continue
    files = sorted(int(f[:-5]) for f in os.listdir(D) if f.endswith(".json") and f != "meta.json")
    marks = []
    chaps = [t for t in toc if t.get("type") == "chapter"]
    n_chap = len(chaps)
    # A. 文件数 vs chapter 数 (part/section 无文件), chapter index 连续 0..N-1
    if len(files) != n_chap:
        marks.append(f"文件{len(files)}!=章{n_chap}(toc{len(toc)})")
    if files != list(range(len(files))):
        marks.append(f"文件index不连续 {files[:3]}...")
    chidx = [t["index"] for t in chaps]
    if chidx != list(range(len(chidx))):
        marks.append(f"chapter index不连续 {chidx[:5]}...")
    # B. part 对齐 + chapterCount
    if meta.get("chapterCount") != n_chap:
        marks.append(f"chapterCount={meta.get('chapterCount')}!={n_chap}")
    for i, t in enumerate(toc):
        if t.get("type") == "part":
            nxt = toc[i+1]["index"] if i + 1 < len(toc) else len(toc)
            if t["index"] != nxt:
                marks.append(f"part[{t['title'][:8]}]index={t['index']}!=下一章{nxt}")
            if t.get("level") != 0:
                marks.append(f"part level={t.get('level')}")
    # C/D/E. 逐章检查
    n_empty = n_tail = n_head = 0
    all_titles = {norm(t["title"]) for t in toc}
    for idx in files:
        try:
            ch = json.load(open(os.path.join(D, f"{idx}.json"), encoding="utf-8"))
        except Exception:
            marks.append(f"#{idx} JSON损坏")
            continue
        vals = [x["value"] for x in ch["content"] if isinstance(x, dict) and x.get("type") == "text"]
        if not vals:
            n_empty += 1
            continue
        nt = norm(ch["title"])
        last, first = norm(vals[-1]), norm(vals[0])
        if last and last in all_titles and last != nt:
            n_tail += 1
        if first and first == nt and len(vals) > 1:
            n_head += 1
    if n_empty: marks.append(f"{n_empty}空章")
    if n_tail: marks.append(f"{n_tail}章尾标题污染")
    if n_head: marks.append(f"{n_head}章首重复标题")
    if marks:
        flags.append(f"{name[:22]:22s} ({bid}) :: " + " | ".join(marks))

print(f"═══ 标记 {len(flags)} 本 ═══")
for f in flags:
    print(" ", f)
