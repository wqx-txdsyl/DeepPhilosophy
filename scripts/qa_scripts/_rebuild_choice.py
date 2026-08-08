# -*- coding: utf-8 -*-
"""论选择的艺术 (爱比克泰德) 文本层全量重建 (2026-08-08) — 整本单章(正文/15568字) 拆为 56 章
源: F:/philosophy/西方/爱比克泰德/论选择的艺术.pdf (67 页, 文本层完整, PDF 目录 57 条)
结构: 前言(p4) + 正文 53 条箴言(p7-63) + 生平年表(p64) + 译后记(p66-67) → 56 章
边界: PDF 目录页码 (1-based, fitz 索引 = 值-1); 版权页(p3)/书名页(p5) 不入库
段落: 文本层空行切段, 行尾中文+行首中文拼接
用法: python _rebuild_choice.py [--write]
"""
import sys, os, re, json, shutil
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"f:\program\Python\PhiAgent\backend\tools")
import rebuild_auto as ra

WRITE = "--write" in sys.argv
import fitz
pdf = fitz.open(r"F:\philosophy\西方\爱比克泰德\论选择的艺术.pdf")
toc = pdf.get_toc()
BOOKS = json.load(open(r"f:\program\Python\PhiAgent\app\public\books.json", encoding="utf-8"))
BID = next(b["id"] for b in BOOKS if b["title"] == "论选择的艺术")
CH = ra.CH
D = os.path.join(CH, BID)
print("bid:", BID)

# ── 章节起始页 (fitz 0-based, 已逐页核对首行编号) ──
STARTS = [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24,
          25, 26, 27, 28, 29, 31, 32, 33, 34, 35, 37, 38, 40, 41, 43, 44, 45, 46,
          47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62]
assert len(STARTS) == 53
# 章节清单: 前言 + 01-53 (长条跨页: 24→fitz30, 29→36, 31→39, 33→42 为续页) + 年表 + 译后记
CHS = [("前言", 4, 5)]
CHS += [(f"{i:02d}", STARTS[i - 1], STARTS[i] if i < 53 else 63) for i in range(1, 54)]
CHS += [("爱比克泰德生平年表", 63, 65),
        ("译后记", 65, 67)]
assert len(CHS) == 56, f"{len(CHS)} 章 != 56"

def _is_cjk(c):
    return 0x4E00 <= ord(c) <= 0x9FFF or 0x3400 <= ord(c) <= 0x4DBF

def page_paras(i):
    txt = pdf[i].get_text()
    lines = [l.strip() for l in txt.split("\n") if l.strip()]
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
for title, lo, hi in CHS:
    paras = []
    for i in range(lo, hi):
        paras.extend(page_paras(i))
    # 章首数字标题行 (01 等) 若独立则跳过
    if paras and re.match(r"^\d{1,2}$", paras[0]):
        paras = paras[1:]
    chapters.append({"title": title, "paras": paras, "page": lo})
    n = sum(len(x) for x in paras)
    flag = "  !!空" if not paras else ""
    print(f"  {title[:24]:<26} fitz[{lo}-{hi}] 段{len(paras):<3} 字{n}{flag}")

# ── 校验 ──
print("\n=== 校验 ===")
for c in chapters:
    if not c["paras"]:
        print(f"  空章: {c['title']}")
        continue
    first, last = c["paras"][0], c["paras"][-1]
    if not re.match(r"^[\u4e00-\u9fff（《\"“0-9]", first[:1]):
        print(f"  首段异常开头: [{c['title'][:12]}] {first[:30]}")
    if last and last[-1] not in "。！？；…\"”)]）】·}":
        print(f"  尾段无句末标点: [{c['title'][:12]}] …{last[-35:]}")

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
    meta = {"bookId": BID, "title": "论选择的艺术", "author": "爱比克泰德",
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
