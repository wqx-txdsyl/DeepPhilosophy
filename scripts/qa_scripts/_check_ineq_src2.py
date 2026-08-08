# -*- coding: utf-8 -*-
import sys, os, json, glob
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CK = json.load(open(r"f:/program/Python/PhiAgent/backend/data/dp_pdf_import_ckpt.json", encoding="utf-8"))
bid = "9e4f98733f0b"
for k in CK.get("books", {}):
    import hashlib
    if hashlib.md5(k.encode()).hexdigest()[:12] == bid:
        print("rel:", k)
        print("books:", {kk: CK["books"][k] for kk, v in CK["books"].items() if False})
        b = CK["books"][k]
        print("books 条目:", {kk: vv for kk, vv in b.items() if kk != "pages"})
        print("pages 数量:", len(b.get("pages", {})))
        full = r"F:/philosophy/" + k.replace("/", os.sep)
        print("PDF 存在:", os.path.exists(full), full)
        if os.path.exists(full):
            import fitz
            doc = fitz.open(full)
            print(f"PDF 页数 {len(doc)} 文本层总字数 {sum(len(doc[i].get_text()) for i in range(len(doc)))}")
            for i in range(min(len(doc), 8)):
                t = doc[i].get_text()
                lines = [l.strip() for l in t.split("\n") if l.strip()]
                print(f" 页{i:03d} {len(t):6d}字 | {' / '.join(lines[:3])[:70]}")
            doc.close()
        break
# OCR 段存在?
d = CK.get("ocr", {}).get(k.replace("/", "_") if k else "")
print("ocr 段:", "有" if d else "无")
