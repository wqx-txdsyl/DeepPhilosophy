# -*- coding: utf-8 -*-
"""斯宾诺莎伦理学补 OCR（主线3）：fail 8 页 + 174-273 页（第4/5部分从未OCR）
输出每页文本到 _xr_spinoza_fill.txt（不写 checkpoint——引擎在跑，全量 dump 会覆盖）
"""
import sys, time, os, re

FP = r'F:/philosophy/西方/巴鲁赫·斯宾诺莎/伦理学.pdf'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_xr_spinoza_fill.txt')

def main():
    import fitz
    from paddleocr import PaddleOCR
    ocr = PaddleOCR(lang="ch", use_textline_orientation=True, cpu_threads=4)
    tmp = os.path.join(os.environ.get("TEMP", "."), "dp_paddle")
    os.makedirs(tmp, exist_ok=True)
    doc = fitz.open(FP)
    pages = [155,156,157,158,159,171,172,173] + list(range(174, 274))
    out = open(OUT, "w", encoding="utf-8")
    t0 = time.time()
    for n, p in enumerate(pages):
        pix = doc[p].get_pixmap(matrix=fitz.Matrix(1.2, 1.2))
        img = os.path.join(tmp, f"_xr_sp_p{p:04d}.png")
        pix.save(img)
        try:
            res = ocr.ocr(img)
            text = "\n".join(line[1][0] for line in res[0]) if res and res[0] else ""
        except Exception as e:
            text = f"__ERR__ {e}"
        out.write(f"### p{p} ({len(text)}字) ###\n{text}\n### END ###\n")
        out.flush()
        if n % 10 == 9:
            print(f"  {n+1}/{len(pages)} p{p} {time.time()-t0:.0f}s", flush=True)
    out.close()
    doc.close()
    print(f"完成: {len(pages)} 页 → {OUT} ({time.time()-t0:.0f}s)")

if __name__ == "__main__":
    main()
