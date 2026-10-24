# -*- coding: utf-8 -*-
"""重建《纯粹现象学和现象学哲学的观念》(8ddb35d61e22) — 17章完整版。

旧状：18章且系统性缺失约21%正文；ch15-17把正文行/脚注行误当章题。
新状：卷首 + 四篇13章（章号重启即篇界）+ 主题索引 + 人名索引 + 中译者术语解释。
"""
import json
import os
import re

RAW = '/Users/sen/Downloads/raw/incoming-codex/raw-text-handoff-20261023/8ddb35d61e22/candidate-01/raw.txt'
OUT_DIR = 'backend/data/book_chapters/8ddb35d61e22'

CHAPTERS = [
    (586,  '第一章 事实和本质', '第一篇'),
    (782,  '第二章 自然主义的错误解释', None),
    (870,  '第一章 自然态度的设定及其排除', '第二篇'),
    (936,  '第二章 意识和自然现实', None),
    (1108, '第三章 纯粹意识区域', None),
    (1236, '第四章 现象学还原', None),
    (1314, '第一章 方法的预备考察', '第三篇'),
    (1474, '第二章 纯粹意识的一般结构', None),
    (1764, '第三章 意向作用和意向对象', None),
    (1890, '第四章 关于意向作用一意向对象', None),
    (2472, '第一章 意向对象的意义和与对象的关系', '第四篇'),
    (2618, '第二章 理性的现象学', None),
    (2786, '第三章 关于理性理论问题', None),
    (2956, '主题索引', None),
    (3644, '人名索引', None),
    (5382, '中译者术语解释', None),
]
TAIL_AT = 5770  # 版权/丛书广告行


def main():
    lines = open(RAW, encoding='utf-8').read().split('\n')
    bounds = [c[0] for c in CHAPTERS] + [TAIL_AT]
    chapters = [( '卷首', [])] + [(t, []) for _, t, _ in CHAPTERS]
    cur = None
    cur_ch = 0

    def flush():
        nonlocal cur
        if cur is not None and cur.strip():
            chapters[cur_ch][1].append(cur)
        cur = None

    for i in range(0, TAIL_AT):
        hit = None
        for ci, (lo, t, _) in enumerate(CHAPTERS):
            if i == lo:
                hit = ci + 1
                break
        if hit is not None:
            flush()
            cur_ch = hit
            chapters[cur_ch][1].append(CHAPTERS[hit - 1][1])
            cur = None
            continue
        s = lines[i].strip()
        if not s:
            continue
        sq = re.sub(r'\s', '', s)
        if re.fullmatch(r'\d{1,3}', sq):
            continue
        # 篇四章内的伪章题正文行保留为正文（它们与真章题文本不同，天然不匹配title丢弃规则）
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

    os.makedirs(OUT_DIR, exist_ok=True)
    meta_toc = []
    chapter_titles = []
    pending_part = None
    for i, (title, blocks) in enumerate(chapters):
        content = [{'type': 'text', 'value': re.sub(r'\s{2,}', ' ', b)} for b in blocks if b.strip()]
        ch = dict(index=i, title=title, paragraphMode='source', content=content)
        with open(f'{OUT_DIR}/{i}.json', 'w', encoding='utf-8') as f:
            json.dump(ch, f, ensure_ascii=False, indent=1)
        chapter_titles.append(title)
        part = CHAPTERS[i - 1][2] if 1 <= i <= len(CHAPTERS) else None
        if part:
            pending_part = part
        if pending_part:
            meta_toc.append(dict(type='part', title=pending_part, index=i, level=0))
            pending_part = None
        meta_toc.append(dict(type='chapter', title=title, index=i, level=1))

    meta = dict(
        bookId='8ddb35d61e22',
        title='纯粹现象学和现象学哲学的观念',
        author='埃德蒙德·胡塞尔',
        region='西方',
        chapterCount=len(chapters),
        chapterTitles=chapter_titles,
        toc=meta_toc,
    )
    with open(f'{OUT_DIR}/meta.json', 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    for i, (title, blocks) in enumerate(chapters):
        print(f'ch{i} {title[:24]}: {len(blocks)} blocks, {sum(len(b) for b in blocks)} chars')
    print('total chars:', sum(len(b) for _, bs in chapters for b in bs))


if __name__ == '__main__':
    main()
