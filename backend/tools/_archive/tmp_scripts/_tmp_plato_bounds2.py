# -*- coding: utf-8 -*-
"""确认块1 + 治国篇卷边界 + 超长块统计"""
import json, os, re

CD = r'F:\program\Python\DeepPhilosophy\DeepPhilosophy\backend\data\book_chapters\35279e2e439d'
blocks = []
for fi in (3, 4):
    ch = json.load(open(os.path.join(CD, '%d.json' % fi), encoding='utf-8'))
    for b in ch.get('content', []):
        blocks.append((fi, b.get('value', '')))

print('=== 块 0/1 ===')
for i in (0, 1):
    print('[%d] %s' % (i, blocks[i][1][:200].replace('\n', '⏎')))
    print()

print('=== 治国篇(358-499) 卷边界 ===')
for i in range(358, 500):
    v = blocks[i][1]
    for m in re.finditer(r'(卷二|卷三|卷十|卷一|第二卷|第三卷|第十卷)', v):
        # 只看块内前 60 字符有卷标记的(页眉候选)
        if m.start() < 20:
            print('[%d] %r' % (i, v[:60].replace('\n', '⏎')))
            break

print()
print('=== 超长块统计(>2400字符) ===')
over = [(i, len(blocks[i][1])) for i in range(len(blocks)) if len(blocks[i][1]) > 2400]
print('超长块数:', len(over))
for i, l in over:
    print('  [%d] %d字符 %r' % (i, l, blocks[i][1][:40].replace('\n', '⏎')))
