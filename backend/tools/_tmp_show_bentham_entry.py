# -*- coding: utf-8 -*-
import json

for p in ['f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/src/assets/books.json',
          'f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json']:
    books = json.load(open(p, encoding='utf-8'))
    print('=====', p)
    hits = [b for b in books if b.get('bookId') == '74ee21ced920']
    if hits:
        print(json.dumps(hits[0], ensure_ascii=False, indent=1)[:2000])
    else:
        print('  无 74ee21ced920 条目')
    # 顺带检查 边沁 相关标题
    for b in books:
        t = str(b.get('title', ''))
        if '边沁' in t or '功利' in t:
            print('  相关:', b.get('bookId'), t)
