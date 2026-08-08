# -*- coding: utf-8 -*-
"""哲学书简 (伏尔泰) 文本层全量重建 (2026-08-08) — 整本单章(正文/100561字) 拆为 27 章
源: F:/philosophy/西方/伏尔泰/哲学书简.pdf (136 页, 文本层完整, PDF 目录 27 条)
结构: 引言(p4-8) + 25 封信(p9-115) + 伏尔泰年表(p116-136) → 27 章
边界: PDF 目录页码 (1-based, fitz 索引 = 值-1), 半开区间
段落: 文本层空行切段, 行尾中文+行首中文拼接 (同 _recover_first_chapter)
用法: python _rebuild_voltair_letters.py [--write]
"""
import sys, os, re, json, shutil
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"f:\program\Python\PhiAgent\backend\tools")
import rebuild_auto as ra

WRITE = "--write" in sys.argv
import fitz
pdf = fitz.open(r"F:\philosophy\西方\伏尔泰\哲学书简.pdf")
N = len(pdf)
toc = pdf.get_toc()
assert len(toc) == 27, f"目录 {len(toc)} != 27"

# 章标题 + 起始页(0-based)
STARTS = [(t[1], t[2] - 1) for t in toc]
BOOKS = json.load(open(r"f:\program\Python\PhiAgent\app\public\books.json", encoding="utf-8"))
BID = next(b["id"] for b in BOOKS if b["title"] == "哲学书简")
CH = ra.CH
D = os.path.join(CH, BID)
print("bid:", BID)

def _is_cjk(c):
    return 0x4E00 <= ord(c) <= 0x9FFF or 0x3400 <= ord(c) <= 0x4DBF

def to_paras(text):
    """行尾中文+行首中文拼接, 空行切段"""
    lines = text.split("\n")
    merged = []
    for line in lines:
        s = line.strip()
        if not s:
            merged.append("")
            continue
        if merged and merged[-1] and _is_cjk(merged[-1][-1]) and _is_cjk(s[0]):
            merged[-1] += s
        else:
            merged.append(s)
    return [p.strip() for p in re.split(r"\n\s*\n", "\n".join(merged)) if p.strip()]

PAGE_RE = re.compile(r"^\d{1,4}$")

def page_paras(i):
    """p i (0-based) 的段落, 过滤纯页码"""
    txt = pdf[i].get_text()
    lines = [l.strip() for l in txt.split("\n") if l.strip() and not PAGE_RE.match(l.strip())]
    if not lines:
        return []
    merged = []
    for s in lines:
        if merged and _is_cjk(merged[-1][-1]) and _is_cjk(s[0]):
            merged[-1] += s
        else:
            merged.append(s)
    return merged

# ── 提取各章 ──
chapters = []
for idx, (title, start) in enumerate(STARTS):
    end = STARTS[idx + 1][1] if idx + 1 < len(STARTS) else N
    paras = []
    for i in range(start, end):
        paras.extend(page_paras(i))
    # 章标题行若残留在首段开头则去掉
    if paras and paras[0] == title:
        paras = paras[1:]
    chapters.append({"title": title, "paras": paras, "page": start})
    n = sum(len(x) for x in paras)
    flag = "  !!空" if not paras else ""
    print(f"  {title[:28]:<30} p{start + 1}-{end} 段{len(paras):<4} 字{n}{flag}")

# ── 校验 ──
print("\n=== 校验 ===")
for c in chapters:
    if not c["paras"]:
        print(f"  空章: {c['title']}")
        continue
    first, last = c["paras"][0], c["paras"][-1]
    if not re.match(r"^[\u4e00-\u9fff（《\"“0-9]", first[:1]):
        print(f"  首段异常开头: [{c['title'][:16]}] {first[:30]}")
    if last and last[-1] not in "。！？；…\"”)]）】·}":
        print(f"  尾段无句末标点: [{c['title'][:16]}] …{last[-40:]}")

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
    meta = {"bookId": BID, "title": "哲学书简", "author": "伏尔泰",
            "toc": [], "cover": None, "chapterCount": len(chapters), "chapterTitles": []}
    for i, c in enumerate(chapters):
        fp = os.path.join(D, f"{i}.json")
        content = [{"type": "text", "value": x} for x in c["paras"]]
        json.dump({"title": c["title"], "content": content, "index": i},
                  open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        meta["toc"].append({"type": "chapter", "title": c["title"], "index": i, "level": 1})
        meta["chapterTitles"].append(c["title"])
    json.dump(meta, open(os.path.join(D, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n写入完成: {len(chapters)} 章, toc {len(meta['toc'])} 条")
    ra.sync_three(BID)
    print("sync_three 完成")
