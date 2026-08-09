# -*- coding: utf-8 -*-
"""最终验证: 打印层级 toc 树 + 各卷字符统计 + 一致性检查"""
import json, os

B = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy'
D = B + '/backend/data/book_chapters/c0e78ea6f80a'

m = json.load(open(D + '/meta.json', encoding='utf-8'))
toc = m['toc']
print('toc:', len(toc), '| chapterTitles:', len(m['chapterTitles']), '| chapterCount:', m['chapterCount'])
print()
vol = None
for t in toc:
    if t['type'] == 'chapter':
        vol = t['title']
        print()
        print('■ %s' % vol)
    else:
        print('   └ [%d] %s' % (t['index'], t['title']))

# 一致性: 所有 section index 有效且 title 与 chapterTitles 一致
err = 0
for t in toc:
    i = t['index']
    if not (0 <= i < m['chapterCount']):
        print('!! 越界 index:', t); err += 1
    elif m['chapterTitles'][i] != t['title']:
        print('!! title 不一致 [%d]: toc=%r meta=%r' % (i, t['title'], m['chapterTitles'][i])); err += 1
print()
print('一致性检查:', '通过' if err == 0 else '%d 处错误' % err)

# 总量
total = sum(sum(len(b.get('value', '')) for b in json.load(open(D + '/%d.json' % i, encoding='utf-8')).get('content', [])) for i in range(130))
print('全库总字符:', total)
