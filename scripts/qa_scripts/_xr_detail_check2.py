# -*- coding: utf-8 -*-
"""补查：与神对话 1.json 内容 / 哲学书简章内注N / 哲学导论章12上下文 / 维特根斯坦章0章1"""
import json, re

def load(bid, n):
    return json.load(open(f'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{bid}/{n}.json', encoding='utf-8'))

def paras(c):
    return [b.get('value', '').strip() for b in c['content'] if isinstance(b, dict) and isinstance(b.get('value'), str) and b['value'].strip()]

# 1) 与神对话 1.json（toc [1] 双条目指向同一文件）
c = load('7657ef4a2cd3', 1)
ps = paras(c)
print('=== 7657ef4a2cd3 章1 (%d段) 前3段:' % len(ps))
for p in ps[:3]:
    print('   ', p[:80])
print('   末尾2段:')
for p in ps[-2:]:
    print('   ', p[:80])
print('   首段是否"导读"内容:', '导读' in (ps[0] if ps else ''))
print()

# 2) 哲学书简 章内"注N"（正文段落里）
bid = '5f838ef64e5e'
import glob
files = sorted(glob.glob(f'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{bid}/[0-9]*.json'),
               key=lambda p: int(re.search(r'(\d+)\.json', p).group(1)))
print('=== 5f838ef64e5e 章内含"注\\d+"的段落（每章最多2条）===')
pat = re.compile(r'注\d+')
total = 0
for f in files:
    n = int(re.search(r'(\d+)\.json', f).group(1))
    c = json.load(open(f, encoding='utf-8'))
    ps = paras(c)
    hits = [p for p in ps if pat.search(p)]
    if hits:
        total += len(hits)
        print('  章%d: %d 段命中' % (n, len(hits)))
        for p in hits[:2]:
            print('      ', p[:90])
print('  共 %d 段命中' % total)
print()

# 3) 哲学导论 章12 全段数 + "第N章"式残留段统计
c = load('c13b139d1db3', 12)
ps = paras(c)
print('=== c13b139d1db3 章12 (%d段) 全部短段(<6字):' % len(ps))
for i, p in enumerate(ps):
    if len(p) < 6:
        print('   [%d] %r' % (i, p))
print('   首段后接:', ps[1][:60] if len(ps) > 1 else '')
print()

# 4) 维特根斯坦 章0/1 内容定位（首尾）
for n, label in ((0, 'MS 101 第一段'), (1, 'MS 101 第二段'), (2, '逻辑哲学论')):
    c = load('c0e78ea6f80a', n)
    ps = paras(c)
    print('=== 维特根斯坦 章%d %s: %d 段' % (n, label, len(ps)))
    print('   首段:', ps[0][:100])
    print('   末段:', ps[-1][:100])
print()

# 5) 与神对话 toc 重复 index 全貌：哪几个 index 出现多次
m = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/7657ef4a2cd3/meta.json', encoding='utf-8'))
from collections import Counter
cnt = Counter(t.get('index') for t in m['toc'])
print('=== 7657ef4a2cd3 index 重复条目:')
for idx, n in cnt.items():
    if n > 1:
        titles = [t.get('title') for t in m['toc'] if t.get('index') == idx]
        print('  index=%d x%d: %s' % (idx, n, titles))
print('toc 共 %d 条, 文件数:' % len(m['toc']))
import os
nd = len([x for x in os.listdir('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/7657ef4a2cd3') if x.endswith('.json') and x != 'meta.json'])
print('  ', nd)
