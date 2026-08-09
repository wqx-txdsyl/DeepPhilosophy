# -*- coding: utf-8 -*-
"""新工具核查：2.json 关键串定位 + PDF 真实页数 + 全目录残留扫描"""
import json, os, re
import fitz
OUT = os.path.dirname(os.path.abspath(__file__)) + '/_xr_out_bacon'
ch = json.load(open(os.path.join(OUT, '2.json'), encoding='utf-8'))
v = ch['content'][0]['value']
for kw in ['进至隐秘', '面包', '人类生活效用']:
    for m in re.finditer(kw, v):
        s = max(0, m.start() - 60)
        print('[2.json 命中 %s] pos=%d' % (kw, m.start()))
        print('  ...' + v[s:m.start() + 80].replace('\n', '⏎') + '...')
        break  # 只查首次
# PDF 真实页数
doc = fitz.open('F:/philosophy/西方/弗朗西斯·培根/新工具.pdf')
print('PDF 真实总页数: %d' % doc.page_count)
doc.close()
# 目录残留扫描（每章行首特征）
for f in ['0.json', '1.json', '2.json']:
    d = json.load(open(os.path.join(OUT, f), encoding='utf-8'))
    t = d['content'][0]['value']
    hdr = re.findall(r'^新工具[①一二]?$|^序言[·.]?$|^第[一二]卷[?·]?$|^语录[?？一二]?$|^第一章$|^____(?:FAILED|OK)____$|__FAILED__', t, re.M)
    print('%s 行首残留: %s' % (f, hdr[:20]))
    bad = t.count('__FAILED__')
    print('%s __FAILED__ 次数: %d' % (f, bad))
