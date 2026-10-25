# -*- coding: utf-8 -*-
"""重建《从逻辑的观点看》(07f28f142bdc) 章节结构。

来源：candidate-01 raw.txt（陈启伟等译，9篇论文+中译本序+索引）。
旧状：整书单章。新状：11章。OCR连续重复行去重（仅相邻全同行）；
页码/页眉（N、题+页码 / 从逻辑的观点看）剔除；脚注①行保留为独立块。
"""
import json
import os
import re

RAW = '/Users/sen/Downloads/raw/incoming-codex/raw-text-handoff-20261023/07f28f142bdc/candidate-01/raw.txt'
OUT_DIR = 'backend/data/book_chapters/07f28f142bdc'

CHAPTERS = [
    (244,  '中译本序'),
    (778,  '一、论何物存在'),
    (1028, '二、经验论的两个教条'),
    (1446, '三、语言学中的意义问题'),
    (1650, '四、同一性、实指和实在化'),
    (2186, '五、数理逻辑的新基础'),
    (2278, '六、逻辑与共相的实物化'),
    (2764, '七、略谈关于指称的理论'),
    (2924, '八、指称和模态'),
    (3390, '九、意义和存在推理'),
    (3872, '索引'),
]
TWO_LINE = {3390}


def squash(s):
    return re.sub(r'[\s　]+', '', s)


def main():
    lines = open(RAW, encoding='utf-8').read().split('\n')
    bounds = [c[0] for c in CHAPTERS] + [len(lines)]
    chapters = []
    for ci, (lo, title) in enumerate(CHAPTERS):
        end = bounds[ci + 1]
        blocks = []
        skip = 0
        prev = None
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
            if sq == '从逻辑的观点看' or re.fullmatch(r'\d{0,3}从逻辑的观点看', sq):
                continue
            # 页眉：编号+题+页码（如「一、论何物存在      3」）
            if re.match(r'^[一二三四五六七八九]+、\S+\s+\d{1,3}$', s):
                continue
            if sq.startswith('[SOURCE'):
                break
            if i == lo:
                blocks.append({'type': 'text', 'value': title})
                if lo in TWO_LINE:
                    skip = 1
                prev = None
                continue
            # 连续全同的OCR重复行去重
            if sq == prev:
                continue
            prev = sq
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
        bookId='07f28f142bdc',
        title='从逻辑的观点看',
        author='威拉德·冯·奥曼·蒯因',
        region='西方',
        chapterCount=len(chapters),
        chapterTitles=chapter_titles,
        toc=meta_toc,
    )
    with open(f'{OUT_DIR}/meta.json', 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    for i, (title, blocks) in enumerate(chapters):
        print(f'ch{i} {title[:20]}: {len(blocks)} blocks, {sum(len(b["value"]) for b in blocks)} chars')
    print('total chars:', sum(len(b['value']) for _, bs in chapters for b in bs))


if __name__ == '__main__':
    main()
