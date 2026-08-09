# -*- coding: utf-8 -*-
"""扫描 '最伟大的思想家' 系列 + 导读类书: books.json 现状 vs 磁盘 PDF"""
import json, os

BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy'
bj = json.load(open(BASE + '/app/public/books.json', encoding='utf-8'))
items = bj if isinstance(bj, list) else bj.get('books', [])

print('== 磁盘上的系列 PDF ==')
for root, dirs, files in os.walk(r'F:/philosophy'):
    for fn in files:
        if fn.startswith('最伟大的思想家'):
            print('  %s/%s' % (os.path.relpath(root, r'F:/philosophy'), fn))

print()
print('== books.json 中标题被改过的系列书 (含系列名或无系列名) ==')
for it in items:
    t = it.get('title', '')
    a = it.get('author', '')
    if '最伟大的思想家' in t:
        print('  [系列名在] %-28s | %s | %s' % (t[:26], a[:20], it.get('id')))
print()
# 找出作者可疑的书: 作者=哲学家本人但书是传记/导读
for it in items:
    t = it.get('title', '')
    a = it.get('author', '')
    # 纯人名标题 (可能是系列书改标题后的)
    ids = it.get('id')
    print('%s | %s | %s' % (t[:36], a[:24], ids))
