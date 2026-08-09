# -*- coding: utf-8 -*-
"""柏拉图对话集重建深度检查"""
import json, os

B = r'F:\program\Python\DeepPhilosophy\DeepPhilosophy\backend'
CD = os.path.join(B, 'data', 'book_chapters', '35279e2e439d')

m = json.load(open(os.path.join(CD, 'meta.json'), encoding='utf-8'))
print('=== meta 全字段 ===')
for k, v in m.items():
    if k == 'toc':
        print('toc:', json.dumps(v, ensure_ascii=False)[:2000])
    elif isinstance(v, str):
        print('%s: %s' % (k, v[:200]))
    else:
        print('%s: %s' % (k, v))

print()
print('=== 各章概况 ===')
for i in range(m['chapterCount']):
    p = os.path.join(CD, '%d.json' % i)
    if not os.path.exists(p):
        print('%d.json 缺失!' % i)
        continue
    ch = json.load(open(p, encoding='utf-8'))
    blocks = ch.get('content', [])
    texts = sum(1 for b in blocks if b.get('type') == 'text')
    total = sum(len(b.get('value', '')) for b in blocks if b.get('type') == 'text')
    print('%d.json title=%r 块=%d 文本块=%d 字符=%d' % (i, ch.get('title', '')[:40], len(blocks), texts, total))

print()
print('=== 第一章首块 ===')
ch0 = json.load(open(os.path.join(CD, '0.json'), encoding='utf-8'))
for b in ch0.get('content', [])[:8]:
    print('  [%s] %s' % (b.get('type'), b.get('value', '')[:100]))
