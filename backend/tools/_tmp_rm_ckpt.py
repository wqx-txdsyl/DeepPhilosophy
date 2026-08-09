# -*- coding: utf-8 -*-
"""删 ckpt 登记(仅 books dict, 保留 ocr dict), 供 --only 重跑重建"""
import json, re, sys

CKPT = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/dp_pdf_import_ckpt.json'
target = sys.argv[1]
ckpt = json.load(open(CKPT, encoding='utf-8'))
books = ckpt.get('books', {})
hit = [k for k in books if target in k]
for k in hit:
    safe = re.sub(r'[^\w\-.]', '_', k)
    print('删除登记:', k, '| ocr 键:', safe in ckpt.get('ocr', {}))
    del books[k]
json.dump(ckpt, open(CKPT, 'w', encoding='utf-8'), ensure_ascii=False)
print('剩余 books 登记:', len(books))
