# -*- coding: utf-8 -*-
"""验证重建终态: 每章块数 + 块值物理 \\n 残留检查"""
import json, os

PA_BC = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters'
for bid in ['dd75d637a2ad', '26f5e0df6d76']:
    D = os.path.join(PA_BC, bid)
    print('=' * 60)
    print(bid, D)
    for f in sorted(os.listdir(D), key=lambda x: int(x[:-5]) if x.endswith('.json') and x != 'meta.json' else -1):
        if not f.endswith('.json') or f == 'meta.json':
            continue
        ch = json.load(open(os.path.join(D, f), encoding='utf-8'))
        blocks = ch.get('content', [])
        n_text = sum(1 for b in blocks if b.get('type') == 'text')
        nl_blocks = [len(b['value'].split('\n')) - 1 for b in blocks if b.get('type') == 'text' and '\n' in b.get('value', '')]
        sizes = [len(b['value']) for b in blocks if b.get('type') == 'text']
        mx = max(sizes) if sizes else 0
        flag = ' <<<' if len(blocks) <= 1 and mx > 1500 else ''
        print('  [%s] 块 %d | 含\\n块 %d%s | 最大块 %d 字符%s' % (
            f[:-5], len(blocks), len(nl_blocks), nl_blocks[:3], mx, flag))
    meta = json.load(open(os.path.join(D, 'meta.json'), encoding='utf-8'))
    print('  meta: %d 章 chapterCount=%s' % (len(meta['toc']), meta.get('chapterCount')))
