# -*- coding: utf-8 -*-
"""指定页补 OCR: python _ocr_pages.py <源pdf> <safe名> <ckpt名> <页1,页2,...>
例: python _ocr_pages.py "F:\philosophy\西方\爱比克泰德\论选择的艺术.pdf" "西方_爱比克泰德_论选择的艺术.pdf" dp_pdf_import_ckpt_choice.json "4,5,13,26,28,34,44,46,47,50,59"
"""
import sys, os, json, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from pathlib import Path
import fitz

fp = sys.argv[1]
safe = sys.argv[2]
ckpt_name = sys.argv[3]
pages_needed = [int(x) for x in sys.argv[4].split(",")]
CKPT_FILE = os.path.join(r"f:\program\Python\PhiAgent\backend\data", ckpt_name)
ZOOM = 1.2

from paddleocr import PaddleOCR
ocr = PaddleOCR(lang="ch", use_textline_orientation=True, cpu_threads=2)

ckpt = json.load(open(CKPT_FILE, encoding="utf-8")) if os.path.exists(CKPT_FILE) else {}
done = ckpt.setdefault("ocr", {}).setdefault(safe, {})
todo = [p for p in pages_needed if done.get(str(p)) in (None, "", "__FAILED__")]
print(f"需 OCR {len(todo)} 页: {todo}", flush=True)

tmp = Path(os.environ.get("TEMP", ".")) / "dp_paddle"
tmp.mkdir(parents=True, exist_ok=True)
t0 = time.time()
for i in todo:
    doc = fitz.open(fp)
    pix = doc[i].get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM))
    img = str(tmp / f"{safe}_p{i:04d}.png")
    pix.save(img)
    doc.close()
    text = ""
    try:
        result = ocr.ocr(img)
        if result and result[0]:
            text = "\n".join(line[1][0] for line in result[0])
    except Exception as e:
        print(f"  页{i} 异常: {e}", flush=True)
    done[str(i)] = text or "__FAILED__"
    print(f"  页{i}: {len(text)}字", flush=True)
    ckpt["ocr"][safe] = done
    json.dump(ckpt, open(CKPT_FILE, "w", encoding="utf-8"), ensure_ascii=False)
print(f"完成: {safe} 补 {len(todo)} 页, 耗时 {(time.time()-t0)/60:.1f} 分钟", flush=True)
