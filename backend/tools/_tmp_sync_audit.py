# -*- coding: utf-8 -*-
"""盘点: meta.json toc vs book_detail toc 一致性 + 找出读《资本论》的超长块"""
import json, os

B = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy'
META_DIR = os.path.join(B, 'backend', 'data', 'book_chapters')
DETAIL_DIR = os.path.join(B, 'backend', 'data', 'book_detail')

def to_key(toc):
    """toc 归一化为 (type|title) 列表, 兼容字符串/字典两种形式"""
    if not toc or not isinstance(toc, list):
        return []
    out = []
    for t in toc:
        if isinstance(t, dict):
            out.append((t.get('type'), str(t.get('title', ''))))
        else:
            out.append(('chapter', str(t)))
    return out

print('=== meta vs detail toc 不一致的书 ===')
mismatch = []
for d in sorted(os.listdir(DETAIL_DIR), key=lambda x: int(x.split('.')[0]) if x.split('.')[0].isdigit() else 0):
    bid = d[:-5]
    mpath = os.path.join(META_DIR, bid, 'meta.json')
    if not os.path.exists(mpath):
        continue
    meta = json.load(open(mpath, encoding='utf-8'))
    detail = json.load(open(os.path.join(DETAIL_DIR, d), encoding='utf-8'))
    mt = to_key(meta.get('toc'))
    dt = to_key(detail.get('toc'))
    if meta.get('chapterCount') != detail.get('chapterCount') or mt != dt:
        n1, n2 = len(mt), len(dt)
        flag = 'COUNT' if meta.get('chapterCount') != detail.get('chapterCount') else 'TOC'
        print('%s %-20s meta:%d detail:%d [%s]' % (bid, meta.get('title', '?')[:18], n1, n2, flag))
        mismatch.append(bid)

print()
print('不一致总数:', len(mismatch))
