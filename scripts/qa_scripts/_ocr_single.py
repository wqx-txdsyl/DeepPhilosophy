# -*- coding: utf-8 -*-
"""单本 OCR（独立 ckpt, 与主任务并发不冲突）: python _ocr_single.py <源pdf> <safe名> <ckpt名>
例: python _ocr_single.py "F:\philosophy\西方\罗兰·巴特\SZ.pdf" "西方_罗兰_巴特_SZ.pdf" dp_pdf_import_ckpt_sz.json
"""
import sys, os, json, time, re
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path
import fitz

fp = sys.argv[1]
safe = sys.argv[2]
ckpt_name = sys.argv[3]
CKPT_FILE = os.path.join(r"f:\program\Python\PhiAgent\backend\data", ckpt_name)
ZOOM = 1.2
RESTART_EVERY = 100

_ocr, _ocr_pages = None, 0

def get_ocr():
    global _ocr, _ocr_pages
    from paddleocr import PaddleOCR
    if _ocr is None or _ocr_pages >= RESTART_EVERY:
        if _ocr is not None:
            del _ocr
            import gc; gc.collect()
        _ocr = PaddleOCR(lang="ch", use_textline_orientation=True, cpu_threads=2)
        _ocr_pages = 0
    return _ocr

def ocr_page(img_path):
    global _ocr_pages
    o = get_ocr()
    result = o.ocr(img_path)
    _ocr_pages += 1
    if result and result[0]:
        return "\n".join(line[1][0] for line in result[0])
    return ""

ckpt = json.load(open(CKPT_FILE, encoding="utf-8")) if os.path.exists(CKPT_FILE) else {}
doc = fitz.open(fp)
total = doc.page_count
doc.close()
done = ckpt.setdefault("ocr", {}).setdefault(safe, {})
pages_map = {int(k): v for k, v in done.items() if v and v != "__FAILED__"}
tmp = Path(os.environ.get("TEMP", ".")) / "dp_paddle"
tmp.mkdir(parents=True, exist_ok=True)
t0 = time.time()
for i in range(total):
    if i in pages_map:
        continue
    doc = fitz.open(fp)
    pix = doc[i].get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM))
    img = str(tmp / f"{safe}_p{i:04d}.png")
    pix.save(img)
    doc.close()
    text = ""
    try:
        text = ocr_page(img)
    except Exception as e:
        print(f"    页{i} 异常: {e}", flush=True)
    done[str(i)] = text or "__FAILED__"
    if i % 5 == 4:
        spd = (time.time() - t0) / (i + 1)
        eta = (total - i - 1) * spd / 60
        print(f"    页 {i+1}/{total}  {spd:.1f}s/页  预计剩 {eta:.0f} 分钟", flush=True)
    if i % 10 == 0:
        ckpt["ocr"][safe] = done
        json.dump(ckpt, open(CKPT_FILE, "w", encoding="utf-8"), ensure_ascii=False)
    time.sleep(0.1)
ckpt["ocr"][safe] = done
json.dump(ckpt, open(CKPT_FILE, "w", encoding="utf-8"), ensure_ascii=False)
print(f"完成: {safe} {total} 页", flush=True)
