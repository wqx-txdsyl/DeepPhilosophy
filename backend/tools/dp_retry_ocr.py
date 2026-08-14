# -*- coding: utf-8 -*-
"""
dp_retry_ocr.py — 重 OCR FAILED 页（断点续传只补失败页, 不碰成功页）
用法: python dp_retry_ocr.py [safe 子串过滤] [--zoom 2.0]
必须先暂停 OCR 主进程 + watchdog（否则主进程全文件覆盖写会冲掉结果）！
"""
import sys, os, re, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dp_pdf_import as dpi

CK = dpi.CKPT_FILE
FILTER = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else ""
if "--zoom" in sys.argv:
    dpi.ZOOM = float(sys.argv[sys.argv.index("--zoom") + 1])
    print(f"ZOOM 提高至 {dpi.ZOOM}")

ck = json.load(open(CK, encoding="utf-8"))
ocr = ck.get("ocr") or {}
cands = [safe for safe, d in ocr.items()
         if any(v == "__FAILED__" for v in d.values())
         and (FILTER in safe if FILTER else True)]
print(f"待重 OCR 的书（含 FAILED 页）: {len(cands)}")

# safe → rel 映射: 扫描 BOOKS_DIR（与 dp_pdf_import.main 同规则; ckpt books 键已弃用, 2026-08-11）
def build_safe_map():
    m = {}
    for region in ["东方", "西方"]:
        rp = os.path.join(dpi.BOOKS_DIR, region)
        if not os.path.isdir(rp):
            continue
        for author in sorted(os.listdir(rp)):
            ap = os.path.join(rp, author)
            if not os.path.isdir(ap):
                continue
            for fn in sorted(os.listdir(ap)):
                fp = os.path.join(ap, fn)
                if not os.path.isfile(fp) or not fn.lower().endswith(".pdf"):
                    continue
                rel = os.path.relpath(fp, dpi.BOOKS_DIR).replace("\\", "/")
                if rel in dpi.MERGE_RULES:
                    continue
                m[re.sub(r"[^\w\-.]", "_", rel)] = rel   # 规则式（· → _）
                m[re.sub(r"[^\w\-.·]", "_", rel)] = rel  # 手工式（保留 ·, 2026-08-11 兼容手工 KEY）
    return m

SAFE_MAP = build_safe_map()
for safe in cands:
    fails = [int(k) for k, v in ocr[safe].items() if v == "__FAILED__"]
    rel = SAFE_MAP.get(safe)
    if not rel:
        print(f"  ✗ {safe}: 磁盘上找不到对应 PDF, 跳过"); continue
    fp = os.path.join(dpi.BOOKS_DIR, rel.replace("/", os.sep))
    if not os.path.exists(fp):
        print(f"  ✗ {safe}: PDF 不存在 {fp}"); continue
    print(f"  ▶ {safe[:36]} {len(fails)} 页 FAILED → 重 OCR（ZOOM={dpi.ZOOM}）")
    dpi.ocr_pdf(fp, ck, safe)   # 只补 FAILED 页; 每 10 页写盘
    # 复查
    ck2 = json.load(open(CK, encoding="utf-8"))
    d2 = ck2["ocr"].get(safe, {})
    left = [k for k, v in d2.items() if v == "__FAILED__"]
    print(f"  ✓ {safe[:36]} 剩余 FAILED: {len(left)} 页 {sorted(map(int, left)) if left else '无'}")
print("\n完成")
