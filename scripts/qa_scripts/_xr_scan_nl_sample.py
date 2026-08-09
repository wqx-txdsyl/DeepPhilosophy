# -*- coding: utf-8 -*-
"""抽查 39 本含 \n 书的块形态：每本前 3 个含 \n 块截断 90 字，判断物理行/行式条目"""
import json, os, sys
sys.stdout.reconfigure(encoding='utf-8')

BC = 'f:/program/Python/PhiAgent/backend/data/book_chapters'
bids = sys.argv[1:]
for bid in bids:
    d = os.path.join(BC, bid)
    m = json.load(open(os.path.join(d, 'meta.json'), encoding='utf-8'))
    print('=' * 8, m.get('title', '')[:24], bid)
    shown = 0
    for f in sorted(os.listdir(d), key=lambda x: int(x[:-5]) if x.endswith('.json') and x != 'meta.json' else -1):
        if not f.endswith('.json') or f == 'meta.json':
            continue
        ch = json.load(open(os.path.join(d, f), encoding='utf-8'))
        for b in ch.get('content', []):
            if b.get('type') != 'text' or '\n' not in b.get('value', ''):
                continue
            v = b['value']
            seg = v.replace('\n', '⏎')[:90]
            print('  [%s] %s' % (f[:-5], seg))
            shown += 1
            if shown >= 3:
                break
        if shown >= 3:
            break
