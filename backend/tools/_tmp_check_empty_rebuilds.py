# -*- coding: utf-8 -*-
"""盘点: ckpt 有 OCR 文本但 book_chapters 缺失/空/异常的批次书"""
import json, os, hashlib, re

CKPT = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/dp_pdf_import_ckpt.json'
BC = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters'
PUB = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters'
MISS = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/missing_pages.json'

ckpt = json.load(open(CKPT, encoding='utf-8'))
ocr = ckpt.get('ocr', {})

print('=== ckpt OCR 完成的书（按提交时间）===')
rows = []
for safe, pages in ocr.items():
    if not pages:
        continue
    bad = [k for k, v in pages.items() if v == '__FAILED__']
    good = {k: v for k, v in pages.items() if v and v != '__FAILED__'}
    chars = sum(len(v) for v in good.values())
    # 从 books dict 找 rel
    rel = None
    for r, b in ckpt.get('books', {}).items():
        if re.sub(r'[^\w\-.]', '_', r) == safe:
            rel = r
            break
    if not rel:
        rel = safe
    bid = hashlib.md5(rel.encode()).hexdigest()[:12]
    d = os.path.join(BC, bid)
    exists = os.path.isdir(d)
    nchars = 0
    nch = 0
    if exists:
        for f in os.listdir(d):
            if re.match(r'^\d+\.json$', f):
                try:
                    ch = json.load(open(os.path.join(d, f), encoding='utf-8'))
                    nch += 1
                    nchars += sum(len(b.get('value', '')) for b in ch.get('content', []))
                except Exception:
                    pass
    rows.append((len(good), chars, bad, rel, bid, exists, nch, nchars))

rows.sort(key=lambda r: r[1])
print('%-56s %6s %8s %4s %6s %6s %6s' % ('rel', '页数', 'OCR字符', 'FAIL', '章数', '重建字符', '是否空'))
for pages, chars, bad, rel, bid, exists, nch, nchars in rows:
    flag = ''
    if not exists:
        flag = '<< 无重建目录'
    elif nchars < 1000:
        flag = '<< 空重建(<1K)'
    elif nchars < chars * 0.3:
        flag = '<< 重建异常(远小于OCR)'
    print('%-56s %6d %8d %4d %6d %6d %s' % (rel[:56], pages, chars, len(bad), nch, nchars, flag))
