# -*- coding: utf-8 -*-
"""139 批次摸底②：pdf 49 本清单 + OCR checkpoint 对应关系"""
import json, os

bk = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json', encoding='utf-8'))
pdfs = [b for b in bk if b.get('file_type') == 'pdf' and (b.get('chapterCount') or 0) == 0]
print('pdf 且 cc=0:', len(pdfs))
ck = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/dp_pdf_import_ckpt.json', encoding='utf-8'))
ck_books = set(ck.get('books', {}).keys())
ck_ocr = set(ck.get('ocr', {}).keys())

with open('C:/Users/wqx_0/AppData/Local/Temp/pdf49_list.txt', 'w', encoding='utf-8') as f:
    for b in pdfs:
        f.write('%s | %s | %s\n' % (b.get('id'), b.get('title'), b.get('author')))

print()
print('=== 49 本 pdf 清单 ===')
for b in pdfs:
    print('  %s | %s | %s' % (b.get('id'), (b.get('title') or '')[:34], (b.get('author') or '')[:16]))
print()
# OCR 进度：checkpoint books 键（已完成章节化的 pdf）与 49 本的关系
print('=== OCR 引擎状态 ===')
print('checkpoint books 键(已章节化): %d 个' % len(ck_books))
print('checkpoint ocr 键(页级文本缓存): %d 个' % len(ck_ocr))
