# -*- coding: utf-8 -*-
"""三本重建成果部署：_xr_out_* → PA 书章节目录（meta 覆盖）"""
import os, shutil
PA = 'f:/program/Python/PhiAgent/backend/data/book_chapters'
OUT = os.path.dirname(os.path.abspath(__file__))
for bid, d in [('f52ed83b99d9', '_xr_out_aquinas6'), ('9ed36aca09c5', '_xr_out_aquinas7'), ('7bb94a203c8c', '_xr_out_bacon')]:
    dst = os.path.join(PA, bid)
    for f in os.listdir(dst):
        os.remove(os.path.join(dst, f))
    for f in os.listdir(os.path.join(OUT, d)):
        shutil.copy2(os.path.join(OUT, d, f), os.path.join(dst, f))
    print('%s: %d 文件' % (bid, len(os.listdir(dst))))
