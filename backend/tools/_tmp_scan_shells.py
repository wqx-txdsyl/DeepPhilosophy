# -*- coding: utf-8 -*-
"""全库盘点: 空壳章(<50字符) / 小章分布 / 章数异常"""
import json, os, re, glob

BC = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters'
meta_files = glob.glob(os.path.join(BC, '*', 'meta.json'))
print('库中书数:', len(meta_files))
print()
print('%-16s %6s %6s %8s %6s %6s  %s' % ('bid', '章数', '空壳', '小章<200', '字符', '页数', '书名'))
for mf in sorted(meta_files):
    bid = os.path.basename(os.path.dirname(mf))
    meta = json.load(open(mf, encoding='utf-8'))
    D = os.path.dirname(mf)
    nch = nshell = nsmall = total = 0
    for f in os.listdir(D):
        if not re.match(r'^\d+\.json$', f):
            continue
        try:
            ch = json.load(open(os.path.join(D, f), encoding='utf-8'))
        except Exception:
            continue
        nch += 1
        n = sum(len(b.get('value', '')) for b in ch.get('content', []))
        total += n
        if n < 50:
            nshell += 1
        elif n < 200:
            nsmall += 1
    print('%-16s %6d %6d %8d %6d  %s' % (bid, nch, nshell, nsmall, total // 1000, str(meta.get('title', ''))[:36]))
