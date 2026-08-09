# -*- coding: utf-8 -*-
"""渲染边沁 PDF 页 85/87 上半部为小图"""
import fitz

fp = r'F:/philosophy/西方/杰里米·边沁/道德与立法原理导论.pdf'
doc = fitz.open(fp)
for p in [85]:
    page = doc[p]
    # 只渲染上半页
    r = page.rect
    clip = fitz.Rect(r.x0, r.y0, r.x1, r.y0 + r.height * 0.55)
    pix = page.get_pixmap(matrix=fitz.Matrix(1.0, 1.0), clip=clip)
    pix.save(r'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/tools/_tmp_bentham_p%d_top.png' % p)
    print('ok', pix.width, pix.height)
doc.close()
