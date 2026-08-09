# -*- coding: utf-8 -*-
"""fitz 提取边沁页 85/87 文本块坐标, 分析版面结构"""
import fitz

fp = r'F:/philosophy/西方/杰里米·边沁/道德与立法原理导论.pdf'
doc = fitz.open(fp)
for p in [85, 87]:
    print('===== 页 %d =====' % p)
    d = doc[p].get_text('dict')
    for b in d['blocks']:
        if b['type'] != 0:
            continue
        for line in b['lines']:
            x0, y0, x1, y1 = line['bbox']
            text = ''.join(s['text'] for s in line['spans'])
            if text.strip():
                print('  y=%.0f x=%.0f-%.0f : %s' % (y0, x0, x1, text[:55]))
doc.close()
