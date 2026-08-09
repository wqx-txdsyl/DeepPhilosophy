# -*- coding: utf-8 -*-
"""形而上学 133 章诊断: 章标题模式 + 前 40 章标题 + 小章内容"""
import json, os, re

bid = None
for r in ['西方/亚里士多德/形而上学.pdf']:
    import hashlib
    bid = hashlib.md5(r.encode()).hexdigest()[:12]
print('bid:', bid)
D = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/%s' % bid
files = sorted([f for f in os.listdir(D) if re.match(r'^\d+\.json$', f)], key=lambda x: int(x.split('.')[0]))
print('章数:', len(files))

# 每章: 标题 + 字符量 + 首块开头
small = []
for fn in files:
    ch = json.load(open(os.path.join(D, fn), encoding='utf-8'))
    n = sum(len(b.get('value', '')) for b in ch.get('content', []))
    head = ''
    if ch.get('content'):
        head = ch['content'][0].get('value', '')[:40]
    if n < 200:
        small.append((ch['index'], ch.get('title', ''), n, head))
    if ch['index'] < 25:
        print('[%03d] %-12s %6d | %s' % (ch['index'], str(ch.get('title'))[:12], n, head))

print()
print('小章(<200字符) 数量:', len(small))
for s in small[:30]:
    print('  [%03d] %-12s %6d | %s' % s)
