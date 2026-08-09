# -*- coding: utf-8 -*-
"""维特根斯坦文集诊断: 每章真实字符量 + 块结构 + epub 源内部结构"""
import json, os, zipfile, re

B = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy'
D = B + '/backend/data/book_chapters/c0e78ea6f80a'

print('=== 章节数据现状 ===')
for fn in sorted([f for f in os.listdir(D) if f.endswith('.json') and f != 'meta.json'], key=lambda x: int(x.split('.')[0])):
    ch = json.load(open(os.path.join(D, fn), encoding='utf-8'))
    blocks = ch.get('content', [])
    n = sum(len(b.get('value', '')) for b in blocks)
    bad = [b for b in blocks if not isinstance(b, dict) or b.get('type') != 'text']
    head = (blocks[0].get('value', '')[:50].replace('\n', ' ') if blocks else '(无块)')
    print('%s %8d字符 %4d块 非text块:%d | %s' % (fn, n, len(blocks), len(bad), head))

print()
print('=== epub 源内部结构 ===')
for ep in [r'F:/philosophy/西方/路德维希·维特根斯坦/《维特根斯坦文集（套装全8卷）》.epub',
           r'F:/philosophy/new/100本哲学书单全收录/31维特根斯坦文集（套装全8卷）/\《维特根斯坦文集（套装全8卷）》.epub']:
    if not os.path.exists(ep):
        print('不存在:', ep)
        continue
    print('源:', ep)
    with zipfile.ZipFile(ep) as z:
        names = [n for n in z.namelist() if n.lower().endswith(('.html', '.xhtml', '.htm', '.opf'))]
        print('  html/opf 文件数:', len(names))
        for n in names[:40]:
            print('   ', n)
