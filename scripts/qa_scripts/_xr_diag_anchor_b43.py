# -*- coding: utf-8 -*-
"""b43aeb7ccc57 锚点分析：标题是否存在于重排后正文"""
import json, re, sys
sys.stdout.reconfigure(encoding='utf-8')

def norm(s):
    return re.sub(r'\s+', '', s or '')

d0 = 'f:/program/Python/PhiAgent/backend/data/book_chapters/b43aeb7ccc57'
m = json.load(open(d0 + '/meta.json', encoding='utf-8'))
secs = [t for t in m['toc'] if t.get('type') == 'section']
vals = [t['sec'] for t in secs]
print('总section', len(secs), '连续占位', sum(1 for a, b in zip(vals, vals[1:]) if b == a + 1), '/', len(vals) - 1)

for idx in range(0, 10):
    try:
        d = json.load(open('%s/%d.json' % (d0, idx), encoding='utf-8'))
    except FileNotFoundError:
        continue
    vs = [norm(b.get('value', '')) for b in d['content'] if b.get('type') == 'text']
    miss = [t for t in secs if t.get('index') == idx
            and not any(norm(v) == norm(t['title']) for v in vs)]
    hit = [t for t in secs if t.get('index') == idx
           and any(norm(v) == norm(t['title']) for v in vs)]
    if miss or hit:
        print('章%d: 命中%d 丢失%d' % (idx, len(hit), len(miss)))
    for t in miss:
        print('  丢失 sec=%s:' % t.get('sec'), repr(t['title'][:30]))
    for t in hit:
        print('  命中:', repr(t['title'][:30]))

print('--- 章1 搜索节标题片段 ---')
d = json.load(open(d0 + '/1.json', encoding='utf-8'))
vs = [norm(b.get('value', '')) for b in d['content'] if b.get('type') == 'text']
for kw in ['人文主义', '精神科学', '释义学', '诠释']:
    hit = [(i, v[:30]) for i, v in enumerate(vs) if kw in v[:50]]
    print(kw, '→', hit[:4])
