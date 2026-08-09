# -*- coding: utf-8 -*-
"""修复 public 侧失同步:
1. public/book_detail/35279e2e439d.json ← backend 17章版
2. public/books.json chapterCount 从 meta 校准(全量)
3. backend/data/book_detail vs public/book_detail 全量对比, 输出失同步清单
"""
import json, os

B = r'F:\program\Python\DeepPhilosophy\DeepPhilosophy'
BD = B + r'\backend\data\book_detail'
PD = B + r'\app\public\book_detail'
CD = B + r'\backend\data\book_chapters'
BJ = B + r'\app\public\books.json'

# 1. 柏拉图 detail 同步
import shutil
src = os.path.join(BD, '35279e2e439d.json')
dst = os.path.join(PD, '35279e2e439d.json')
shutil.copy2(src, dst)
d = json.load(open(dst, encoding='utf-8'))
print('1. public/book_detail 柏拉图: chapterCount=%d toc=%d 项 ✓' % (d['chapterCount'], len(d['toc'])))

# 2. books.json 校准
books = json.load(open(BJ, encoding='utf-8'))
fixed = 0
for it in books:
    bid = it.get('id', '')
    mp = os.path.join(CD, bid, 'meta.json')
    if not os.path.exists(mp):
        continue
    m = json.load(open(mp, encoding='utf-8'))
    real = m.get('chapterCount', 0)
    if it.get('chapterCount') != real:
        print('  books.json %-16s %-36s %s -> %d' % (bid, it['title'][:34], it.get('chapterCount', 0), real))
        it['chapterCount'] = real
        fixed += 1
json.dump(books, open(BJ, 'w', encoding='utf-8'), ensure_ascii=False)
print('2. books.json 校准: %d 本修正' % fixed)

# 3. detail 双端全量对比
mism = []
for f in sorted(os.listdir(BD)):
    if not f.endswith('.json'):
        continue
    p = os.path.join(PD, f)
    if not os.path.exists(p):
        mism.append((f, 'public缺'))
    elif open(os.path.join(BD, f), 'rb').read() != open(p, 'rb').read():
        mism.append((f, '内容不一致'))
for f in sorted(os.listdir(PD)):
    if f.endswith('.json') and not os.path.exists(os.path.join(BD, f)):
        mism.append((f, 'backend缺'))
print()
print('3. detail 双端对比: %d 处不一致' % len(mism))
for f, why in mism[:40]:
    print('   %-20s %s' % (f, why))
if len(mism) > 40:
    print('   ...共 %d 处' % len(mism))
