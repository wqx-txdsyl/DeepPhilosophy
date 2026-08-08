# -*- coding: utf-8 -*-
"""从 ckpt ocr 缓存导出指定书的页文本到 _xc_tmp_pages.json
用法: python _xc_dump_pages.py <safe_key> <总页数>
"""
import json, sys, os

sys.stdout.reconfigure(encoding="utf-8")

SAFE = sys.argv[1]
N = int(sys.argv[2]) if len(sys.argv) > 2 else None
ck = json.load(open(r"f:/program/Python/PhiAgent/backend/data/dp_pdf_import_ckpt.json", encoding="utf-8"))
v = ck["ocr"][SAFE]
if N is None:
    N = len(v)
pages = {str(k): v.get(str(k), "<缺失>") for k in range(N)}
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_xc_tmp_pages.json")
json.dump(pages, open(out, "w", encoding="utf-8"), ensure_ascii=False)
fails = [k for k, t in pages.items() if (t or "").strip() in ("FAILED", "") or len((t or "").strip()) < 8]
print(f"导出 {N} 页 → {out}, 空/极短页: {len(fails)}")
