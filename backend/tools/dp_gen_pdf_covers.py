# -*- coding: utf-8 -*-
"""
dp_gen_pdf_covers.py — pdf 书封面抓取（不需要 OCR! fitz 渲染首页即可）
背景: 86 本 pdf 无封面——原设计等 OCR 完成后 make_cover 生成; 但首页渲染不依赖 OCR, 可提前
  1. books.json 中 file_type==pdf 且无 cover 的书
  2. fitz 打开 pdf → 渲染第 1 页（Matrix 1.5）→ webp → /covers/{bid}_cover.webp
  3. detail 更新 cover 字段; covers.json 由 dp_epub_covers.py 重建
"""
import sys, io, os, json, re
from pathlib import Path

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dp_gen_pdf_covers.log")
def _log(*args, **kwargs):
    msg = " ".join(str(a) for a in args)
    try:
        sys.__stdout__.write(msg + "\n"); sys.__stdout__.flush()
    except Exception:
        pass
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass

import fitz
TOOLS = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, TOOLS)
from build_book_json import save_as_webp

BASE = os.path.dirname(TOOLS)  # backend/
PHILO = r"F:/philosophy"
BOOKS_FILE = os.path.join(BASE, "..", "app", "public", "books.json")
DDIR = os.path.join(BASE, "data", "book_detail")
COVERS_DIR = os.path.join(BASE, "..", "app", "public", "covers")
os.makedirs(COVERS_DIR, exist_ok=True)

# 与 dp_pdf_import 一致的合并规则（副文件跳过——只处理主文件）
MERGE_SUBS = {
    "西方/弗里德里希·恩格斯/MEGA：陶伯特版《德意志意识形态·费尔巴哈》.pdf",
    "西方/弗里德里希·恩格斯/共产党宣言.pdf",
    "西方/弗里德里希·恩格斯/德意志意识形态（节选本）.pdf",
    "西方/弗里德里希·恩格斯/马克思恩格斯文集.epub",
    "西方/波爱修斯/哲学规劝录 哲学的慰藉.pdf",
}


def find_pdfs():
    found = {}
    for region in ("东方", "西方"):
        rp = os.path.join(PHILO, region)
        for root, dirs, files in os.walk(rp):
            for fn in files:
                if fn.lower().endswith(".pdf"):
                    rel = os.path.relpath(os.path.join(root, fn), PHILO).replace("\\", "/")
                    if rel in MERGE_SUBS:
                        continue
                    found[rel] = os.path.join(root, fn)
    return found


def render_cover(pdf_path, out_path):
    doc = fitz.open(pdf_path)
    pix = doc[0].get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
    doc.close()
    tmp = Path(os.environ.get("TEMP", ".")) / "dp_pdf_cover.png"
    pix.save(str(tmp))
    save_as_webp(tmp.read_bytes(), out_path)
    tmp.unlink(missing_ok=True)
    return out_path


def main():
    books = json.load(open(BOOKS_FILE, encoding="utf-8"))
    pdfs = find_pdfs()
    todo = [b for b in books if b.get("file_type") == "pdf" and not b.get("cover")]
    _log(f"pdf 无封面: {len(todo)}")
    done, fail = 0, 0
    for b in todo:
        rel = None
        for r in pdfs:
            import hashlib
            if hashlib.md5(r.encode("utf-8")).hexdigest()[:12] == b["id"]:
                rel = r
                break
        if rel is None:
            _log(f"  !! 文件未找到: {b['title']} (bid {b['id']})")
            fail += 1
            continue
        try:
            op = os.path.join(COVERS_DIR, f"{b['id']}_cover.webp")
            render_cover(pdfs[rel], op)
            # 更新 detail.cover
            dp = os.path.join(DDIR, f"{b['id']}.json")
            det = {}
            if os.path.exists(dp):
                try:
                    det = json.load(open(dp, encoding="utf-8"))
                except Exception:
                    pass
            det["cover"] = f"/covers/{b['id']}_cover.webp"
            json.dump(det, open(dp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            _log(f"  ✓ {b['title']}")
            done += 1
        except Exception as e:
            _log(f"  ✗ {b['title']}: {e}")
            fail += 1
    _log(f"done: {done} ok, {fail} fail（covers.json 由 dp_epub_covers.py 重建）")


if __name__ == "__main__":
    main()
