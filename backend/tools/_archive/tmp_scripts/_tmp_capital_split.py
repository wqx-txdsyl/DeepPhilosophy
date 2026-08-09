# -*- coding: utf-8 -*-
"""读《资本论》(b3219ec260ed): 拆分超长块(>6000字符)为自然段落
块为单行连续文本(nl_fix 合并), 按中文句读(。！？；…)切分, 目标段 800-2400 字符
"""
import json, os, shutil, re

B = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy'
D = os.path.join(B, 'backend/data/book_chapters/b3219ec260ed')
PUB = os.path.join(B, 'app/public/backend/data/book_chapters/b3219ec260ed')

# 句读后可能跟右引号/括号, 切点放在其后
CUT_PAT = re.compile(r'[。！？；…]["”』」）】\']*')

def split_block(text, minlen=800, maxlen=2400):
    cuts = [m.end() for m in CUT_PAT.finditer(text) if m.end() < len(text)]
    paras, start = [], 0
    while True:
        nxt = [c for c in cuts if start + minlen <= c <= start + maxlen or (c >= start + maxlen)]
        if not nxt:
            break
        p = nxt[0]
        paras.append(text[start:p])
        start = p
        if len(text) - start <= maxlen * 1.2:
            break
    if start < len(text):
        paras.append(text[start:])
    return paras

targets = {
    '2.json': [0, 10], '6.json': [0], '7.json': [0], '8.json': [3],
    '9.json': [1], '11.json': [2], '12.json': [2], '16.json': [4],
    '17.json': [1], '18.json': [1],
}

for fn, idxs in targets.items():
    p = os.path.join(D, fn)
    ch = json.load(open(p, encoding='utf-8'))
    content = ch.get('content', [])
    for i in sorted(idxs, reverse=True):
        b = content[i]
        v = b.get('value', '')
        if b.get('type') != 'text' or len(v) <= 6000:
            print(fn, i, '跳过'); continue
        paras = split_block(v)
        content[i:i+1] = [{'type': 'text', 'value': x} for x in paras]
        print('%s 块%d: %d字符 → %d段 [%d-%d]' % (fn, i, len(v), len(paras), min(map(len, paras)), max(map(len, paras))))
    ch['content'] = content
    json.dump(ch, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
    shutil.copy2(p, os.path.join(PUB, fn))

print('\n=== 拆分后超长块(>6000) ===')
n_over = 0
for fn in sorted([f for f in os.listdir(D) if f.endswith('.json') and f != 'meta.json'], key=lambda x: int(x.split('.')[0])):
    ch = json.load(open(os.path.join(D, fn), encoding='utf-8'))
    for b in ch.get('content', []):
        if len(b.get('value', '')) > 6000:
            n_over += 1
            print(fn, len(b.get('value', '')), '字符')
print('剩余超长块:', n_over)
