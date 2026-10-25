# -*- coding: utf-8 -*-
"""重建《如何以言行事》(920596aed622) — 15章完整版。

旧状：17章混乱（第十讲空壳27字、ch13-16为标题碎片、第十二讲吞并后两讲内容），
缺失约13%正文。新状：卷首 + 12讲 + 附录 + 索引。
"""
import json
import os
import re

RAW = '/Users/sen/Downloads/raw/incoming-codex/raw-text-handoff-20261023/920596aed622/candidate-01/raw.txt'
OUT_DIR = 'backend/data/book_chapters/920596aed622'

CHAPTERS = [
    (656,  '第一讲 施行式与记述式'),
    (848,  '第二讲 适当的施行式的条件'),
    (1066, '第三讲 不恰当：未成'),
    (1270, '第四讲 不恰当：滥用'),
    (1556, '第五讲 施行式的可能标准'),
    (1786, '第六讲 显性施行式'),
    (2110, '第七讲 显性施行式动词'),
    (2324, '第八讲 话语行为、话语施事行为和话语施效行为'),
    (2608, '第九讲 话语施事行为和话语施效行为之间的区分'),
    (2774, '第十讲“在说当中”对“经由说”'),
    (2990, '第十一讲 陈述、施行话语与话语施事力'),
    (3278, '第十二讲 话语施事力的分类'),
    (4064, '附录'),
    (5042, '索引'),
]
TAIL_AT = 5070


def main():
    lines = open(RAW, encoding='utf-8').read().split('\n')
    bounds = [c[0] for c in CHAPTERS] + [TAIL_AT]
    chapters = [('卷首', [])] + [(t, []) for _, t in CHAPTERS]
    cur = None
    cur_ch = 0

    def flush():
        nonlocal cur
        if cur is not None and cur.strip():
            chapters[cur_ch][1].append(cur)
        cur = None

    for i in range(0, TAIL_AT):
        hit = None
        for ci, (lo, _) in enumerate(CHAPTERS):
            if i == lo:
                hit = ci + 1
                break
        if hit is not None:
            flush()
            cur_ch = hit
            chapters[cur_ch][1].append(CHAPTERS[hit - 1][1])
            cur = None
            continue
        # 卷首内的印刷目录块（482-607）剔除
        if cur_ch == 0 and 482 <= i < 607:
            continue
        s = lines[i].strip()
        if not s:
            continue
        sq = re.sub(r'\s', '', s)
        if re.fullmatch(r'\d{1,3}', sq):
            continue
        if sq.startswith('[SOURCE'):
            break
        # 页眉（第X讲题+页码）
        if re.match(r'^第[一二三四五六七八九十]+讲\s*\S+\s*\d{1,3}$', s):
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

    os.makedirs(OUT_DIR, exist_ok=True)
    # 清陈旧源文件
    for fn in os.listdir(OUT_DIR):
        if fn.endswith('.json') and fn != 'meta.json':
            stem = fn[:-5]
            if stem.isdigit() and int(stem) >= len(chapters):
                os.remove(os.path.join(OUT_DIR, fn))
    meta_toc = []
    chapter_titles = []
    for i, (title, blocks) in enumerate(chapters):
        content = [{'type': 'text', 'value': re.sub(r'\s{2,}', ' ', b)} for b in blocks if b.strip()]
        ch = dict(index=i, title=title, paragraphMode='source', content=content)
        with open(f'{OUT_DIR}/{i}.json', 'w', encoding='utf-8') as f:
            json.dump(ch, f, ensure_ascii=False, indent=1)
        chapter_titles.append(title)
        meta_toc.append(dict(type='chapter', title=title, index=i, level=1))

    meta = dict(
        bookId='920596aed622',
        title='如何以言行事',
        author='约翰·奥斯汀',
        region='西方',
        chapterCount=len(chapters),
        chapterTitles=chapter_titles,
        toc=meta_toc,
    )
    with open(f'{OUT_DIR}/meta.json', 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    for i, (title, blocks) in enumerate(chapters):
        print(f'ch{i} {title[:22]}: {len(blocks)} blocks, {sum(len(b) for b in blocks)} chars')
    print('total chars:', sum(len(b) for _, bs in chapters for b in bs))


if __name__ == '__main__':
    main()
