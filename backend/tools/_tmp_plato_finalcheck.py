# -*- coding: utf-8 -*-
"""柏拉图最终校验: 双端一致/章节完整/页序/元数据同步"""
import json, os, hashlib, urllib.request

B = r'F:\program\Python\DeepPhilosophy\DeepPhilosophy'
CD = B + r'\backend\data\book_chapters\35279e2e439d'
PD = B + r'\app\public\backend\data\book_chapters\35279e2e439d'

# 1. 双端文件一致
mismatch = 0
for f in os.listdir(CD):
    p = os.path.join(PD, f)
    if not os.path.exists(p):
        print('public 缺:', f); mismatch += 1
    elif open(os.path.join(CD, f), 'rb').read() != open(p, 'rb').read():
        print('不一致:', f); mismatch += 1
for f in os.listdir(PD):
    if not os.path.exists(os.path.join(CD, f)):
        print('backend 缺:', f); mismatch += 1
print('双端文件:', '一致' if mismatch == 0 else '有%d处不一致' % mismatch)

# 2. 全书完整
m = json.load(open(os.path.join(CD, 'meta.json'), encoding='utf-8'))
n = m['chapterCount']
total = 0
empty = 0
maxblock = 0
for i in range(n):
    ch = json.load(open(os.path.join(CD, '%d.json' % i), encoding='utf-8'))
    if not ch['content']:
        empty += 1
    for b in ch['content']:
        total += len(b.get('value', ''))
        maxblock = max(maxblock, len(b.get('value', '')))
print('章数: %d, 空章: %d, 全书字符: %d, 最大块: %d' % (n, empty, total, maxblock))

# 3. 章16 页序抽查(前4块)
ch16 = json.load(open(os.path.join(CD, '16.json'), encoding='utf-8'))
print()
print('章16 前4块:')
for b in ch16['content'][:4]:
    print('  ', b['value'][:60].replace('\n', '⏎'))

# 4. 元数据同步
d = json.load(open(B + r'\backend\data\book_detail\35279e2e439d.json', encoding='utf-8'))
cat = json.load(open(B + r'\backend\data\books_catalog.json', encoding='utf-8'))
plato_cat = [x for x in cat['books'] if x['id'] == '35279e2e439d'][0]
print()
print('meta.chapterCount:', m['chapterCount'], '| detail.chapterCount:', d['chapterCount'],
      '| catalog.chapterCount:', plato_cat['chapterCount'])
print('meta.chapterTitles == detail.chapterTitles:', m['chapterTitles'] == d['chapterTitles'])
print('meta.toc 项数:', len(m['toc']), '| detail.toc 项数:', len(d['toc']))
print('toc[0]:', json.dumps(m['toc'][0], ensure_ascii=False))

# 5. 前端运行时验证
print()
for p in ('/backend/data/book_chapters/35279e2e439d/meta.json',
          '/backend/data/book_chapters/35279e2e439d/15.json'):
    try:
        r = urllib.request.urlopen('http://localhost:5173' + p, timeout=10)
        body = r.read()
        print('%s → %dB %s' % (p.split('/')[-1], len(body), 'JSON' if body[:1] == b'{' else 'HTML!'))
    except Exception as e:
        print('%s → 请求失败: %s' % (p.split('/')[-1], e))
