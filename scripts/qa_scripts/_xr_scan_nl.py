# -*- coding: utf-8 -*-
"""全书扫描：text 块含 \n 的书/章（段内物理换行病），排除 _old_bad* 备份"""
import json, os, sys
sys.stdout.reconfigure(encoding='utf-8')

BC = 'f:/program/Python/PhiAgent/backend/data/book_chapters'
bad = []
for bid in sorted(os.listdir(BC)):
    d = os.path.join(BC, bid)
    if not os.path.isdir(d) or '_old_bad' in bid:
        continue
    if not os.path.exists(os.path.join(d, 'meta.json')):
        continue
    try:
        m = json.load(open(os.path.join(d, 'meta.json'), encoding='utf-8'))
    except Exception:
        continue
    title = m.get('title', '')[:20]
    nl_ch = []   # (idx, 块数, nl数)
    for f in os.listdir(d):
        if not f.endswith('.json') or f == 'meta.json':
            continue
        idx = f[:-5]
        try:
            ch = json.load(open(os.path.join(d, f), encoding='utf-8'))
        except Exception:
            continue
        n_blk = n_nl = 0
        for b in ch.get('content', []):
            if b.get('type') == 'text':
                c = b.get('value', '').count('\n')
                if c:
                    n_blk += 1
                    n_nl += c
        if n_nl:
            nl_ch.append((idx, n_blk, n_nl))
    if nl_ch:
        tot_blk = sum(x[1] for x in nl_ch)
        tot_nl = sum(x[2] for x in nl_ch)
        bad.append((bid, title, len(nl_ch), tot_blk, tot_nl, nl_ch[:5]))

print('含 \\n 的书 %d 本:' % len(bad))
for bid, t, nch, nblk, nnl, ex in sorted(bad, key=lambda x: -x[4]):
    print('%s %-16s 章%d 块%d \\n%d 例:%s' % (bid, t, nch, nblk, nnl, ex[:2]))
