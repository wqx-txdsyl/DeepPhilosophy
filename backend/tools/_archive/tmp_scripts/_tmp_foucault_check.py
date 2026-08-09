# -*- coding: utf-8 -*-
"""导读福柯: chapterTitles 12 vs chapterCount 10 诊断"""
import json, os, sys, io

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy'
# 找导读福柯的 bid
bj = json.load(open(os.path.join(BASE, 'app/public/books.json'), encoding='utf-8'))
items = bj if isinstance(bj, list) else bj.get('books', [])
for it in items:
    if '福柯' in it.get('title', '') or '规训' in it.get('title', ''):
        print('books:', it.get('id'), it.get('title'), it.get('chapterCount'))
        bid = it['id']
        mfp = os.path.join(BASE, 'backend/data/book_chapters', bid, 'meta.json')
        if os.path.exists(mfp):
            m = json.load(open(mfp, encoding='utf-8'))
            print('meta: chapterCount=%d toc=%d chapterTitles=%d' % (m.get('chapterCount'), len(m.get('toc', [])), len(m.get('chapterTitles', []))))
            print('  toc 前 3:', json.dumps(m.get('toc', [])[:3], ensure_ascii=False)[:200])
            print('  toc 后 3:', json.dumps(m.get('toc', [])[-3:], ensure_ascii=False)[:200])
            print('  chapterTitles:', m.get('chapterTitles'))
            # 文件数
            D = os.path.join(BASE, 'backend/data/book_chapters', bid)
            files = [f for f in os.listdir(D) if f.endswith('.json') and f != 'meta.json']
            print('  文件数:', len(files), files[:12])
        print()
