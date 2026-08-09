# -*- coding: utf-8 -*-
"""诊断 FAILED 页渲染: 像素统计判断页面是空白/纯色/有内容"""
import fitz, os, sys, io

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

PDF = r'F:/philosophy/西方/格奥尔格·威廉·弗里德里希·黑格尔/精神现象学.pdf'
TARGETS = [92, 94, 142, 144, 180, 300, 302, 450, 522, 538]
doc = fitz.open(PDF)
print('总页数:', doc.page_count)
for i in TARGETS:
    pg = doc[i]
    # 页面本身内容类型
    objs = pg.get_text('dict')
    n_blocks = len(objs.get('blocks', []))
    n_imgs = sum(1 for b in objs.get('blocks', []) if b.get('type') == 1)
    print('页 %d: blocks=%d images=%d rect=%s' % (i, n_blocks, n_imgs, pg.rect))
    pix = pg.get_pixmap(matrix=fitz.Matrix(1.0, 1.0))
    # 像素统计: 采样
    samples = pix.samples
    n = pix.width * pix.height
    nonwhite = 0
    dark = 0
    step = max(1, pix.width * pix.height // 20000)
    for p in range(0, n * pix.n, step * pix.n):
        r = samples[p]; g = samples[p + 1]; b = samples[p + 2]
        if r < 200 or g < 200 or b < 200:
            nonwhite += 1
            if r < 80 and g < 80 and b < 80:
                dark += 1
    tot_sampled = n // step
    print('  尺寸 %dx%d 采样 %d: 非白 %.1f%% 全黑 %.1f%%' % (
        pix.width, pix.height, tot_sampled, 100 * nonwhite / tot_sampled, 100 * dark / tot_sampled))
doc.close()
