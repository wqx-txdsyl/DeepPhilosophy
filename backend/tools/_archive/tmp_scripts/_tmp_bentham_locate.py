# -*- coding: utf-8 -*-
"""定位边沁正文所在章节 + 总目录页码结构"""
import json, os

D = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/74ee21ced920'
meta = json.load(open(os.path.join(D, 'meta.json'), encoding='utf-8'))

# 每章字符量排序
stats = []
for i in range(meta['chapterCount']):
    ch = json.load(open(os.path.join(D, '%d.json' % i), encoding='utf-8'))
    c = sum(len(b.get('value', '')) for b in ch.get('content', []))
    stats.append((c, i, ch['title'][:35]))
stats.sort(reverse=True)
print('字符量 Top 15 章:')
for c, i, t in stats[:15]:
    print('  [%d] %5d字符 %s' % (i, c, t))
print()
print('1 块以下的小章数:', sum(1 for c, i, t in stats if c < 100))

# 正文标志句在哪章
for i in range(meta['chapterCount']):
    ch = json.load(open(os.path.join(D, '%d.json' % i), encoding='utf-8'))
    txt = ' '.join(b['value'] for b in ch['content'])
    if '自然把人类置于' in txt:
        print()
        print('正文[自然把人类置于] 在章 %d (%s)' % (i, ch['title'][:35]))
        # 打印该章开头
        print('  章开头: %s' % txt[:120])
        break
