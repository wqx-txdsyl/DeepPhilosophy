# -*- coding: utf-8 -*-
"""维特根斯坦文集 (c0e78ea6f80a) 最终收尾: 8 卷层级 toc + 卷标题清洗 + public 双写 + detail/books.json 同步
130 章 = 8 卷标题章 + 目录/总序/编译前言等 + 正文章; 纯标题分组章(内容==标题)不进 toc"""
import json, os, shutil, re

B = 'f:/program/Python/DeepPhilosophy/DeepPhilosophy'
D = os.path.join(B, 'backend/data/book_chapters/c0e78ea6f80a')
PUB = os.path.join(B, 'app/public/backend/data/book_chapters/c0e78ea6f80a')
DETAIL = os.path.join(B, 'backend/data/book_detail/c0e78ea6f80a.json')
PUB_DETAIL = os.path.join(B, 'app/public/book_detail/c0e78ea6f80a.json')

mp = os.path.join(D, 'meta.json')
m = json.load(open(mp, encoding='utf-8'))
n = m['chapterCount']

# 1. 逐章读取, 判定纯标题分组章 + 卷标题章
VOL_PAT = re.compile(r'^维特根斯坦文集.*第[一二三四五六七八九十百\d]+卷')
title_chapters = []   # 卷标题章 index（chapter 条目）
pure_group = []       # 纯标题分组章 index（剔除出 toc, 保留文件）
chapter_titles = []
for i in range(n):
    ch = json.load(open(os.path.join(D, '%d.json' % i), encoding='utf-8'))
    t = ch.get('title', '')
    # 清洗仅限卷标题章: epub 文件名残留噪声（第4卷哲学研究16463-4 / 第5卷数学基础研究16464-1）
    if VOL_PAT.match(t):
        t2 = re.sub(r'[-\d]+$', '', t)
        if t2 != t:
            ch['title'] = t2
            json.dump(ch, open(os.path.join(D, '%d.json' % i), 'w', encoding='utf-8'), ensure_ascii=False)
            t = t2
    if VOL_PAT.match(t):
        title_chapters.append(i)
    else:
        body = ''.join(b.get('value', '') for b in ch.get('content', []) if b.get('type') == 'text').strip()
        if body == t.strip():
            pure_group.append(i)
    chapter_titles.append(t)

print('卷标题章:', title_chapters)
print('纯标题分组章(剔除出toc):', pure_group)

# 2. 卷边界 → 构建层级 toc
bounds = title_chapters + [n]
toc = []
for vi, vol_idx in enumerate(title_chapters):
    toc.append({'type': 'chapter', 'title': chapter_titles[vol_idx], 'index': vol_idx})
    for i in range(vol_idx + 1, bounds[vi + 1]):
        if i in pure_group:
            continue
        toc.append({'type': 'section', 'title': chapter_titles[i], 'index': i})

print('toc: chapter %d + section %d = %d' % (
    sum(1 for t in toc if t['type'] == 'chapter'),
    sum(1 for t in toc if t['type'] == 'section'), len(toc)))

# 3. 写 meta.json
m['toc'] = toc
m['chapterTitles'] = chapter_titles
json.dump(m, open(mp, 'w', encoding='utf-8'), ensure_ascii=False)
print('meta.json: toc %d 项, chapterTitles %d 项' % (len(toc), len(chapter_titles)))

# 4. public 双写（全部章节 + meta）
os.makedirs(PUB, exist_ok=True)
for fn in os.listdir(D):
    if fn.endswith('.json'):
        shutil.copy2(os.path.join(D, fn), os.path.join(PUB, fn))
print('public 章节双写:', len(os.listdir(PUB)), '个文件')

# 5. detail（backend + public）
SUMMARY = ('《维特根斯坦文集》商务印书馆版套装，全书 8 卷完整收录：第1卷《战时笔记（1914—1917）》'
           '（含哲学部分与私人部分手稿）、第2卷《逻辑哲学论》（1—7 全部命题）、'
           '第3卷《哲学语法》、第4卷《哲学研究》（正文与附录）、第5卷《数学基础研究》、'
           '第6卷《关于心理学哲学的研究》、第7卷《心理学哲学笔记》（手稿169—171）、'
           '第8卷《最后的哲学笔记（1950—1951）》（手稿172—177，含《论确定性》《论颜色》'
           '与《关于心理学哲学的最后著作》第2卷内容），共130章按卷分级组织。')
for p in [DETAIL, PUB_DETAIL]:
    d = json.load(open(p, encoding='utf-8'))
    d['toc'] = toc
    d['chapterTitles'] = chapter_titles
    d['chapterCount'] = n
    d['summary'] = SUMMARY
    json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
    print('detail 同步:', os.path.basename(p))

# 6. books.json（两份）
for bp in [os.path.join(B, 'app/public/books.json'), os.path.join(B, 'app/src/assets/books.json')]:
    books = json.load(open(bp, encoding='utf-8'))
    hit = False
    for b in books:
        if b.get('id') == 'c0e78ea6f80a':
            b['summary'] = SUMMARY
            b['chapterCount'] = n
            hit = True
            break
    json.dump(books, open(bp, 'w', encoding='utf-8'), ensure_ascii=False)
    print('books.json 同步:', os.path.basename(bp), '| 命中:', hit)
print('完成')
