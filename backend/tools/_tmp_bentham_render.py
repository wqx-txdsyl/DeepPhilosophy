# -*- coding: utf-8 -*-
"""渲染边沁 PDF 页 85/87 看版面结构"""
import fitz

fp = r'F:/philosophy/西方/杰里米·边沁/道德与立法原理导论.pdf'
doc = fitz.open(fp)
for p in [85, 87]:
    pix = doc[p].get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
    pix.save(r'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/tools/_tmp_bentham_p%d.png' % p)
    print('已渲染页', p)
doc.close()
