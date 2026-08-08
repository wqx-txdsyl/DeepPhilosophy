# -*- coding: utf-8 -*-
"""单页补 OCR 工具（主线3）：对已入库书的 fail 页单独 OCR
用法: python _xr_page_ocr.py <pdf路径> <页号> [页号...]
输出: 每页 OCR 文本到 stdout（页号 从0开始，与 checkpoint 一致）
不动 checkpoint（引擎在跑，全量 dump 会覆盖）；结果用于人工补录章节数据。
"""
import sys, time, os

def main():
    if len(sys.argv) < 3:
        sys.exit("用法: python _xr_page_ocr.py <pdf路径> <页号...>")
    fp, pages = sys.argv[1], [int(x) for x in sys.argv[2:]]
    import fitz
    from paddleocr import PaddleOCR
    ocr = PaddleOCR(lang="ch", use_textline_orientation=True, cpu_threads=4)
    tmp = os.path.join(os.environ.get("TEMP", "."), "dp_paddle")
    os.makedirs(tmp, exist_ok=True)
    doc = fitz.open(fp)
    for p in pages:
        pix = doc[p].get_pixmap(matrix=fitz.Matrix(1.2, 1.2))
        img = os.path.join(tmp, f"_xr_page_{p:04d}.png")
        pix.save(img)
        t0 = time.time()
        res = ocr.ocr(img)
        text = "\n".join(line[1][0] for line in res[0]) if res and res[0] else ""
        print(f"### p{p} ({time.time()-t0:.0f}s) {len(text)}字 ###")
        print(text)
        print("### END ###")
        sys.stdout.flush()
    doc.close()

if __name__ == "__main__":
    main()
