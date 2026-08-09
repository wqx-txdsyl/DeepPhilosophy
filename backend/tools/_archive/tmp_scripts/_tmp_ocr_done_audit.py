# -*- coding: utf-8 -*-
"""盘点 src: ocr 已完成重建的书: 章节数/字符量/块结构 vs OCR 缓存页数"""
import json, os, hashlib

B = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy'
CD = B + '/backend/data/book_chapters'
DD = B + '/backend/data/book_detail'
ck = json.load(open(B + '/backend/data/dp_pdf_import_ckpt.json', encoding='utf-8'))

ocr_books = [(rel, v) for rel, v in ck['books'].items() if v.get('src') == 'ocr']
print('src: ocr 已登记:', len(ocr_books))
print()

for rel, v in ocr_books:
    bid = hashlib.md5(rel.encode()).hexdigest()[:12]
    cdir = os.path.join(CD, bid)
    meta = None
    if os.path.exists(os.path.join(cdir, 'meta.json')):
        meta = json.load(open(os.path.join(cdir, 'meta.json'), encoding='utf-8'))
    n_ch = meta.get('chapterCount', 0) if meta else 0
    total = 0
    maxch = 0
    blocks = 0
    for i in range(n_ch):
        p = os.path.join(cdir, '%d.json' % i)
        if not os.path.exists(p):
            continue
        ch = json.load(open(p, encoding='utf-8'))
        bl = ch.get('content', [])
        sz = sum(len(b.get('value', '')) for b in bl if b.get('type') == 'text')
        total += sz
        maxch = max(maxch, sz)
        blocks += len(bl)
    # OCR 缓存页数
    ocr_key = rel.replace('/', '_').replace('（', '_').replace('）', '_').replace('《', '_').replace('》', '_').replace('·', '_').replace('：', '_').replace(':', '_') + '.pdf'
    pages = ck['ocr'].get(ocr_key, {})
    print('%-52s 登记ch=%s 实际章=%d 总字符=%d 最大章=%d 块=%d ocr页=%d' % (
        rel[:48], v.get('chapters'), n_ch, total, maxch, blocks, len(pages) if isinstance(pages, dict) else 0))
