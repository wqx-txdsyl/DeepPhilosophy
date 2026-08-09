# -*- coding: utf-8 -*-
"""查康德相关书在 books.json 的标题/bid/章数 + meta toc 类型"""
import json, os, sys, io

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy'
bj = json.load(open(os.path.join(BASE, 'app/public/books.json'), encoding='utf-8'))
items = bj if isinstance(bj, list) else bj.get('books', [])
for it in items:
    t = it.get('title', '')
    if '康德' in t:
        bid = it['id']
        mfp = os.path.join(BASE, 'backend/data/book_chapters', bid, 'meta.json')
        ttype = '缺失'
        cc = it.get('chapterCount')
        if os.path.exists(mfp):
            m = json.load(open(mfp, encoding='utf-8'))
            toc = m.get('toc', [])
            ttype = type(toc[0]).__name__ if toc else '空'
            cc = m.get('chapterCount')
        print('%s %s  file=%s  chapterCount=%s  toc[0]=%s' % (bid, t[:28], it.get('file_type'), cc, ttype))
