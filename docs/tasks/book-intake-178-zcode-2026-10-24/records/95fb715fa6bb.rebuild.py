# -*- coding: utf-8 -*-
"""重建《文集》（拉康选集，褚孝泉译）(95fb715fa6bb) 章节结构。

22章 = 18篇文章 + 译名对照表 + 拉康著作表 + 拉康生平年表 + 译后记。
正文为整段一行式：每个非空行=一个段落块；剔除封面/目录(0-393)、
页码页眉行（\d+ 拉康选集 / 拉康选集）、各篇标题的页眉重复行。
"""
import json
import os
import re

RAW = '/Users/sen/Downloads/raw/incoming-codex/raw-text-handoff-20261023/95fb715fa6bb/candidate-01/raw.txt'
OUT_DIR = 'backend/data/book_chapters/95fb715fa6bb'

CHAPTERS = [
    (154,   '总序'),
    (180,   '编者前言'),
    (394,   '关于《被窃的信》的研讨会'),
    (1416,  '关于我的经历'),
    (1588,  '超越“现实原则”'),
    (1822,  '助成“我”的功能形成的镜子阶段'),
    (1936,  '精神分析中的侵凌性'),
    (2352,  '精神分析学在犯罪学中的功能的理论导论'),
    (2798,  '谈心理因果'),
    (3622,  '逻辑时间及预期确定性的肯定'),
    (3916,  '就转移作的发言'),
    (4110,  '终于谈到了主体'),
    (4322,  '精神分析学中的言语和语言的作用和领域'),
    (5956,  '典型疗法的变体'),
    (6674,  '弗洛伊德事务或在精神分析学中回归弗洛伊德的意义'),
    (7232,  '无意识中文字的动因或自弗洛伊德以来的理性'),
    (8010,  '论精神错乱的一切可能疗法的一个先决问题'),
    (9018,  '治疗的方向和它的力量的原则'),
    (10270, '男根的意义'),
    (10478, '主体的倾覆和在弗洛伊德无意识中的欲望的辩证法'),
    (11240, '译名对照表'),
    (11326, '拉康著作表'),
    (11340, '拉康生平年表'),
    (11412, '译后记'),
]


def squash(s):
    return re.sub(r'[\s　]+', '', s)


def main():
    lines = open(RAW, encoding='utf-8').read().split('\n')
    n = len(lines)
    bounds = [c[0] for c in CHAPTERS] + [n]
    chapters = []
    for ci, (lo, title) in enumerate(CHAPTERS):
        end = bounds[ci + 1]
        blocks = []
        for i in range(lo, end):
            s = lines[i].strip()
            if not s:
                continue
            sq = squash(s)
            if re.fullmatch(r'\d{1,3}', sq):
                continue
            if sq == '拉康选集' or re.fullmatch(r'\d{1,3}拉康选集', sq):
                continue  # 页码+页眉
            if re.fullmatch(r'编者前言\d{0,3}', sq) and not (i == lo and title == '编者前言'):
                continue  # 页眉（可带页码）
            if sq == squash(title):
                if i == lo:
                    blocks.append({'type': 'text', 'value': title})
                continue  # 页眉重复
            blocks.append({'type': 'text', 'value': re.sub(r'\s{2,}', ' ', s)})
        chapters.append((title, blocks))

    os.makedirs(OUT_DIR, exist_ok=True)
    meta_toc = []
    chapter_titles = []
    for i, (title, blocks) in enumerate(chapters):
        ch = dict(index=i, title=title, paragraphMode='source', content=blocks)
        with open(f'{OUT_DIR}/{i}.json', 'w', encoding='utf-8') as f:
            json.dump(ch, f, ensure_ascii=False, indent=1)
        chapter_titles.append(title)
        meta_toc.append(dict(type='chapter', title=title, index=i, level=1))

    meta = dict(
        bookId='95fb715fa6bb',
        title='文集',
        author='雅克·拉康',
        region='西方',
        chapterCount=len(chapters),
        chapterTitles=chapter_titles,
        toc=meta_toc,
    )
    with open(f'{OUT_DIR}/meta.json', 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    for i, (title, blocks) in enumerate(chapters):
        print(f'ch{i} {title}: {len(blocks)} blocks, {sum(len(b["value"]) for b in blocks)} chars')
    print('total chars:', sum(len(b['value']) for _, bs in chapters for b in bs))


if __name__ == '__main__':
    main()
