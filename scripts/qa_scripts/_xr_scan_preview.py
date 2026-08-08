# -*- coding: utf-8 -*-
"""模拟新版 dp_pdf_import 判定：全量扫描 → 待处理清单（dry-run，不跑 OCR）"""
import os, json, re, hashlib

BOOKS_DIR = "F:/philosophy"
CDIR = "f:/program/Python/PhiAgent/backend/data/book_chapters"

MERGE = {
    "西方/弗里德里希·恩格斯/MEGA：陶伯特版《德意志意识形态·费尔巴哈》.pdf",
    "西方/弗里德里希·恩格斯/共产党宣言.pdf",
    "西方/弗里德里希·恩格斯/德意志意识形态（节选本）.pdf",
    "西方/弗里德里希·恩格斯/马克思恩格斯文集.epub",
    "西方/波爱修斯/哲学规劝录 哲学的慰藉.pdf",
    "西方/让-保罗·萨特/存在与虚无.pdf",
    "西方/柏拉图/理想国.pdf",
}
pdfs = []
for region in ["东方", "西方"]:
    rp = os.path.join(BOOKS_DIR, region)
    for author in sorted(os.listdir(rp)):
        ap = os.path.join(rp, author)
        if not os.path.isdir(ap):
            continue
        for fn in sorted(os.listdir(ap)):
            fp = os.path.join(ap, fn)
            if not os.path.isfile(fp):
                continue
            rel = os.path.relpath(fp, BOOKS_DIR).replace("\\", "/")
            if rel in MERGE:
                continue
            if fn.lower().endswith(".pdf"):
                pdfs.append(rel)

def valid(bid):
    bd = os.path.join(CDIR, bid)
    if not os.path.isdir(bd):
        return False
    try:
        m = json.load(open(os.path.join(bd, "meta.json"), encoding="utf-8"))
        return m.get("chapterCount", 0) >= 1
    except Exception:
        return False

todo, skip = [], 0
for rel in pdfs:
    bid = hashlib.md5(rel.encode()).hexdigest()[:12]
    if valid(bid):
        skip += 1
    else:
        todo.append(rel)
print(f"全量扫描: {len(pdfs)} 本 | 已有章节跳过: {skip} | 待处理: {len(todo)}")
print("== 待处理清单 ==")
for rel in sorted(todo):
    print("  ", rel)
