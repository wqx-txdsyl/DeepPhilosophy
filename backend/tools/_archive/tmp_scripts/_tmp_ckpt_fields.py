# -*- coding: utf-8 -*-
"""ckpt books 条目完整字段 + 是否有 ok/done 标记"""
import json

ck = json.load(open(r'F:\program\Python\DeepPhilosophy\DeepPhilosophy\backend\data\dp_pdf_import_ckpt.json', encoding='utf-8'))
books = ck['books']
# 收集所有字段名
keys = set()
for v in books.values():
    keys.update(v.keys())
print('books 条目字段:', sorted(keys))
# 找含 ok/done/status 的字段
for k, v in books.items():
    if any(x in k.lower() for x in ['ok', 'done', 'status', 'state', 'finish', 'complete']):
        print('  含标记:', k, v)
# 打印每本完整记录（前 30 本）
print()
for i, (rel, v) in enumerate(books.items()):
    print('%-55s %s' % (rel[:50], v))
    if i > 30:
        print('  ...')
        break
