# -*- coding: utf-8 -*-
"""全库同步 book_detail ← meta.json（toc/chapterCount/chapterTitles），books.json 同步 chapterCount
72 本不同步（book-detail-sync-rule 历史遗漏）：detail 保留 summary/tags 等其余字段
以 meta 为准: /reader 用 meta.toc, /book 必须与之一致（toc index 对应真实章节文件）
"""
import json, os

B = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy'
META_DIR = os.path.join(B, 'backend', 'data', 'book_chapters')
DETAIL_DIR = os.path.join(B, 'backend', 'data', 'book_detail')
PUBLIC_DETAIL_DIR = os.path.join(B, 'app', 'public', 'book_detail')
BOOKS_JSONS = [os.path.join(B, 'app', 'public', 'books.json'),
               os.path.join(B, 'app', 'src', 'assets', 'books.json')]

def to_key(toc):
    if not toc or not isinstance(toc, list):
        return []
    out = []
    for t in toc:
        if isinstance(t, dict):
            out.append((t.get('type'), str(t.get('title', ''))))
        else:
            out.append(('chapter', str(t)))
    return out

books_all = {}
for bp in BOOKS_JSONS:
    books_all[bp] = json.load(open(bp, encoding='utf-8'))

n_detail = n_books = 0
for fn in sorted(os.listdir(DETAIL_DIR)):
    if not fn.endswith('.json'):
        continue
    bid = fn[:-5]
    mpath = os.path.join(META_DIR, bid, 'meta.json')
    if not os.path.exists(mpath):
        continue
    meta = json.load(open(mpath, encoding='utf-8'))
    if not isinstance(meta.get('toc'), list):
        continue

    for p in [os.path.join(DETAIL_DIR, fn), os.path.join(PUBLIC_DETAIL_DIR, fn)]:
        if not os.path.exists(p):
            continue
        d = json.load(open(p, encoding='utf-8'))
        old = (d.get('chapterCount'), len(d.get('toc') or []))
        new = (meta.get('chapterCount'), len(meta.get('toc') or []))
        if old == new and to_key(d.get('toc')) == to_key(meta.get('toc')):
            continue
        d['chapterCount'] = meta.get('chapterCount')
        d['toc'] = meta.get('toc')
        d['chapterTitles'] = meta.get('chapterTitles') or []
        json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
        n_detail += 1

    for bp, books in books_all.items():
        for b in books:
            if b.get('id') == bid and b.get('chapterCount') != meta.get('chapterCount'):
                b['chapterCount'] = meta.get('chapterCount')
                n_books += 1

for bp, books in books_all.items():
    json.dump(books, open(bp, 'w', encoding='utf-8'), ensure_ascii=False)
print('同步 detail 文件数:', n_detail, '| books.json 更新条数:', n_books)
