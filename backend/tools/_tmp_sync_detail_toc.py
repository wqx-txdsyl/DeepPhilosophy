# -*- coding: utf-8 -*-
"""同步 book_detail（backend+public）的 toc/chapterCount/chapterTitles ← book_chapters meta.json
修复: 工具论(b471f41a78de) /book 页 toc 扁平（detail 缺 section 分级项）、边沁(74ee21ced920) chapterCount 0
book-detail-sync-rule 三处同步: backend detail + public detail + books.json chapterCount
"""
import json, os, shutil

B = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy'
META_DIR = os.path.join(B, 'backend', 'data', 'book_chapters')
DETAIL_DIR = os.path.join(B, 'backend', 'data', 'book_detail')
PUBLIC_DETAIL_DIR = os.path.join(B, 'app', 'public', 'book_detail')
BOOKS_JSONS = [os.path.join(B, 'app', 'public', 'books.json'),
               os.path.join(B, 'app', 'src', 'assets', 'books.json')]

BIDS = ['b471f41a78de', '74ee21ced920']

for bid in BIDS:
    meta = json.load(open(os.path.join(META_DIR, bid, 'meta.json'), encoding='utf-8'))
    for p in [os.path.join(DETAIL_DIR, bid + '.json'), os.path.join(PUBLIC_DETAIL_DIR, bid + '.json')]:
        d = json.load(open(p, encoding='utf-8'))
        old = (d.get('chapterCount'), len(d.get('toc') or []))
        d['chapterCount'] = meta['chapterCount']
        d['toc'] = meta.get('toc') or []
        d['chapterTitles'] = meta.get('chapterTitles') or []
        json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
        print('detail:', os.path.basename(p), '| 旧 chapterCount/toc:', old, '→', meta['chapterCount'], len(d['toc']))

    # books.json 同步 chapterCount
    for bp in BOOKS_JSONS:
        books = json.load(open(bp, encoding='utf-8'))
        for b in books:
            if b.get('id') == bid:
                old = b.get('chapterCount')
                b['chapterCount'] = meta['chapterCount']
                print('books.json:', os.path.basename(os.path.dirname(bp)) + '/', bid, '| chapterCount:', old, '→', meta['chapterCount'])
        json.dump(books, open(bp, 'w', encoding='utf-8'), ensure_ascii=False)
print('完成')
