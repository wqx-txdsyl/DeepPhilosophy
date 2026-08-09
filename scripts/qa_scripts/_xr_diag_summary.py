# -*- coding: utf-8 -*-
"""盘点 PA+DP 两端 detail 缺 summary / toc 异常的书"""
import os, json, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def check(dir, label):
    print('=====', label, dir)
    miss_sum, miss_toc_str, total = [], [], 0
    for f in os.listdir(dir):
        if not f.endswith('.json'):
            continue
        total += 1
        p = os.path.join(dir, f)
        try:
            d = json.load(open(p, encoding='utf-8'))
        except Exception as e:
            print('  JSON坏:', f, e)
            continue
        if not d.get('summary'):
            miss_sum.append(f)
        toc = d.get('toc') or []
        if toc and isinstance(toc[0], str) and toc[0].lstrip().startswith("{'") or (toc and isinstance(toc[0], str) and 'type' in toc[0][:30]):
            miss_toc_str.append(f)
    print('  总数 %d | 缺summary %d | toc双重编码 %d' % (total, len(miss_sum), len(miss_toc_str)))
    print('  缺summary:', miss_sum)
    print('  toc异常:', miss_toc_str)

check('f:/program/Python/PhiAgent/backend/data/book_detail', 'PA')
check('f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail', 'DP-public')

# PA 的书单文件在哪
print()
print('== 找 PA books 列表文件 ==')
for p in ['f:/program/Python/PhiAgent/backend/data/books.json',
          'f:/program/Python/PhiAgent/backend/data/book_list.json',
          'f:/program/Python/PhiAgent/app/src/data/books.json']:
    print(p, os.path.exists(p))
