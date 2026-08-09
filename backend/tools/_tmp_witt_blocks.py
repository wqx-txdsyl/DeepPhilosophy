# -*- coding: utf-8 -*-
"""超大章块结构诊断: 块数/最大块长/块长分布 → 决定拆块策略"""
import json

B = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy'
D = B + '/backend/data/book_chapters/c0e78ea6f80a'

for i in [28, 38, 89, 90, 95]:
    ch = json.load(open(D + '/%d.json' % i, encoding='utf-8'))
    blocks = ch.get('content', [])
    lens = [len(b.get('value', '')) for b in blocks if b.get('type') == 'text']
    n = sum(lens)
    big = [l for l in lens if l > 2400]
    print('%d %-30s 字符=%d 块=%d 最大块=%d 超2400块=%d 超6000块=%d' % (
        i, ch.get('title', '')[:26], n, len(blocks), max(lens) if lens else 0,
        len([l for l in lens if l > 2400]), len([l for l in lens if l > 6000])))
    # 超长块样例开头
    for b in blocks:
        v = b.get('value', '')
        if len(v) > 6000:
            print('   超长块样例(%d字符): %s...' % (len(v), v[:50].replace('\n', ' ')))
            break
