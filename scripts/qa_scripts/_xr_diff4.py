# -*- coding: utf-8 -*-
"""4 本 detail.toc vs meta.toc diff：维特根斯坦/尼采/现象学/认识世界"""
import json, os

DP = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy'
for bid, name in [('c0e78ea6f80a', '维特根斯坦'), ('4cc9d23c7dbf', '尼采'), ('ef76ae88994f', '现象学'), ('c97cb4e6161a', '认识世界')]:
    m = json.load(open(os.path.join(DP, 'backend/data/book_chapters/%s/meta.json' % bid), encoding='utf-8'))
    d = json.load(open(os.path.join(DP, 'app/public/book_detail/%s.json' % bid), encoding='utf-8'))
    print('=' * 20, name, 'meta.toc=%d detail.toc=%d' % (len(m['toc']), len(d.get('toc', []))))
    mt, dt = m['toc'], d.get('toc', [])
    n = max(len(mt), len(dt))
    diffn = 0
    for i in range(n):
        a = mt[i] if i < len(mt) else None
        b = dt[i] if i < len(dt) else None
        if a != b:
            diffn += 1
            if diffn <= 6:
                print('  [%d] meta:  %s' % (i, json.dumps(a, ensure_ascii=False)[:110]))
                print('       detail: %s' % (json.dumps(b, ensure_ascii=False)[:110]))
    print('  差异条目数: %d' % diffn)
    print()
