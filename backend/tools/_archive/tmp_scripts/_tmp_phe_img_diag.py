# -*- coding: utf-8 -*-
"""检查 FAILED 页图像对象: 编码/数据完整性"""
import fitz, os, sys, io

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

PDF = r'F:/philosophy/西方/格奥尔格·威廉·弗里德里希·黑格尔/精神现象学.pdf'
TARGETS = [92, 94, 300, 538]
doc = fitz.open(PDF)
for i in TARGETS:
    pg = doc[i]
    imgs = pg.get_images(full=True)
    print('页 %d: %d 图像' % (i, len(imgs)))
    for im in imgs:
        xref, smask, w, h, bpc, colorspace, altcs, name, filter, *rest = im
        print('  xref=%s w=%s h=%s bpc=%s cs=%s filter=%s smask=%s' % (xref, w, h, bpc, colorspace, filter, smask))
        # 提取原始数据检查大小
        try:
            raw = doc.extract_image(xref)
            print('    extract_image: %s %d bytes %s' % (raw.get('ext'), raw.get('image', b'').__len__(), raw.get('smask') and 'smask存在' or ''))
        except Exception as e:
            print('    extract_image 失败: %s' % e)
        # 页面图像 bbox
        for b in pg.get_image_info():
            print('    图像 bbox:', b.get('bbox'))
doc.close()
