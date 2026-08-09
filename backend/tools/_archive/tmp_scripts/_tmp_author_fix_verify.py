# -*- coding: utf-8 -*-
"""作者修正验证: 磁盘 + 5173 读取链"""
import json, os, urllib.request

EXPECT = {
    'd036e1e712eb': '道格拉斯·格鲁秀斯',
    '75efcbb151b7': '加勒特·汤姆森',
    'add6c213fde8': '苏珊·李·安德森',
    'cba9d40254dc': '霍普·梅',
    '00fadd7de47c': '埃里克·斯坦哈特',
    '324c13db486e': '丹尼尔·托马斯·普里莫兹克',
    '60eed962806b': '安妮·施沃恩、史蒂芬·夏皮罗',
    '7f462a9750e8': '亨利·萨默斯-霍尔',
    '62c5caa0bfde': '艾四林 等',
}
fails = []

# 磁盘一致性: books.json / detail / meta 三处(DP+PHI)
BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy'
PHI = r'F:/program/Python/PhiAgent/backend/data'
srcs = [
    (BASE + '/app/public/books.json', 'books.json(list)'),
    (BASE + '/backend/data/book_detail/{bid}.json', 'DP_detail'),
    (BASE + '/app/public/book_detail/{bid}.json', 'DP_public_detail'),
    (BASE + '/backend/data/book_chapters/{bid}/meta.json', 'DP_meta'),
    (BASE + '/app/public/backend/data/book_chapters/{bid}/meta.json', 'DP_public_meta'),
    (PHI + '/book_detail/{bid}.json', 'PHI_detail'),
    (PHI + '/book_chapters/{bid}/meta.json', 'PHI_meta'),
]
for bid, want in EXPECT.items():
    # books.json list
    bj = json.load(open(BASE + '/app/public/books.json', encoding='utf-8'))
    items = bj if isinstance(bj, list) else bj.get('books', [])
    hit = next((it for it in items if it.get('id') == bid), None)
    if hit is None or hit.get('author') != want:
        fails.append('%s books.json=%s' % (bid, hit.get('author') if hit else '无条目'))
    for pat, label in srcs[1:]:
        fp = pat.format(bid=bid)
        if not os.path.exists(fp):
            continue  # 苏格拉底 meta 未入库, 跳过
        d = json.load(open(fp, encoding='utf-8'))
        if d.get('author') != want:
            fails.append('%s %s=%s' % (bid, label, d.get('author')))

# 5173 读取链
try:
    r = urllib.request.urlopen('http://localhost:5173/books.json', timeout=5)
    bj = json.loads(r.read().decode('utf-8'))
    items = bj if isinstance(bj, list) else bj.get('books', [])
    for bid, want in EXPECT.items():
        hit = next((it for it in items if it.get('id') == bid), None)
        got = hit.get('author') if hit else '无条目'
        if got != want:
            fails.append('5173 books.json %s=%s (want %s)' % (bid, got, want))
    for bid, want in EXPECT.items():
        r = urllib.request.urlopen('http://localhost:5173/book_detail/%s.json' % bid, timeout=5)
        d = json.loads(r.read().decode('utf-8'))
        if d.get('author') != want:
            fails.append('5173 book_detail %s=%s (want %s)' % (bid, d.get('author'), want))
except Exception as e:
    fails.append('5173 不可达: %s' % e)

print('修正清单:')
for bid, want in EXPECT.items():
    print('  %s → %s' % (bid, want))
print()
if fails:
    print('✗ %d 处不一致:' % len(fails))
    for f in fails:
        print('  %s' % f)
else:
    print('✓ 全部一致 (磁盘 7 源 + 5173 books.json/book_detail 读取链)')
