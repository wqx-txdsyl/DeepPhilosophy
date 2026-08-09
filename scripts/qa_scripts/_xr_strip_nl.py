# -*- coding: utf-8 -*-
"""清除 text 块值内的物理换行 \n（散文段内行断点 → 右半空白根因）
用法: python _xr_strip_nl.py <bid> [bid...]   # 全书全部章
"""
import json, os, sys
sys.stdout.reconfigure(encoding='utf-8')

PA_BC = 'f:/program/Python/PhiAgent/backend/data/book_chapters'

for bid in sys.argv[1:]:
    d = os.path.join(PA_BC, bid)
    if not os.path.isdir(d):
        print('无此目录:', bid)
        continue
    total = 0
    for f in sorted(os.listdir(d), key=lambda x: int(x[:-5]) if x.endswith('.json') and x != 'meta.json' else -1):
        if not f.endswith('.json') or f == 'meta.json':
            continue
        p = os.path.join(d, f)
        ch = json.load(open(p, encoding='utf-8'))
        n = 0
        for b in ch.get('content', []):
            if b.get('type') == 'text' and '\n' in b.get('value', ''):
                b['value'] = b['value'].replace('\n', '')
                n += 1
        if n:
            json.dump(ch, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
            total += n
            print('  %s 清 \n 块 %d' % (f, n))
    print('%s 共清 %d 块' % (bid, total))
