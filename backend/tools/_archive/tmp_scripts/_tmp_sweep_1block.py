# -*- coding: utf-8 -*-
"""盘点 DeepPhilosophy 全库 1-block 章节（判定异常 vs 正常）:
- 1 块且字符 >1500 → 异常（多页章挤成 1 块）
- 1 块且字符 <=1500 → 正常（短章 1 页/行式块）
- 顺便统计: 块含物理换行的散文块残留（_xr_nl_fix 标准未达标）"""
import json, os, re

PA_BC = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters'

suspects = []   # (bid, 章号, 标题, 字符数)
nl_resid = []   # (bid, 章号, 块数, 残留物理换行的散文块数)
total_books = 0
total_ch = 0
for bid in sorted(os.listdir(PA_BC)):
    d = os.path.join(PA_BC, bid)
    if not os.path.isdir(d):
        continue
    meta_p = os.path.join(d, 'meta.json')
    if not os.path.exists(meta_p):
        continue
    meta = json.load(open(meta_p, encoding='utf-8'))
    total_books += 1
    for f in sorted(os.listdir(d), key=lambda x: int(x[:-5]) if x.endswith('.json') and x != 'meta.json' else -1):
        if not f.endswith('.json') or f == 'meta.json':
            continue
        total_ch += 1
        ch = json.load(open(os.path.join(d, f), encoding='utf-8'))
        blocks = ch.get('content', [])
        text_blocks = [b for b in blocks if b.get('type') == 'text']
        if len(text_blocks) <= 1:
            size = sum(len(b.get('value', '')) for b in text_blocks)
            if size > 1500:
                suspects.append((bid, f[:-5], ch.get('title', '?')[:20], size))
        # 物理换行残留检查: 块值内单 \n 且非行式
        for b in text_blocks:
            v = b.get('value', '')
            if '\n' in v:
                lines = [l for l in v.split('\n') if l.strip()]
                if len(lines) >= 3 and max(len(l) for l in lines) > 20:
                    nl_resid.append((bid, f[:-5], len(text_blocks), v.count('\n')))

print('总书数: %d | 总章数: %d' % (total_books, total_ch))
print()
print('=== 异常 1-block 章节 (1块且>1500字符): %d 条 ===' % len(suspects))
from collections import Counter
per_book = Counter(s[0] for s in suspects)
for bid, n in sorted(per_book.items(), key=lambda x: -x[1]):
    print('  %s: %d 章异常 %s' % (bid, n, str([(s[1], s[2], s[3]) for s in suspects if s[0] == bid])))
print()
print('=== 散文块物理换行残留: %d 条 ===' % len(nl_resid))
per_book2 = Counter(r[0] for r in nl_resid)
for bid, n in sorted(per_book2.items(), key=lambda x: -x[1])[:30]:
    print('  %s: %d 章' % (bid, n))
