# -*- coding: utf-8 -*-
"""图斯库兰论辩集 + 现象学的观念: 实际章节文件列表 + toc 全文"""
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
    print('文件列表:', sorted(f for f in os.listdir(D) if f.endswith('.json')))
    m = json.load(open(os.path.join(D, 'meta.json'), encoding='utf-8'))
    print('chapterCount:', m.get('chapterCount'))
    for t in m.get('toc', []):
        print('  toc:', json.dumps(t, ensure_ascii=False)[:80])
    # 检查是 pdf 还是 epub: 看 books.json
    bj = json.load(open(os.path.join(BASE, 'app/public/books.json'), encoding='utf-8'))
    items = bj if isinstance(bj, list) else bj.get('books', [])
    for it in items:
        if it.get('id') == bid:
            print('books.json:', it.get('title'), it.get('author'), it.get('file_type'))
    print()
