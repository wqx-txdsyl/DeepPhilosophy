# -*- coding: utf-8 -*-
"""台账外批次重建：book_chapters 目录 − catalog 已有 bid → 台账外候选
按有章节数据 / 空目录 / _old_bad 备份 分类"""
import json, os, sys
sys.stdout.reconfigure(encoding='utf-8')

BC = 'f:/program/Python/PhiAgent/backend/data/book_chapters'
cat = json.load(open('f:/program/Python/PhiAgent/backend/data/books_catalog.json', encoding='utf-8'))
cat_ids = set(b.get('id') for b in cat['books'] if b.get('id'))

waiji, bad, empty = [], [], []
for bid in sorted(os.listdir(BC)):
    d = os.path.join(BC, bid)
    if not os.path.isdir(d):
        continue
    if '_old_bad' in bid:
        bad.append(bid)
        continue
    if bid in cat_ids:
        continue
    js = [f for f in os.listdir(d) if f.endswith('.json')]
    meta_p = os.path.join(d, 'meta.json')
    if os.path.exists(meta_p):
        try:
            m = json.load(open(meta_p, encoding='utf-8'))
            waiji.append((bid, m.get('title', '')[:30], m.get('chapterCount', '?')))
            continue
        except Exception:
            pass
    empty.append((bid, len(js)))

print('== 台账外有章节数据 %d 本:' % len(waiji))
for bid, t, cc in sorted(waiji):
    print('  %s %-30s cc=%s' % (bid, t, cc))
print('== 台账外无meta(空/半成品) %d:' % len(empty))
for bid, n in empty:
    print('  %s 文件%d' % (bid, n))
print('== _old_bad 备份 %d:' % len(bad), bad[:10])
