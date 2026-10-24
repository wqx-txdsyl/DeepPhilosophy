# -*- coding: utf-8 -*-
"""重建《九章集》(39c09c0f8d09) 章节结构。

来源：candidate-01 raw.txt（石敏敏译全译本，中国社会科学出版社，上下册拼接）。
旧状：卷一~卷五为空壳（各仅6块标题），下册全文被误并入「第六卷」单章；
上册正文（卷一~三+卷四上半）在旧导入中整体丢失（缺约19万字）。
新状：12章 = 卷首/卷一~卷六/附录一~三/译名对照表/译后记；
卷内论文名（I.1式标题行）作节锚点。两个印刷目录页块剔除。
"""
import json
import os
import re

RAW = '/Users/sen/Downloads/raw/incoming-codex/raw-text-handoff-20261023/39c09c0f8d09/candidate-01/raw.txt'
OUT_DIR = 'backend/data/book_chapters/39c09c0f8d09'

# (起始行, 标题)；行号为正文标题行
CHAPTERS = [
    (3218,  '卷一'),
    (4822,  '卷二'),
    (6506,  '卷三'),
    (9086,  '卷四'),
    (12324, '卷五'),
    (14248, '卷六'),
    (18204, '附录一 普罗提诺年表'),
    (18272, '附录二 《九章集》的版本'),
    (18332, '附录三 普罗提诺著述年表和坡菲利排序表对照'),
    (18582, '译名对照表'),
    (19096, '译后记'),
]
# 卷首起点与两个目录块
PRE_START = 0
PRE_END = 2847        # 卷首（含出版说明/总序/导言/生平）
TOC_BLOCKS = [(2848, 3217), (11568, 12323)]  # 上册目录 / 下册目录
TAIL_AT = 19146       # 丛书列表+版权

TREATISE = re.compile(r'^[IVX]+\.\s?\d{1,2}')


def main():
    lines = open(RAW, encoding='utf-8').read().split('\n')
    volumes = [(lo, title) for lo, title in CHAPTERS if title.startswith('卷')]

    def vol_of(i):
        cur = ('卷首', PRE_START)
        for lo, title in volumes:
            if i >= lo:
                cur = (title, lo)
        return cur

    chapters = []  # (title, blocks, head_line)
    chapters.append(('卷首', [], PRE_START))
    for lo, title in CHAPTERS:
        chapters.append((title, [], lo))
    sec_anchors = []  # (chapter_index, block_index, treatise_title)
    pending_treatise = None
    cur = None
    cur_ch = 0

    def flush():
        nonlocal cur
        if cur is not None and cur.strip():
            chapters[cur_ch][1].append(cur)
        cur = None

    for i in range(PRE_START, TAIL_AT):
        # 章界切换
        switched = False
        for ci, (lo, title, _) in enumerate([(c[2], c[0], None) for c in chapters]):
            if i == lo:
                flush()
                cur_ch = ci
                if i != PRE_START:
                    chapters[cur_ch][1].append(title)
                cur = None
                switched = True
                break
        if switched:
            continue
        in_toc = any(a <= i < b for a, b in TOC_BLOCKS)
        if in_toc:
            continue
        s = lines[i].strip()
        if not s:
            continue
        if re.fullmatch(r'\d{1,3}', s):
            continue
        if '九章集·' in s or re.fullmatch(r'\d{1,3}\s*九章集', squash := re.sub(r'\s', '', s)):
            continue
        if s in ('上册目录', '总目录', '下册目录'):
            continue
        # 论文标题行 → 节锚点
        if TREATISE.match(s) and len(s) <= 40 and cur_ch in (1, 2, 3, 4, 5, 6):
            flush()
            pending_treatise = len(chapters[cur_ch][1])
            chapters[cur_ch][1].append(s)
            sec_anchors.append((cur_ch, pending_treatise, s))
            cur = None
            continue
        if cur is None:
            cur = s
        else:
            a, bb = cur[-1:], s[:1]
            if re.fullmatch(r'[A-Za-z0-9]', a or ' ') and re.fullmatch(r'[A-Za-z0-9]', bb or ' '):
                cur += ' ' + s
            else:
                cur += s
        if cur and cur[-1] in '。！？…”」】）':
            flush()
    flush()

    # 修正：卷首作为第一章，其后依次为卷一~卷六、附录、译名表、译后记
    meta_toc = []
    chapter_titles = []
    toc_sections = []
    for i, (title, blocks, _) in enumerate(chapters):
        content = [{'type': 'text', 'value': re.sub(r'\s{2,}', ' ', b) if not b.startswith('卷') else b}
                   for b in blocks]
        ch = dict(index=i, title=title, paragraphMode='source', content=content)
        with open(f'{OUT_DIR}/{i}.json', 'w', encoding='utf-8') as f:
            json.dump(ch, f, ensure_ascii=False, indent=1)
        chapter_titles.append(title)
        meta_toc.append(dict(type='chapter', title=title, index=i, level=1))
    for ch_idx, bi, t in sec_anchors:
        meta_toc.append(dict(type='section', title=t, index=ch_idx, sec=bi, level=2))

    meta = dict(
        bookId='39c09c0f8d09',
        title='九章集',
        author='普罗提诺',
        region='西方',
        chapterCount=len(chapters),
        chapterTitles=chapter_titles,
        toc=meta_toc,
    )
    with open(f'{OUT_DIR}/meta.json', 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    for i, (title, blocks, _) in enumerate(chapters):
        print(f'ch{i} {title[:18]}: {len(blocks)} blocks, {sum(len(b) for b in blocks)} chars')
    print('sections:', len(sec_anchors))


if __name__ == '__main__':
    main()
