# -*- coding: utf-8 -*-
"""查尼采与哲学: 三端 chapterCount/章节标题 + 源文本卷标题形态"""
import sys, os, json, re, glob
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"f:/program/Python/PhiAgent/backend"
CH = os.path.join(BASE, "data", "book_chapters")
DP_BACKEND = r"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters"
DP_PUBLIC = r"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters"

bid = None
for b in os.listdir(CH):
    mfp = os.path.join(CH, b, "meta.json")
    if os.path.exists(mfp):
        m = json.load(open(mfp, encoding="utf-8"))
        if "尼采与哲学" in m.get("title", ""):
            bid = b
            break
print("bid =", bid)
if not bid:
    sys.exit(0)

meta = json.load(open(os.path.join(CH, bid, "meta.json"), encoding="utf-8"))
print("PhiAgent chapterCount =", meta.get("chapterCount"))
print("章节标题全部（{} 个）:".format(len(meta.get("chapterTitles", []))))
for i, t in enumerate(meta.get("chapterTitles", [])):
    print(f"  {i}: {t}")
for tag, base in (("DP后端", DP_BACKEND), ("DPpublic", DP_PUBLIC)):
    d = os.path.join(base, bid, "meta.json")
    if os.path.exists(d):
        dm = json.load(open(d, encoding="utf-8"))
        print(f"{tag} chapterCount =", dm.get("chapterCount"))
    else:
        print(f"{tag} 缺失")

# 源文本卷标题形态: 找该书的 pdf/epub 文本层
import fitz
pdf_candidates = glob.glob(r"f:/program/Python/PhiAgent/backend/data/**/*.pdf", recursive=True)
hit = None
for p in pdf_candidates:
    try:
        doc = fitz.open(p)
        t0 = doc[0].get_text()[:200]
        if "尼采" in t0:
            hit = p
            doc.close()
            break
        doc.close()
    except Exception:
        pass
print("\n源 PDF =", hit)
if hit:
    doc = fitz.open(hit)
    pat = re.compile(r"第[一二三四五六七八九十]+卷|第[一二三四五六七八九十]+章|^[一二三四五六七八九十]+、|^第[一二三四五六七八九十]+节")
    found = {}
    for i in range(len(doc)):
        t = doc[i].get_text()
        for m in pat.finditer(t):
            line = t[m.start():m.start()+30].replace("\n", "⏎")[:30]
            found.setdefault(line[:12], []).append(i)
        if len(found) > 40:
            break
    doc.close()
    for k, v in list(found.items())[:40]:
        print(f"  {k!r} @页 {v[:8]}")
