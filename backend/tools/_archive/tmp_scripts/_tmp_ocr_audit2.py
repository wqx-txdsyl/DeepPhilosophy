# -*- coding: utf-8 -*-
"""OCR 队列审计: 全部 PDF vs 已入库 books vs ocr 进度 → 未完成清单"""
import json, os, re

BASE = r'F:\program\Python\DeepPhilosophy\DeepPhilosophy'
BOOKS_DIR = r"F:/philosophy"
CK = os.path.join(BASE, 'backend', 'data', 'dp_pdf_import_ckpt.json')
ck = json.load(open(CK, encoding='utf-8'))
books = ck.get('books', {})
ocr = ck.get('ocr', {})

pdfs = []
for region in ['东方', '西方']:
    rp = os.path.join(BOOKS_DIR, region)
    if not os.path.isdir(rp):
        print('目录不存在:', rp)
        continue
    for author in sorted(os.listdir(rp)):
        ap = os.path.join(rp, author)
        if not os.path.isdir(ap):
            continue
        for fn in sorted(os.listdir(ap)):
            if fn.lower().endswith('.pdf'):
                rel = os.path.relpath(os.path.join(ap, fn), BOOKS_DIR).replace('\\', '/')
                pdfs.append((rel, region, author, fn))
print('全部 PDF: %d 本' % len(pdfs))
print('books 已入库: %d 本' % len(books))

# 未入库 PDF
todo = []
for rel, region, author, fn in pdfs:
    if rel in books:
        continue
    safe_key = re.sub(r'[^\w\-.]', '_', rel)
    o = ocr.get(safe_key)
    state = ''
    if o:
        done = sum(1 for x in o.values() if isinstance(x, str) and len(x) > 5)
        state = 'OCR %d/%d' % (done, len(o))
    todo.append((rel, state))
print()
print('== 未入库 PDF: %d 本 ==' % len(todo))
for rel, state in sorted(todo):
    print('  %s  [%s]' % (rel, state or '未开始'))
