# -*- coding: utf-8 -*-
"""查看 OCR 检查点: 已完成 vs 进行中, 各书状态"""
import json, os

ck = json.load(open(r'F:\program\Python\DeepPhilosophy\DeepPhilosophy\backend\data\dp_pdf_import_ckpt.json', encoding='utf-8'))
print('顶层键:', list(ck.keys()))

books = ck.get('books', {})
ocr = ck.get('ocr', {})
print('books 条目:', len(books), '| ocr 条目:', len(ocr))
print()
print('=== books（已完成重建的书）===')
for rel, v in books.items():
    print('  %-60s %s' % (rel, v))
print()
print('=== ocr（OCR 中/已 OCR 待重建的书）===')
for rel, pages in ocr.items():
    status = []
    if isinstance(pages, dict):
        for k, v in list(pages.items())[:3]:
            status.append('%s: %s字' % (k, len(v) if isinstance(v, str) else v))
    print('  %-60s %d页 %s' % (rel, len(pages) if isinstance(pages, dict) else 0, ' | '.join(status)))
