# -*- coding: utf-8 -*-
"""验证: 拆分后块结构 + 前端读取抽查"""
import json, os, hashlib
import urllib.request

B = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy'
CD = B + '/backend/data/book_chapters'
ck = json.load(open(B + '/backend/data/dp_pdf_import_ckpt.json', encoding='utf-8'))

rels = [rel for rel, v in ck['books'].items() if v.get('src') == 'ocr']
print('=== 拆分后块结构 ===')
for rel in rels:
    bid = hashlib.md5(rel.encode()).hexdigest()[:12]
    m = json.load(open(os.path.join(CD, bid, 'meta.json'), encoding='utf-8'))
    n = m['chapterCount']
    maxblock = 0
    over2400 = 0
    total = 0
    for i in range(n):
        ch = json.load(open(os.path.join(CD, bid, '%d.json' % i), encoding='utf-8'))
        for b in ch.get('content', []):
            if b.get('type') == 'text':
                l = len(b.get('value', ''))
                maxblock = max(maxblock, l)
                if l > 2400:
                    over2400 += 1
                total += l
    print('%-48s 总=%d 最大块=%d 超2400=%d' % (rel[:44], total, maxblock, over2400))

print()
print('=== 前端读取抽查 ===')
def get(p):
    with urllib.request.urlopen('http://localhost:5173' + p, timeout=10) as r:
        return r.read()

for rel, chk in [('西方/托马斯·霍布斯/托马斯•霍布斯.pdf', 6), ('西方/杰里米·边沁/道德与立法原理导论.pdf', 5),
                 ('西方/伊曼努尔·康德/康德《实践理性批判》句读.pdf', 1)]:
    bid = hashlib.md5(rel.encode()).hexdigest()[:12]
    d = get('/backend/data/book_chapters/%s/%d.json' % (bid, chk))
    print('%-40s %d.json %dB %s' % (rel[:36], chk, len(d), 'JSON' if d[:1] == b'{' else 'HTML!'))
