# -*- coding: utf-8 -*-
"""回答用户：pdf 未入库清单 + 维特根斯坦章1手稿号 + 三十六计 epub 源"""
import json, os, re, glob

# 1) pdf 入库状态：books.json 全量 vs checkpoint books 键 vs 实际 chapters
bk = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json', encoding='utf-8'))
ck = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/dp_pdf_import_ckpt.json', encoding='utf-8'))
ck_books = set(ck.get('books', {}).keys())
print('books.json 总数:', len(bk))
# 找 file_type=pdf 的书
pdfs = [b for b in bk if b.get('file_type') == 'pdf']
print('books.json 中 pdf 已入库:', len(pdfs))
print('checkpoint books 键(已写入 chapters 的 pdf):', len(ck_books))
for k in sorted(ck_books):
    print('   ', k)
print()
# 2) 维特根斯坦 章1 手稿号：搜日期之外的标识
c = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/c0e78ea6f80a/1.json', encoding='utf-8'))
ps = [b.get('value', '').strip() for b in c['content'] if isinstance(b, dict) and isinstance(b.get('value'), str) and b['value'].strip()]
print('=== 维特根斯坦 章1 前 20 段（找手稿号/卷标识）===')
for p in ps[:20]:
    print('   ', p[:80])
print()
# 3) 三十六计 epub 源：找 F:/philosophy 下文件
hits = []
for root, dirs, files in os.walk('F:/philosophy'):
    for f in files:
        if '三十六' in f or '三十六计' in root:
            hits.append(os.path.join(root, f))
print('=== 三十六计 源文件 ===')
for h in hits:
    print('   ', h)
