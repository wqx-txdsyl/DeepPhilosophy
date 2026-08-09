# -*- coding: utf-8 -*-
"""搜全库章节文件里含 '建言' 的入库书 (定位论文文本来源)"""
import os, json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)

base = r'F:\program\Python\DeepPhilosophy\DeepPhilosophy\backend\data\book_chapters'
hits = []
for bid in os.listdir(base):
    d = os.path.join(base, bid)
    if not os.path.isdir(d):
        continue
    meta_fp = os.path.join(d, 'meta.json')
    if not os.path.exists(meta_fp):
        continue
    meta = json.load(open(meta_fp, encoding='utf-8'))
    title = meta.get('title', '')
    for fn in sorted(os.listdir(d)):
        if fn == 'meta.json':
            continue
        try:
            txt = open(os.path.join(d, fn), encoding='utf-8').read(200000)
        except Exception:
            continue
        if '建言' in txt:
            hits.append((bid, title, fn))
            break
print('含"建言"的入库书:', hits if hits else '无')
