# -*- coding: utf-8 -*-
"""维特根斯坦文集 (c0e78ea6f80a) 重修: 24 章按卷分组 toc + 正确标题 + 卷内顺序重排
鉴定结论: 0/1=卷1战时笔记, 2=卷3哲学语法, 3-7=卷5数学基础, 8/9/10/14/16/21=卷6心理学最后著作,
         12/13/15/19=卷7论颜色, 11/17/18/20/22/23=卷8论确定性; 卷2逻辑哲学论与卷4哲学研究套装源缺失(单本已收录)
"""
import json, os, shutil

B = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy'
D = os.path.join(B, 'backend/data/book_chapters/c0e78ea6f80a')
PUB = os.path.join(B, 'app/public/backend/data/book_chapters/c0e78ea6f80a')
DETAIL = os.path.join(B, 'backend/data/book_detail/c0e78ea6f80a.json')
PUB_DETAIL = os.path.join(B, 'app/public/book_detail/c0e78ea6f80a.json')

# (type, 标题, index=章节文件号)
TOC = [
    ('chapter', '第1卷 战时笔记（1914-1916）', 0),
    ('section', '逻辑笔记（MS 101）', 0),
    ('section', '战时日记（MS 101）', 1),
    ('chapter', '第3卷 哲学语法', 2),
    ('chapter', '第5卷 数学基础研究', 3),
    ('section', '数学与游戏', 3),
    ('section', '论基数', 4),
    ('section', '数学证明', 5),
    ('section', '归纳证明·循环性', 6),
    ('section', '数学中的无穷·外延的看法', 7),
    ('chapter', '第6卷 关于心理学哲学的最后著作', 8),
    ('section', '手稿169（约1949）', 8),
    ('section', '手稿170（约1949）', 9),
    ('section', '手稿171（约1949-1950）', 10),
    ('section', '第2卷第4章前半', 14),
    ('section', '第2卷第5章', 16),
    ('section', '第2卷第6章', 21),
    ('chapter', '第7卷 论颜色', 19),
    ('section', '第1部分', 19),
    ('section', '第2部分', 12),
    ('section', '第3部分（1-130）', 13),
    ('section', '第3部分（131-350）与第2卷第4章后半', 15),
    ('chapter', '第8卷 论确定性', 11),
    ('section', '1-65节', 11),
    ('section', '66-192节', 17),
    ('section', '193-425节', 18),
    ('section', '426-523节', 20),
    ('section', '524-637节', 22),
    ('section', '638-676节', 23),
]

# 文件号 → 章标题（chapterTitles 用, 与 toc 的 chapter/section 标题一致）
FILE_TITLES = {
    0: '第1卷 战时笔记·逻辑笔记（MS 101）', 1: '第1卷 战时笔记·战时日记（MS 101）',
    2: '第3卷 哲学语法',
    3: '第5卷 数学基础研究·数学与游戏', 4: '第5卷 数学基础研究·论基数',
    5: '第5卷 数学基础研究·数学证明', 6: '第5卷 数学基础研究·归纳证明',
    7: '第5卷 数学基础研究·数学中的无穷',
    8: '第6卷 心理学最后著作·手稿169', 9: '第6卷 心理学最后著作·手稿170',
    10: '第6卷 心理学最后著作·手稿171', 14: '第6卷 心理学最后著作·第2卷第4章前半',
    16: '第6卷 心理学最后著作·第2卷第5章', 21: '第6卷 心理学最后著作·第2卷第6章',
    19: '第7卷 论颜色·第1部分', 12: '第7卷 论颜色·第2部分',
    13: '第7卷 论颜色·第3部分（1-130）', 15: '第7卷 论颜色·第3部分（131-350）',
    11: '第8卷 论确定性·1-65节', 17: '第8卷 论确定性·66-192节',
    18: '第8卷 论确定性·193-425节', 20: '第8卷 论确定性·426-523节',
    22: '第8卷 论确定性·524-637节', 23: '第8卷 论确定性·638-676节',
}

# 1. meta.json: toc + chapterTitles
mp = os.path.join(D, 'meta.json')
m = json.load(open(mp, encoding='utf-8'))
m['toc'] = [{'type': t, 'title': title, 'index': idx} for t, title, idx in TOC]
m['chapterTitles'] = [FILE_TITLES[i] for i in range(24)]
json.dump(m, open(mp, 'w', encoding='utf-8'), ensure_ascii=False)
shutil.copy2(mp, os.path.join(PUB, 'meta.json'))
print('meta.json: toc', len(m['toc']), '项(含 chapter', sum(1 for t in TOC if t[0] == 'chapter'), '+ section', sum(1 for t in TOC if t[0] == 'section'), ')')

# 2. 各章文件 title
for fn in os.listdir(D):
    if not (fn.endswith('.json') and fn != 'meta.json'):
        continue
    i = int(fn.split('.')[0])
    p = os.path.join(D, fn)
    ch = json.load(open(p, encoding='utf-8'))
    ch['title'] = FILE_TITLES[i]
    json.dump(ch, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
    shutil.copy2(p, os.path.join(PUB, fn))
print('24 章 title 已更新 + public 双写')

# 3. book_detail（backend + public）
SUMMARY = ('《维特根斯坦文集》商务印书馆版套装（全8卷），本书 epub 源含第1卷《战时笔记》、第3卷《哲学语法》、'
           '第5卷《数学基础研究》、第6卷《关于心理学哲学的最后著作》、第7卷《论颜色》、第8卷《论确定性》正文，'
           '共24个章节文件按卷分级组织。套装源缺《逻辑哲学论》（第2卷）与《哲学研究》（第4卷）正文，'
           '两卷单本已分别单独收录于书库，可直接搜索阅读。')
for p in [DETAIL, PUB_DETAIL]:
    d = json.load(open(p, encoding='utf-8'))
    d['toc'] = m['toc']
    d['chapterTitles'] = m['chapterTitles']
    d['summary'] = SUMMARY
    json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
    print('detail 同步:', os.path.basename(p))

# 4. books.json summary（两份）
for bp in [os.path.join(B, 'app/public/books.json'), os.path.join(B, 'app/src/assets/books.json')]:
    books = json.load(open(bp, encoding='utf-8'))
    for b in books:
        if b.get('id') == 'c0e78ea6f80a':
            b['summary'] = SUMMARY
    json.dump(books, open(bp, 'w', encoding='utf-8'), ensure_ascii=False)
print('books.json summary 同步')
print('完成')
