# -*- coding: utf-8 -*-
"""读图斯库兰 7 文件 + 现象学观念各文件标题"""
import json, os, sys, io

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy'
BC = os.path.join(BASE, 'backend/data/book_chapters')

for bid, name in [('4be7b72cf01d', '图斯库兰论辩集'), ('e2a4c4f78c40', '现象学的观念')]:
    D = os.path.join(BC, bid)
    print('==== %s %s' % (bid, name))
    for fn in sorted(f for f in os.listdir(D) if f.endswith('.json') and f != 'meta.json'):
        j = json.load(open(os.path.join(D, fn), encoding='utf-8'))
        body = j.get('content', '')
        print('  [%s] %r  %d字' % (fn, j.get('title', ''), len(body)))
    print()
