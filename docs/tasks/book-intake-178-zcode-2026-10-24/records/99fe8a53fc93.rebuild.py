# -*- coding: utf-8 -*-
"""重建《声音与现象》(99fe8a53fc93) — 8章完整版。

旧状：9章（ch0以丛书名作章题、ch6以脚注行作章题），缺德里达导言等约30%。
新状：导言 + 第一章~第七章；篇末译注按来源顺序保留在第七章尾部。
"""
import json
import os
import re

RAW = '/Users/sen/Downloads/raw/incoming-codex/raw-text-handoff-20261023/99fe8a53fc93/public-epub/raw.txt'
OUT_DIR = 'backend/data/book_chapters/99fe8a53fc93'

CHAPTERS = [
    (20,  '导言'),
    (187, '第一章 符号和诸种符号'),
    (269, '第二章 指号和还原'),
    (310, '第三章 作为自白的“意谓”'),
    (423, '第四章 “意谓”和再现'),
    (542, '第五章 符号与瞬间'),
    (657, '第六章 保持沉默的声音'),
    (820, '第七章 根源的补充'),
]


def main():
    lines = open(RAW, encoding='utf-8').read().split('\n')
    bounds = [c[0] for c in CHAPTERS] + [len(lines)]
    chapters = []
    for ci, (lo, title) in enumerate(CHAPTERS):
        end = bounds[ci + 1]
        blocks = []
        prev = None
        for i in range(lo, end):
            s = lines[i].strip()
            if not s:
                continue
            if i == lo:
                blocks.append(title)
                continue
            sq = re.sub(r'\s', '', s)
            if sq == prev:
                continue
            prev = sq
            if re.fullmatch(r'\d{1,3}', sq):
                continue
            blocks.append(re.sub(r'\s{2,}', ' ', s))
        chapters.append((title, blocks))

    os.makedirs(OUT_DIR, exist_ok=True)
    for fn in os.listdir(OUT_DIR):
        if fn.endswith('.json') and fn != 'meta.json':
            stem = fn[:-5]
            if stem.isdigit() and int(stem) >= len(chapters):
                os.remove(os.path.join(OUT_DIR, fn))
    meta_toc = []
    chapter_titles = []
    for i, (title, blocks) in enumerate(chapters):
        content = [{'type': 'text', 'value': b} for b in blocks if b.strip()]
        ch = dict(index=i, title=title, paragraphMode='source', content=content)
        with open(f'{OUT_DIR}/{i}.json', 'w', encoding='utf-8') as f:
            json.dump(ch, f, ensure_ascii=False, indent=1)
        chapter_titles.append(title)
        meta_toc.append(dict(type='chapter', title=title, index=i, level=1))

    meta = dict(
        bookId='99fe8a53fc93',
        title='声音与现象',
        author='雅克·德里达',
        region='西方',
        chapterCount=len(chapters),
        chapterTitles=chapter_titles,
        toc=meta_toc,
    )
    with open(f'{OUT_DIR}/meta.json', 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    for i, (title, blocks) in enumerate(chapters):
        print(f'ch{i} {title[:18]}: {len(blocks)} blocks, {sum(len(b) for b in blocks)} chars')
    print('total chars:', sum(len(b) for _, bs in chapters for b in bs))


if __name__ == '__main__':
    main()
