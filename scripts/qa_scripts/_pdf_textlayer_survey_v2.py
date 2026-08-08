# -*- coding: utf-8 -*-
"""82 本无目录 pdf 严格文本层检测 v2（修正: 多页抽样防假阳性）"""
import sys, os, re, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import fitz

BOOKS = json.load(open(r"f:\program\Python\PhiAgent\app\public\books.json", encoding="utf-8"))
CH = r"f:\program\Python\PhiAgent\backend\data\book_chapters"
dirset = set(os.listdir(CH))
def norm(n):
    return re.sub(r"[\s（）(《》「」\"'”’【】)\]）·•　\-—]+", "", n).lower()

srcs = []
for root, dirs, files in os.walk(r"F:\philosophy"):
    for f in files:
        if f.lower().endswith(".pdf"):
            srcs.append((norm(os.path.splitext(f)[0]), os.path.join(root, f)))

no_dir = [b for b in BOOKS if b.get("file_type") == "pdf" and b["id"] not in dirset]
tl, ocr = [], []
for b in no_dir:
    bn = norm(b["title"])
    cands = [p for n, p in srcs if n == bn] or [p for n, p in srcs if bn and bn in n and len(n) <= len(bn) + 10]
    if not cands:
        print(f"  无源: {b['title']}", flush=True)
        ocr.append((b["title"], None, 0)); continue
    p = cands[0]
    try:
        d = fitz.open(p)
        n = len(d)
        # 严格抽样: 前3 + 1/3 + 2/3 + 尾页
        idxs = list(range(min(3, n)))
        if n > 6:
            idxs += [n // 3, 2 * n // 3, n - 1]
        pages_txt = [d[i].get_text() for i in idxs]
        zh_total = sum(len(re.findall(r'[\u4e00-\u9fff]', t)) for t in pages_txt)
        ok_pages = sum(1 for t in pages_txt if len(re.findall(r'[\u4e00-\u9fff]', t)) > 50)
        d.close()
        if ok_pages >= 3 and zh_total > 300:
            tl.append((b["title"], p, n))
            print(f"  ✓ 文本层 {b['title'][:28]:<30} {n}页", flush=True)
        else:
            ocr.append((b["title"], p, n))
            print(f"  ✗ 需OCR  {b['title'][:28]:<30} {n}页 (抽样中文{zh_total})", flush=True)
    except Exception as e:
        ocr.append((b["title"], None, 0))
        print(f"  ! {b['title'][:28]} {e}", flush=True)

print(f"\n=== 严格检测: 文本层 {len(tl)} 本 / 需OCR {len(ocr)} 本 ===")
json.dump({"tl": tl, "ocr": ocr}, open(r"f:\program\Python\DeepPhilosophy\DeepPhilosophy\scripts\qa_scripts\_pdf_missing_survey_v2.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for t, p, n in tl:
    print("  文本层:", t, p)
