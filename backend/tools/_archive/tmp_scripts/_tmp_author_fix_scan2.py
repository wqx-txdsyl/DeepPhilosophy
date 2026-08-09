# -*- coding: utf-8 -*-
"""系列书 → books.json 条目匹配: 找出作者=哲学家本人的条目"""
import json, os

BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy'
bj = json.load(open(BASE + '/app/public/books.json', encoding='utf-8'))
items = bj if isinstance(bj, list) else bj.get('books', [])
by_id = {it.get('id'): it for it in items}

# 系列书哲学家名 (PDF 文件名去掉系列名)
series = []
for root, dirs, files in os.walk(r'F:/philosophy'):
    for fn in files:
        if fn.startswith('最伟大的思想家'):
            name = fn.replace('最伟大的思想家 - ', '').replace('.pdf', '')
            series.append((name, os.path.join(root, fn)))
print('== 系列 PDF (%d 本) ==' % len(series))
for name, p in sorted(series):
    # 找 books.json 中 title 完全等于哲学家名 或含哲学家的条目
    cands = [it for it in items if it.get('title') == name or (name and name in it.get('title', ''))]
    if cands:
        for it in cands:
            flag = ''
            if it.get('author') == name or (name in (it.get('author') or '') and len(it.get('author', '')) <= 6):
                flag = '  ← 作者疑似本人, 需修正'
            print('%-10s | books: %-30s | 作者: %-24s | %s%s' % (
                name, it.get('title', '')[:28], it.get('author', '')[:22], it.get('id'), flag))
    else:
        print('%-10s | (books.json 无匹配条目)' % name)
