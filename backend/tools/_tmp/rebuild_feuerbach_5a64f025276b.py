# -*- coding: utf-8 -*-
"""重建《基督教的本质》(5a64f025276b) — 33章完整版。

旧状：28章+14个标题碎片假章；缺三篇序言与附录（解释、注解和引证），
旧数据222,365字 vs raw 331,389字（缺1/3，主要为附录）。
新状：3序言 + 导论2章 + 第一部分(第三~十九章) + 第二部分(第二十~二十八章)
+ 附录；part分层入toc。
"""
import json
import os
import re

RAW = '/Users/sen/Downloads/raw/incoming-codex/raw-text-handoff-20261023/5a64f025276b/candidate-01/raw.txt'
OUT_DIR = 'backend/data/book_chapters/5a64f025276b'

CHAPTERS = [
    (438,  '1841年初版序言', None),
    (540,  '1843年第二版序言', None),
    (790,  '1848年第三版序言', None),
    (818,  '第一章 概论人的本质', '导论'),
    (992,  '第二章 概论宗教的本质', None),
    (1332, '第三章 作为理智本质的上帝', '第一部分 宗教之真正的、即人本学的本质'),
    (1494, '第四章 作为道德本质或法律的上帝', None),
    (1588, '第五章 化身之秘密或作为心之本质的上帝', None),
    (1774, '第六章 受难上帝之秘密', None),
    (1870, '第七章 三位一体与圣母之秘密', None),
    (2020, '第八章 逻各斯与属神的肖像之秘密', None),
    (2162, '第九章 上帝里面的创世原则之秘密', None),
    (2250, '第十章 神秘主义或上帝里面的自然之秘密', None),
    (2478, '第十一章 天意和无中创有之秘密', None),
    (2658, '第十二章 犹太教中创造的意义', None),
    (2812, '第十三章 心情之全能或祈祷之秘密', None),
    (2930, '第十四章 信仰之秘密——奇迹之秘密', None),
    (3086, '第十五章 复活与超自然的诞生之秘密', None),
    (3176, '第十六章 基督教的基督或人格上帝之秘密', None),
    (3354, '第十七章 基督教与异教的区别', None),
    (3500, '第十八章 自由独身与修道之基督教的意义', None),
    (3694, '第十九章 基督教的天国或人格式的不死', None),
    (3942, '第二十章 宗教的基本立场', '第二部分 宗教之不真的（或神学的）本质'),
    (4136, '第二十一章 上帝的实存中的矛盾', None),
    (4270, '第二十二章 上帝的启示中的矛盾', None),
    (4408, '第二十三章 上帝一般本质中的矛盾', None),
    (4618, '第二十四章 思辨的上帝学说中的矛盾', None),
    (4702, '第二十五章 三位一体中的矛盾', None),
    (4770, '第二十六章 圣礼中的矛盾', None),
    (4972, '第二十七章 信仰与爱的矛盾', None),
    (5366, '第二十八章 结束语', None),
    (5494, '附录 解释、注解和引证', None),
]
TAIL_AT = 6652


def main():
    lines = open(RAW, encoding='utf-8').read().split('\n')
    bounds = [c[0] for c in CHAPTERS] + [TAIL_AT]
    chapters = [(t, []) for _, t, _ in CHAPTERS]
    cur = None
    cur_ch = 0

    def flush():
        nonlocal cur
        if cur is not None and cur.strip():
            chapters[cur_ch][1].append(cur)
        cur = None

    for i in range(0, TAIL_AT):
        hit = None
        for ci, (lo, _, _) in enumerate(CHAPTERS):
            if i == lo:
                hit = ci
                break
        if hit is not None:
            flush()
            cur_ch = hit
            chapters[cur_ch][1].append(CHAPTERS[hit][1])
            cur = None
            # 标题换行行消费
            if i + 1 < TAIL_AT:
                nxt = lines[i + 1].strip()
                if 0 < len(nxt) < 20 and not nxt.endswith(('。', '，', '；')) and not re.match(r'^[①②③④⑤⑥⑦⑧⑨⑩\d]', nxt) and i + 1 != bounds[hit + 1]:
                    nxtsq = re.sub(r'[\s　]+', '', nxt)
                    titlesq = re.sub(r'[\s　]+', '', CHAPTERS[hit][1])
                    if nxtsq and nxtsq not in titlesq and titlesq.endswith(nxtsq[:4]):
                        # 下一行确为标题后半
                        lines[i + 1] = '\0CONSUMED'
            continue
        s = lines[i]
        if s == '\0CONSUMED':
            continue
        s = s.strip()
        if not s:
            continue
        sq = re.sub(r'\s', '', s)
        if re.fullmatch(r'\d{1,3}', sq):
            continue
        # 页眉：章题+页码
        if re.match(r'^第[一二三四五六七八九十]+章\s*\S{0,20}\s+\d{1,3}$', s):
            continue
        if re.fullmatch(r'\d{1,3}\s*(1841|1843|1848)?\s*\S{0,12}(序言|导论|附录)?', sq) and len(sq) < 22 and ('序言' in sq or '导论' in sq or '附录' in sq):
            continue
        if sq.startswith('[SOURCE'):
            break
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
    for fn in os.listdir(OUT_DIR):
        if fn.endswith('.json') and fn != 'meta.json':
            stem = fn[:-5]
            if stem.isdigit() and int(stem) >= len(chapters):
                os.remove(os.path.join(OUT_DIR, fn))
    meta_toc = []
    chapter_titles = []
    pending_part = None
    for i, (title, blocks) in enumerate(chapters):
        content = [{'type': 'text', 'value': re.sub(r'\s{2,}', ' ', b)} for b in blocks if b.strip()]
        ch = dict(index=i, title=title, paragraphMode='source', content=content)
        with open(f'{OUT_DIR}/{i}.json', 'w', encoding='utf-8') as f:
            json.dump(ch, f, ensure_ascii=False, indent=1)
        chapter_titles.append(title)
        part = CHAPTERS[i][2]
        if part:
            pending_part = part
        if pending_part:
            meta_toc.append(dict(type='part', title=pending_part, index=i, level=0))
            pending_part = None
        meta_toc.append(dict(type='chapter', title=title, index=i, level=1))

    meta = dict(
        bookId='5a64f025276b',
        title='基督教的本质',
        author='路德维希·费尔巴哈',
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
