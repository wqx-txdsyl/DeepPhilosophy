# -*- coding: utf-8 -*-
"""重建《书写与差异》(39cd5aab287c) 章节结构。

来源：candidate-01 raw.txt（张宁译，上海译文《书写与差异》全本）。
旧状：仅6章且用的是节名（如「一般书写与一般经济学」「一种无保留的黑格尔主义」
实为《从有限经济学到一般经济学》一文的子节），缺8篇。
新状：15章（访谈代序/译者前言/12篇论文/篇章来源/特殊用语）+ 节锚点。
"""
import json
import os
import re

RAW = '/Users/sen/Downloads/raw/incoming-codex/raw-text-handoff-20261023/39cd5aab287c/candidate-01/raw.txt'
OUT_DIR = 'backend/data/book_chapters/39cd5aab287c'

CHAPTERS = [
    (394,  '访谈代序'),
    (758,  '译者前言'),
    (962,  '力量与意谓'),
    (1722, '我思与疯狂史'),
    (2456, '爱德蒙·雅毕斯与书的疑问'),
    (2896, '暴力与形而上学——论埃马纽埃尔·勒维纳斯的思想'),
    (5038, '“生成与结构”及现象学'),
    (5468, '被劫持的言语'),
    (6168, '弗洛伊德与书写舞台'),
    (6990, '残酷戏剧与再现的关闭'),
    (7490, '从有限经济学到一般经济学——一种无保留的黑格尔主义'),
    (8264, '人文科学话语中的结构、符号与游戏'),
    (8578, '省略/循回'),
    (8850, '篇章来源'),
    (8924, '特殊用语（术语、人名中西文对照表）'),
]
SECTIONS = [(1722, 1734, '一张透明的扉页把它与疯狂分开'),
            (7490, 8014, '一般书写与一般经济学'),
            (8578, 8734, '一个洞，那只是个洞'),
            (8578, 8774, '三个问题引诱了那本书')]
TAIL_AT = 10193  # 547 页码后为 SOURCE NOTES 工件
TWO_LINE_TITLE = {7490}  # 下一行为标题后半
NO_HEAD_DROP = {'篇章来源', '特殊用语（术语、人名中西文对照表）'}


def squash(s):
    return re.sub(r'[\s　]+', '', s)


def main():
    lines = open(RAW, encoding='utf-8').read().split('\n')
    bounds = [c[0] for c in CHAPTERS] + [TAIL_AT]
    chapters = []
    for ci, (lo, title) in enumerate(CHAPTERS):
        end = bounds[ci + 1]
        blocks = []
        skip = 0
        for i in range(lo, end):
            s = lines[i].strip()
            if not s:
                continue
            if skip > 0:
                skip -= 1
                continue
            sq = squash(s)
            if re.fullmatch(r'\d{1,3}', sq):
                continue
            if sq.startswith('[SOURCE NOTES'):
                break
            if i == lo:
                blocks.append({'type': 'text', 'value': title})
                if lo in TWO_LINE_TITLE:
                    skip = 1  # 消费标题第二行
                continue
            if title not in NO_HEAD_DROP and sq == squash(title):
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
    # 节锚点
    for ch_idx, sec_line, sec_title in SECTIONS:
        ci = [k for k, c in enumerate(CHAPTERS) if c[0] == ch_idx][0]
        blocks = chapters[ci][1]
        for bi, b in enumerate(blocks):
            if squash(b['value']).startswith(squash(sec_title)):
                meta_toc.append(dict(type='section', title=sec_title, index=ci, sec=bi, level=2))
                break

    meta = dict(
        bookId='39cd5aab287c',
        title='书写与差异',
        author='雅克·德里达',
        region='西方',
        chapterCount=len(chapters),
        chapterTitles=chapter_titles,
        toc=meta_toc,
    )
    with open(f'{OUT_DIR}/meta.json', 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    for i, (title, blocks) in enumerate(chapters):
        print(f'ch{i} {title[:26]}: {len(blocks)} blocks, {sum(len(b["value"]) for b in blocks)} chars')
    print('total chars:', sum(len(b['value']) for _, bs in chapters for b in bs))


if __name__ == '__main__':
    main()
