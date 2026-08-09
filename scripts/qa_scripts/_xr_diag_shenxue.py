# -*- coding: utf-8 -*-
"""诊断：神学大全两卷 文件名/id/缓存key 一致性"""
import os, hashlib, json, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

kd = 'F:/philosophy'
print('== F盘文件名 ==')
for root, dirs, files in os.walk(kd):
    for f in files:
        if '神学大全' in f:
            full = os.path.join(root, f)
            rel = os.path.relpath(full, kd).replace('\\', '/')
            print('文件名:', repr(f))
            print('rel   :', repr(rel))
            print('scan_id:', hashlib.md5(rel.encode()).hexdigest()[:12])

print()
print('== 缓存key ==')
cache = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_summaries.json', encoding='utf-8'))
for k in cache:
    if '神学大全' in k:
        print(repr(k))

print()
print('== books.json 条目 ==')
b = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json', encoding='utf-8'))
for x in b:
    if '神学大全' in x.get('title', ''):
        print(x.get('id'), repr(x.get('title')), x.get('file_type'), x.get('chapterCount'))

print()
print('== DP backend/data 是否有 book_summaries 之外的其他 books 源 ==')
for p in ['f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/books.json']:
    if os.path.exists(p):
        d = json.load(open(p, encoding='utf-8'))
        print(p, '存在 条目数', len(d))
        for x in d:
            if '神学大全' in str(x.get('title', '')):
                print(' ', x.get('id'), repr(x.get('title')))
    else:
        print(p, '不存在')
