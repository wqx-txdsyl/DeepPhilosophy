# -*- coding: utf-8 -*-
"""全量体检：403 本 detail 字段完整性 + toc 格式（找所有'加载方式不一样'的书）"""
import os, json, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DIR = 'f:/program/Python/PhiAgent/backend/data/book_detail'
FIELDS = ['summary', 'tags', 'region', 'file_type', 'extract']

issues = {}   # bid -> {缺失字段: []}
toc_flat = []  # toc 纯字符串平铺（前端读不到层级目录）
toc_double = []  # toc 双重编码

total = 0
for f in sorted(os.listdir(DIR)):
    if not f.endswith('.json'):
        continue
    total += 1
    bid = f[:-5]
    try:
        d = json.load(open(os.path.join(DIR, f), encoding='utf-8'))
    except Exception as e:
        issues[bid] = ['JSON损坏: %s' % e]
        continue
    miss = [k for k in FIELDS if not d.get(k)]
    toc = d.get('toc') or []
    if toc and isinstance(toc[0], str):
        if toc[0].lstrip().startswith("{'"):
            toc_double.append(bid)
        else:
            toc_flat.append(bid)
    if miss:
        issues[bid] = miss

print('总数: %d' % total)
print()
print('== 缺字段的书 (%d 本) ==' % len(issues))
for bid, miss in sorted(issues.items()):
    t = ''
    try:
        t = json.load(open(os.path.join(DIR, bid + '.json'), encoding='utf-8')).get('title', '')
    except Exception:
        pass
    print('  %s %s 缺: %s' % (bid, t[:30], miss))
print()
print('== toc 纯字符串平铺 (无层级, %d 本) ==' % len(toc_flat))
print(' ', toc_flat)
print()
print('== toc 双重编码 (%d 本) ==' % len(toc_double))
print(' ', toc_double)
