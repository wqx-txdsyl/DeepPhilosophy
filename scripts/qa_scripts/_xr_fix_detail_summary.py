# -*- coding: utf-8 -*-
"""修复缺 summary 的 detail：从 DP books.json 补 summary/tags/region/file_type/extract（PA+DP 两端）
缺 summary 的书：f52ed83b99d9(神学大全6卷) 9ed36aca09c5(神学大全7卷) 7bb94a203c8c(新工具 培根)
"""
import json, os, sys, datetime

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BOOKS = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json'
PA_DETAIL = 'f:/program/Python/PhiAgent/backend/data/book_detail'
DP_DETAIL = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail'
FIX = ['f52ed83b99d9', '9ed36aca09c5', '7bb94a203c8c']

books = json.load(open(BOOKS, encoding='utf-8'))
by_id = {b['id']: b for b in books}

for bid in FIX:
    b = by_id.get(bid)
    if not b:
        print(bid, 'books.json 无此 id!')
        continue
    print('== %s %s' % (bid, b['title']))
    for label, DIR in [('PA', PA_DETAIL), ('DP', DP_DETAIL)]:
        f = os.path.join(DIR, bid + '.json')
        d = json.load(open(f, encoding='utf-8'))
        before = set(d.keys())
        for k in ['summary', 'tags', 'region', 'file_type', 'extract']:
            if k not in d and k in b:
                d[k] = b[k]
        # tags 可能为 list[str]，books.json 里已是 list
        json.dump(d, open(f, 'w', encoding='utf-8'), ensure_ascii=False)
        added = set(d.keys()) - before
        print('  %s: 新增字段 %s | 现有 keys=%d' % (label, sorted(added), len(d.keys())))
    print('  summary 长度: %d' % len(b.get('summary', '')))

# 校验写回后可读
print()
print('== 校验 ==')
for bid in FIX:
    for label, DIR in [('PA', PA_DETAIL), ('DP', DP_DETAIL)]:
        d = json.load(open(os.path.join(DIR, bid + '.json'), encoding='utf-8'))
        print('  %s %s: summary=%d字 tags=%s file_type=%s' % (
            label, bid, len(d.get('summary', '')), d.get('tags'), d.get('file_type')))
