# -*- coding: utf-8 -*-
"""作者修正 apply: 9 本书 × 全部数据源 (books.json/detail/meta × DP/PHI/dist)
每处打印前后对比, 幂等"""
import json, os, shutil

BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy'
PHI = r'F:/program/Python/PhiAgent/backend/data'

# rel → 新作者 (书名页 OCR/文本层确认)
AUTHOR_FIX = {
    '西方/布莱兹·帕斯卡尔/最伟大的思想家 - 帕斯卡尔.pdf': '道格拉斯·格鲁秀斯',
    '西方/戈特弗里德·威廉·莱布尼茨/最伟大的思想家 - 莱布尼茨.pdf': '加勒特·汤姆森',
    '西方/索伦·克尔凯郭尔/最伟大的思想家 - 克尔恺廓尔.pdf': '苏珊·李·安德森',
    '西方/苏格拉底/最伟大的思想家 - 苏格拉底.pdf': '霍普·梅',
    '西方/弗里德里希·尼采/最伟大的思想家 - 尼采.pdf': '埃里克·斯坦哈特',
    '西方/莫里斯·梅洛-庞蒂/最伟大的思想家 - 梅洛-庞蒂.pdf': '丹尼尔·托马斯·普里莫兹克',
    '西方/米歇尔·福柯/导读福柯《规训与惩罚》.pdf': '安妮·施沃恩、史蒂芬·夏皮罗',
    '西方/吉尔·德勒兹/导读德勒兹《差异与重复》.pdf': '亨利·萨默斯-霍尔',
    '西方/弗里德里希·恩格斯/《反杜林论》导读.epub': '艾四林 等',
}
import hashlib
BIDS = {hashlib.md5(rel.encode()).hexdigest()[:12]: (rel, auth) for rel, auth in AUTHOR_FIX.items()}

def set_author(fp, new):
    """改文件 author 字段, 返回 (旧, 新) 或 None(文件不存在/无 author)"""
    if not os.path.exists(fp):
        return None
    d = json.load(open(fp, encoding='utf-8'))
    if isinstance(d, list):
        out = []
        for it in d:
            if it.get('id') in BIDS and it.get('author') != new:
                it['author'] = new
            out.append(it)
        return out
    if 'author' not in d or d['author'] == new:
        return None
    old = d['author']
    d['author'] = new
    json.dump(d, open(fp, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    return (old, new)

print('== books.json ==')
bj = json.load(open(BASE + '/app/public/books.json', encoding='utf-8'))
bj = bj if isinstance(bj, list) else bj.get('books', [])
changed = 0
for it in bj:
    if it.get('id') in BIDS and it.get('author') != BIDS[it['id']][1]:
        print('  %s: %s → %s' % (it['title'], it['author'], BIDS[it['id']][1]))
        it['author'] = BIDS[it['id']][1]
        changed += 1
json.dump(bj, open(BASE + '/app/public/books.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('  books.json 修改 %d 本' % changed)

# 各 detail/meta 位置
spots = []
for pre in [BASE + '/backend/data', BASE + '/app/public', PHI]:
    spots.append((pre + '/book_detail/{bid}.json', 'detail'))
    spots.append((pre + '/book_chapters/{bid}/meta.json', 'meta'))
# dist (若有)
for pre in [BASE + '/app/dist', BASE + '/app/dist_app']:
    if os.path.exists(pre + '/books.json'):
        spots.append((pre + '/book_detail/{bid}.json', 'dist_detail'))
        spots.append((pre + '/book_chapters/{bid}/meta.json', 'dist_meta'))
        print('  dist 存在: %s' % pre)
if os.path.exists(BASE + '/app/dist/books.json'):
    bjd = json.load(open(BASE + '/app/dist/books.json', encoding='utf-8'))
    bjd = bjd if isinstance(bjd, list) else bjd.get('books', [])
    ch = 0
    for it in bjd:
        if it.get('id') in BIDS and it.get('author') != BIDS[it['id']][1]:
            print('  [dist] %s: %s → %s' % (it['title'], it['author'], BIDS[it['id']][1]))
            it['author'] = BIDS[it['id']][1]
            ch += 1
    json.dump(bjd, open(BASE + '/app/dist/books.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print('  [dist] books.json 修改 %d 本' % ch)

print()
print('== detail/meta 逐处 ==')
for pat, label in spots:
    for bid, (rel, new) in BIDS.items():
        fp = pat.format(bid=bid)
        r = set_author(fp, new)
        if r is None:
            continue
        print('  %-12s %-12s %s → %s' % (label, rel.split('/')[1][:10], r[0], r[1]))

print()
print('DONE')
