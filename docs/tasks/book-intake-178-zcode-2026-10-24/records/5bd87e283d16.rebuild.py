# -*- coding: utf-8 -*-
"""重建《千高原》(5bd87e283d16) 章节结构。

来源：candidate-01 raw.txt（上海人民出版社2023修订译本，姜宇辉译，资本主义与精神分裂卷2）。
旧状：整书单章1619块，封面/营销文案/目录/插图目录/CIP/丛书列表混入。
新状：16章 = 15座高原 + 修订版后记；正文为分页断行文本，按"非终结标点跨行/跨页
接续"拼接段落；页码行、页眉行（章题/书名重复）剔除；页脚注①行独立成段。
"""
import json
import os
import re

RAW = '/Users/sen/Downloads/raw/incoming-codex/raw-text-handoff-20261023/5bd87e283d16/candidate-01/raw.txt'
OUT_DIR = 'backend/data/book_chapters/5bd87e283d16'

# (起始标题行, 正题)
PLATEAUS = [
    (326,  '1. 导论：根茎'),
    (622,  '2. 1914年：一匹或几匹狼？'),
    (764,  '3. 公元前10000年：道德的地质学'),
    (1148, '4. 1923年11月20日：语言学的公设'),
    (1668, '5. 公元前587年——公元70年：论几种符号的机制'),
    (2106, '6. 1947年11月28日：怎样将自身变为一具无器官的身体？'),
    (2300, '7. 元年：颜貌'),
    (2666, '8. 1874年：三则短篇小说，或“发生了什么？”'),
    (2884, '9. 1933年：微观政治和节段性'),
    (3270, '10. 1730年：生成—强度，生成—动物，生成—不可感知'),
    (4280, '11. 1837年：迭奏曲'),
    (4830, '12. 1227年——论游牧学：战争机器'),
    (5838, '13. 公元前7000年：捕获装置'),
    (6480, '14. 1440年：平滑与纹理化'),
    (6824, '15. 结论：具体的规则与抽象的机器'),
    (6968, '修订版后记'),
]
TAIL_AT = 7006  # CIP 起
HEAD_PREFIXES = ('资本主义与精神分裂',)


def squash(s):
    return re.sub(r'\s+', '', s)


def is_head_line(sq):
    """章题页眉：章题形（冒号/分号/破折号/空格变体）或书名页眉。"""
    if sq.startswith(HEAD_PREFIXES):
        return True
    for _, t in PLATEAUS:
        a = squash(t)
        # 归一化比较：去掉编号点后前12字一致且长度接近
        a2 = a.replace('.', '').replace('：', '').replace('？', '').replace('—', '').replace('，', '')
        for probe in (sq, sq.replace(';', '：').replace('；', '：').replace(':', '：').replace('一', '—')):
            b2 = probe.replace('.', '').replace('：', '').replace('？', '').replace('—', '').replace('，', '')
            if len(b2) >= 8 and (b2.startswith(a2[:10]) or a2.startswith(b2[:10])):
                return True
    return False


def main():
    lines = open(RAW, encoding='utf-8').read().split('\n')
    bounds = [p[0] for p in PLATEAUS] + [TAIL_AT]
    chapters = []
    pending = None  # 待接续的半句

    def flush(force=True):
        nonlocal pending
        if pending is not None and pending.strip():
            chapters[-1][1].append(pending)
        pending = None

    for ci, (lo, title) in enumerate(PLATEAUS):
        chapters.append((title, []))
        end = bounds[ci + 1]
        for i in range(lo + 1, end):  # lo 行为章题，由边界直接落块
            s = lines[i].strip()
            if not s:
                continue
            if re.fullmatch(r'\d{1,3}', s):
                continue  # 页码
            sq = squash(s)
            if is_head_line(sq):
                continue  # 页眉
            # 页脚注①行
            if re.match(r'^[①-⑳]', s):
                flush()
                chapters[-1][1].append(s)
                pending = None
                continue
            # 章内小节题（无缩进短行）不特殊处理，并入段落流
            if pending is None:
                pending = s
            else:
                pending += s
            # 段落终结判断：句末标点收尾则收段
            if pending and pending[-1] in '。！？…””」』）】':
                flush()
        flush()

    os.makedirs(OUT_DIR, exist_ok=True)
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
        bookId='5bd87e283d16',
        title='千高原',
        author='吉尔·德勒兹',
        region='西方',
        chapterCount=len(chapters),
        chapterTitles=chapter_titles,
        toc=meta_toc,
    )
    with open(f'{OUT_DIR}/meta.json', 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)

    for i, (title, blocks) in enumerate(chapters):
        print(f'ch{i} {title}: {len(blocks)} blocks, {sum(len(b) for b in blocks)} chars')
    print('total chars:', sum(len(b) for _, bs in chapters for b in bs))


if __name__ == '__main__':
    main()
