# -*- coding: utf-8 -*-
"""16 本 OCR 书的块结构诊断: 每本最大块长/超长块数(>2400, >6000)"""
import json, os, hashlib

B = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy'
CD = B + '/backend/data/book_chapters'
ck = json.load(open(B + '/backend/data/dp_pdf_import_ckpt.json', encoding='utf-8'))

rels = [rel for rel, v in ck['books'].items() if v.get('src') == 'ocr']
for rel in rels:
    bid = hashlib.md5(rel.encode()).hexdigest()[:12]
    cdir = os.path.join(CD, bid)
    mp = os.path.join(cdir, 'meta.json')
    if not os.path.exists(mp):
        print('%-50s 无 meta!' % rel[:46])
        continue
    m = json.load(open(mp, encoding='utf-8'))
    n = m['chapterCount']
    total = 0
    maxblock = 0
    over2400 = 0
    over6000 = 0
    bigch = 0
    for i in range(n):
        p = os.path.join(cdir, '%d.json' % i)
        if not os.path.exists(p):
            continue
        ch = json.load(open(p, encoding='utf-8'))
        bl = ch.get('content', [])
        sz = sum(len(b.get('value', '')) for b in bl if b.get('type') == 'text')
        total += sz
        if sz > 60000:
            bigch += 1
        for b in bl:
            if b.get('type') == 'text':
                l = len(b.get('value', ''))
                maxblock = max(maxblock, l)
                if l > 2400:
                    over2400 += 1
                if l > 6000:
                    over6000 += 1
    print('%-52s 章=%d 总=%d 最大块=%d 超2400=%d 超6000=%d 超大章(>60K)=%d' % (
        rel[:48], n, total, maxblock, over2400, over6000, bigch))
