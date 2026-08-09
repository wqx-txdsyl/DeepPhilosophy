# -*- coding: utf-8 -*-
"""扫描柏拉图正文: 篇首锚点(谈话人行 + 附录标题), 输出切分边界"""
import json, os, re

CD = r'F:\program\Python\DeepPhilosophy\DeepPhilosophy\backend\data\book_chapters\35279e2e439d'

# 合并 3,4 为连续块流
blocks = []
for fi in (3, 4):
    ch = json.load(open(os.path.join(CD, '%d.json' % fi), encoding='utf-8'))
    for b in ch.get('content', []):
        blocks.append((fi, b.get('value', '')))

print('总块数:', len(blocks))

# 篇首锚点 1: 谈话人行
print()
print('=== "谈话人" 出现处 ===')
for i, (fi, v) in enumerate(blocks):
    for line in v.split('\n'):
        if '谈话人' in line:
            print('  全局块%4d (来自%d.json) %r' % (i, fi, line.strip()[:60]))
            break

# 篇首锚点 2: 附录标题(独立短行, 非页眉)
print()
print('=== 附录标题候选 ===')
app_pat = re.compile(r'^(苏格拉底、柏拉图传|亚里士多德论柏拉图|柏拉图关于"是"的学说|王太庆论柏拉图哲学和翻译问题)$')
for i, (fi, v) in enumerate(blocks):
    for line in v.split('\n'):
        if app_pat.match(line.strip()):
            print('  全局块%4d (来自%d.json) %r' % (i, fi, line.strip()[:50]))
            break

# 篇首锚点 3: 每篇正文第一块内容预览(在谈话人块前后)
print()
print('=== 篇首块上下文(锚点块-1 到 +1) ===')
for i, (fi, v) in enumerate(blocks):
    if '谈话人' in v and len(v) < 300:
        print('--- 全局块 %d ---' % i)
        for j in range(max(0, i - 1), min(len(blocks), i + 2)):
            print('   [%d] %s' % (j, blocks[j][1][:80].replace('\n', '⏎')))
