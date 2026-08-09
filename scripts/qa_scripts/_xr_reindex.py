# -*- coding: utf-8 -*-
"""删章后 index 重排压缩连续：现象学 + 黑格尔
算法：读全部内容 → 删所有将改名的旧文件 → 写新名 → 更新 toc index"""
import json, os, re

DP = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters'

def reindex(bid):
    base = os.path.join(DP, bid)
    files = sorted(int(f[:-5]) for f in os.listdir(base) if re.fullmatch(r'\d+\.json', f))
    n = len(files)
    # 已是连续 0..n-1？
    if files == list(range(n)):
        print('%s: 已连续 0..%d，无需重排' % (bid, n - 1))
        return
    # 构造映射 old -> new
    mapping = {}
    for new, old in enumerate(files):
        if old != new:
            mapping[old] = new
    print('%s: %d 个文件, %d 个需改名' % (bid, n, len(mapping)))
    # 读全部内容
    contents = {}
    for old in files:
        contents[old] = json.load(open(os.path.join(base, '%d.json' % old), encoding='utf-8'))
    # 删旧文件
    for old in mapping:
        os.remove(os.path.join(base, '%d.json' % old))
    # 写新名
    for old, new in mapping.items():
        json.dump(contents[old], open(os.path.join(base, '%d.json' % new), 'w', encoding='utf-8'), ensure_ascii=False)
    # 更新 toc index
    mp = os.path.join(base, 'meta.json')
    m = json.load(open(mp, encoding='utf-8'))
    for t in m.get('toc', []):
        old = t.get('index')
        if old in mapping:
            t['index'] = mapping[old]
    json.dump(m, open(mp, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    # 校验
    now = sorted(int(f[:-5]) for f in os.listdir(base) if re.fullmatch(r'\d+\.json', f))
    tidx = sorted(t.get('index') for t in m['toc'])
    ok = now == list(range(len(now))) and tidx == now
    print('%s: 重排后文件=%d, toc=%d, 连续=%s' % (bid, len(now), len(tidx), ok))

reindex('ef76ae88994f')
reindex('bbac1be0bb4b')
