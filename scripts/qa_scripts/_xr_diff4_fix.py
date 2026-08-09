# -*- coding: utf-8 -*-
"""4 本 detail/meta 失同步修复：维特根斯坦/尼采/现象学/认识世界
以 meta 为权威：detail.toc = meta.toc 拷贝；现象学另修 meta.chapterCount 37→33
"""
import json, os

DP = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy'
PA = 'f:/program/Python/PhiAgent'
BOOKS = [
    ('c0e78ea6f80a', '维特根斯坦', 24),
    ('4cc9d23c7dbf', '尼采', 59),
    ('ef76ae88994f', '现象学', 33),
    ('c97cb4e6161a', '认识世界', 112),
]

for bid, name, cc in BOOKS:
    mp = os.path.join(DP, 'backend/data/book_chapters/%s/meta.json' % bid)
    m = json.load(open(mp, encoding='utf-8'))
    # 现象学：meta.chapterCount 37→33
    if m.get('chapterCount') != cc:
        print('%s: meta.chapterCount %r -> %d' % (name, m.get('chapterCount'), cc))
        m['chapterCount'] = cc
    # meta chapterTitles 长度核对
    if len(m.get('chapterTitles', [])) != cc:
        print('%s: meta.chapterTitles %d -> 重建' % (name, len(m.get('chapterTitles', []))))
        m['chapterTitles'] = [t['title'] for t in m['toc'] if t['type'] == 'chapter']
    # 写 4 处 meta
    for p in [
        os.path.join(DP, 'backend/data/book_chapters/%s/meta.json' % bid),
        os.path.join(DP, 'app/public/backend/data/book_chapters/%s/meta.json' % bid),
        os.path.join(PA, 'backend/data/book_chapters/%s/meta.json' % bid),
        os.path.join(PA, 'app/public/backend/data/book_chapters/%s/meta.json' % bid),
    ]:
        json.dump(m, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    # detail（DP+PA）toc 重同步
    for root, tag in [(DP, 'DP'), (PA, 'PA')]:
        dp = os.path.join(root, 'app/public/book_detail/%s.json' % bid)
        d = json.load(open(dp, encoding='utf-8'))
        before = len(d.get('toc', []))
        d['toc'] = [dict(t) for t in m['toc']]
        d['chapterTitles'] = list(m.get('chapterTitles', []))
        d['chapterCount'] = cc
        json.dump(d, open(dp, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
        print('%s: detail(%s) toc %d -> %d' % (name, tag, before, len(d['toc'])))
print()
print('完成。')
