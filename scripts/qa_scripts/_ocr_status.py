# -*- coding: utf-8 -*-
"""统计 OCR 状态：无文本层 PDF 的完成情况
分组: 未开始 / 进行中(未跑完) / 已完成但带 fail 页 / 已完成
"""
import sys, os, json, re, hashlib
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path
import fitz

CKPT = r"f:\program\Python\PhiAgent\backend\data\dp_pdf_import_ckpt.json"
CH = r"f:\program\Python\PhiAgent\backend\data\book_chapters"
ck = json.load(open(CKPT, encoding="utf-8"))
ocr = ck.get("ocr", {})

def rel2safe(rel):
    """与 dp_pdf_import.py:299 一致: 非 \w-. → _"""
    return re.sub(r"[^\w\-.]", "_", rel)

def imported(rel):
    """book_chapters 里已有章节内容（非空章）"""
    bid = hashlib.md5(rel.encode()).hexdigest()[:12]
    d = os.path.join(CH, bid)
    if not os.path.isdir(d):
        return False
    mf = os.path.join(d, "meta.json")
    if not os.path.exists(mf):
        return False
    try:
        meta = json.load(open(mf, encoding="utf-8"))
        n = meta.get("chapterCount", 0)
    except Exception:
        n = 0
    if n <= 0:
        return False
    for i in range(n):
        f = os.path.join(d, f"{i}.json")
        if not os.path.exists(f):
            return False
        try:
            ch = json.load(open(f, encoding="utf-8"))
        except Exception:
            return False
        vals = [x.get("value", "") for x in ch.get("content", []) if isinstance(x, dict) and x.get("type") == "text"]
        if not any(v.strip() for v in vals):
            return False
    return True

pending, partial, failed, done = [], [], [], []
n_textlayer = 0
n_done_imported = 0
for p in sorted(Path(r"F:\philosophy").rglob("*.pdf")):
    rel = p.as_posix().replace("F:/philosophy/", "")
    safe = rel2safe(rel)
    rec = ocr.get(safe)
    try:
        doc = fitz.open(str(p))
        total = doc.page_count
        # 文本层检测: 前 5 页有非空文本即视为有文本层
        has_text = any(doc[i].get_text().strip() for i in range(min(5, total)))
        doc.close()
    except Exception as e:
        print(f"打开失败 {rel}: {e}")
        continue
    if has_text:
        n_textlayer += 1
        continue
    if rec is None:
        if imported(rel):
            n_done_imported += 1
        else:
            pending.append((total, rel))
    else:
        n = len(rec)
        failed_n = sum(1 for v in rec.values() if v == "__FAILED__" or (isinstance(v, str) and not v.strip()))
        if n < total:
            partial.append((total, n, failed_n, rel))
        elif failed_n:
            failed.append((total, failed_n, rel))
        else:
            done.append((total, rel))

print(f"F:/philosophy 总 PDF: {n_textlayer + n_done_imported + len(pending) + len(partial) + len(failed) + len(done)}")
print(f"有文本层(不需OCR): {n_textlayer}")
print(f"无文本层但已入库(早期OCR成果/其他来源): {n_done_imported}")
print(f"\n═══ 真正未开始 OCR: {len(pending)} 本 ═══")
for total, rel in sorted(pending):
    print(f"  {total:4d}页  {rel}")
print(f"\n═══ 进行中(页未跑完): {len(partial)} 本 ═══")
for total, n, failed_n, rel in sorted(partial):
    print(f"  {n:4d}/{total:4d}页 fail={failed_n}  {rel}")
print(f"\n═══ 已跑完但带 fail 页(需重跑): {len(failed)} 本 ═══")
for total, failed_n, rel in sorted(failed, key=lambda x: -x[1]):
    print(f"  fail={failed_n:3d}  {rel}")
print(f"\n已完成无 fail: {len(done)} 本")
