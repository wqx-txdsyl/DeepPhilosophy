# -*- coding: utf-8 -*-
"""4 本问题书精查：维特根斯坦/与神对话/哲学书简/哲学导论"""
import json, re

def load(bid, n):
    return json.load(open(f'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{bid}/{n}.json', encoding='utf-8'))

def paras(c):
    return [b.get('value', '').strip() for b in c['content'] if isinstance(b, dict) and isinstance(b.get('value'), str) and b['value'].strip()]

# 1) 维特根斯坦 toc 前 10 条
m = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/c0e78ea6f80a/meta.json', encoding='utf-8'))
print('=== c0e78ea6f80a 维特根斯坦 toc 前10条 ===')
for t in m['toc'][:10]:
    print("  [%s] %s" % (t.get('index'), t.get('title')))
for n in (0, 1, 3):
    ps = paras(load('c0e78ea6f80a', n))
    print('--- 章%d (%d段) 首段: %s' % (n, len(ps), ps[0][:80] if ps else '空'))
print()

# 2) 与神对话 toc 前 10 条
m = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/7657ef4a2cd3/meta.json', encoding='utf-8'))
print('=== 7657ef4a2cd3 与神对话 toc 前10条 ===')
for t in m['toc'][:10]:
    print("  [%s] %s" % (t.get('index'), t.get('title')))
print()

# 3) 哲学书简 标题含"注N"的章
m = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/5f838ef64e5e/meta.json', encoding='utf-8'))
print('=== 5f838ef64e5e 哲学书简 toc（标题含"注"+数字）===')
for t in m['toc']:
    ti = t.get('title', '')
    if re.search(r'注\d+', ti):
        print("  [%s] %s" % (t.get('index'), ti))
print('  toc 前4条:')
for t in m['toc'][:4]:
    print("  [%s] %s" % (t.get('index'), t.get('title')[:50]))
print()

# 4) 哲学导论 章49 首段 + 章12 前5段
c = load('c13b139d1db3', 49)
ps = paras(c)
print('=== c13b139d1db3 哲学导论 章49 (%d段) 首段: %s' % (len(ps), ps[0][:80] if ps else '空'))
m = json.load(open('f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/c13b139d1db3/meta.json', encoding='utf-8'))
print('  章49 标题:', [t.get('title') for t in m['toc'] if t.get('index') == 49])
c12 = load('c13b139d1db3', 12)
p12 = paras(c12)
print('  章12 前5段:')
for p in p12[:5]:
    print('    ', p[:70])
