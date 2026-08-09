# -*- coding: utf-8 -*-
"""对比正常页与 FAILED 页的图像大小, 验证占位图假设"""
import fitz, os, sys, io

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

PDF = r'F:/philosophy/西方/格奥尔格·威廉·弗里德里希·黑格尔/精神现象学.pdf'
doc = fitz.open(PDF)
# 抽样: 页 100(正文), 91(FAILED 前), 93, 95, 141, 143
pages = [91, 92, 93, 94, 95, 100, 141, 142, 143, 144, 145]
for i in pages:
    pg = doc[i]
    imgs = pg.get_images(full=True)
    info = []
    for im in imgs:
        xref = im[0]
        try:
            raw = doc.extract_image(xref)
            info.append('%d: %dKB %s' % (xref, len(raw['image']) // 1024, raw['ext']))
        except Exception as e:
            info.append('%d: ERR' % xref)
    print('页 %3d: %s' % (i, ' | '.join(info) if info else '无图像(文本页)'))
doc.close()
