# -*- coding: utf-8 -*-
"""16 本 OCR 书: public 副本存在性 + detail chapterCount 一致性盘点"""
import json, os, hashlib

B = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy'
CD = B + '/backend/data/book_chapters'
PUB = B + '/app/public/backend/data/book_chapters'
DD = B + '/backend/data/book_detail'
ck = json.load(open(B + '/backend/data/dp_pdf_import_ckpt.json', encoding='utf-8'))

rels = [rel for rel, v in ck['books'].items() if v.get('src') == 'ocr']
for rel in rels:
    bid = hashlib.md5(rel.encode()).hexdigest()[:12]
    cdir = os.path.join(CD, bid)
    pdir = os.path.join(PUB, bid)
    m = json.load(open(os.path.join(cdir, 'meta.json'), encoding='utf-8'))
    n_meta = m['chapterCount']
    # public 章文件数
    n_pub = len([f for f in os.listdir(pdir) if f.endswith('.json')]) if os.path.exists(pdir) else 0
    # detail
    dp = os.path.join(DD, bid + '.json')
    d = json.load(open(dp, encoding='utf-8')) if os.path.exists(dp) else {}
    n_detail = d.get('chapterCount', '?')
    # books.json
    books = json.load(open(B + '/app/public/books.json', encoding='utf-8'))
    b = next((x for x in books if x.get('id') == bid), None)
    n_book = b.get('chapterCount', '?') if b else '?'
    flags = []
    if n_pub != n_meta + 1:
        flags.append('public=%d≠%d' % (n_pub, n_meta + 1))
    if n_detail != n_meta:
        flags.append('detail=%s≠%d' % (n_detail, n_meta))
    if n_book != n_meta:
        flags.append('books=%s≠%d' % (n_book, n_meta))
    print('%-50s meta=%d %s' % (rel[:46], n_meta, ' | '.join(flags) if flags else 'OK'))
