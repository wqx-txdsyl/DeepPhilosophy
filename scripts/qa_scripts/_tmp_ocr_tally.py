# -*- coding: utf-8 -*-
"""临时：按 dp_pdf_import.py 扫描逻辑统计待 OCR 书目"""
import json, os, re, hashlib

BOOKS_DIR = 'F:/philosophy'
CDIR = 'f:/program/Python/PhiAgent/backend/data/book_chapters'
MERGE_RULES = {
    '西方/弗里德里希·恩格斯/MEGA：陶伯特版《德意志意识形态·费尔巴哈》.pdf': None,
    '西方/弗里德里希·恩格斯/共产党宣言.pdf': None,
    '西方/弗里德里希·恩格斯/德意志意识形态（节选本）.pdf': None,
    '西方/波爱修斯/哲学规劝录 哲学的慰藉.pdf': None,
    '西方/让-保罗·萨特/存在与虚无.pdf': None,
    '西方/柏拉图/理想国.pdf': None,
}
pdfs = []
for region in ['东方', '西方']:
    rp = os.path.join(BOOKS_DIR, region)
    for author in sorted(os.listdir(rp)):
        ap = os.path.join(rp, author)
        if not os.path.isdir(ap):
            continue
        for fn in sorted(os.listdir(ap)):
            fp = os.path.join(ap, fn)
            if not os.path.isfile(fp):
                continue
            rel = os.path.relpath(fp, BOOKS_DIR).replace(os.sep, '/')
            if rel in MERGE_RULES:
                continue
            if fn.lower().endswith('.pdf'):
                pdfs.append({'rel': rel, 'file': fn})
print('扫描列表(MERGE后):', len(pdfs))

def has_valid(bid):
    return os.path.exists(os.path.join(CDIR, bid, 'meta.json'))

no_ch = []
for b in pdfs:
    bid = hashlib.md5(b['rel'].encode()).hexdigest()[:12]
    if not has_valid(bid):
        no_ch.append((bid, b['rel']))
print('无有效章节(待处理):', len(no_ch))
for bid, rel in no_ch:
    print(' ', bid, rel)
