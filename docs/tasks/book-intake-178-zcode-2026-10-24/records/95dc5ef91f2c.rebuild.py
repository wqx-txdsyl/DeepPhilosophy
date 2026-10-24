# -*- coding: utf-8 -*-
"""重建《词与物》(95dc5ef91f2c) 章节结构。

来源：memoof-959 raw.txt（上海三联2016修订译本扫描OCR文字层，莫伟民译）。
单遍扫描 1159..tail_start：页码行/页眉行剔除；目录页(1487-1600)剔除；
段落以≥2空格缩进起段；章界按 CH_BOUNDARIES（lo=标题行），节题按正文行定位；
OCR残形编题修正常题（策—编→第一编 / 第—编→第二编 / 第「节→第一节）。
"""
import json
import os
import re

RAW = '/Users/sen/Downloads/raw/incoming-codex/raw-text-handoff-20261023/95dc5ef91f2c/memoof-959/raw.txt'
OUT_DIR = 'backend/data/book_chapters/95dc5ef91f2c'

# (lo=标题行, hi=-exclusive, title, part)
CH_BOUNDARIES = [
    (94, 148, '总序', None),
    (149, 1092, '译者的话：19世纪—"人"的世纪', None),
    (1092, 1487, '前言', None),
    (1602, 2142, '第一章 宫中侍女', '第一编'),
    (2142, 3295, '第二章 世界的散文', None),
    (3295, 4591, '第三章 表象', None),
    (4591, 6511, '第四章 言说', None),
    (6511, 8119, '第五章 分类', None),
    (8119, 9941, '第六章 交换', None),
    (9943, 11180, '第七章 表象的界限', '第二编'),
    (11180, 13190, '第八章 劳动、生命和语言', None),
    (13190, 14731, '第九章 人及其复本', None),
    (14731, 16381, '第十章 人文科学', None),
    (16381, 16544, '附录一 人名对照表', None),
    (16544, None, '附录二 术语对照表', None),
]
# OCR残形编题行 → (正题, 归属章index, 前置章范围)
PART_LINES = {1601: ('第一编', 1, (1500, 1602)), 9942: ('第二编', 7, (9900, 9943))}
TAIL_JUNK = re.compile(r'^\s*\d{1,2}[.．、]\s*《')


def squash(s):
    return re.sub(r'\s+', '', s)


def main():
    lines = open(RAW, encoding='utf-8').read().split('\n')
    n = len(lines)
    tail_start = n
    for i in range(16560, n):
        if '已出书目' in lines[i]:
            tail_start = i
            break
    print('tail junk starts at line', tail_start, repr(lines[tail_start][:60]))
    print('appendix2 last lines:', repr(lines[tail_start - 4][:60]), repr(lines[tail_start - 2][:60]))

    chapters = [[b[2], []] for b in CH_BOUNDARIES]
    cur_ch = None
    cur = None
    in_note = False

    def flush():
        nonlocal cur
        if cur is not None and cur.strip() and cur_ch is not None:
            chapters[cur_ch][1].append(('p', cur))
        cur = None

    for i in range(94, tail_start):
        s = lines[i].strip()
        if not s:
            continue
        # 章界切换（含前言/附录）
        nxt = None
        for ci, (lo, hi, title, part) in enumerate(CH_BOUNDARIES):
            if i == lo:
                nxt = ci
                break
        if nxt is not None:
            flush()
            cur_ch = nxt
            chapters[cur_ch][1].append(('h', CH_BOUNDARIES[nxt][2]))
            cur = None
            continue
        if 1487 <= i < 1601:
            continue  # 目录页
        # 找当前所属章（标题行之间的行归属前一章）
        if cur_ch is None or i >= (CH_BOUNDARIES[cur_ch][1] or tail_start):
            for ci, (lo, hi, title, part) in enumerate(CH_BOUNDARIES):
                if lo <= i < (hi if hi is not None else tail_start):
                    if ci != cur_ch:
                        flush()
                        cur_ch = ci
                    break
        if re.fullmatch(r'\d{1,3}', s):
            if in_note:
                flush()
                in_note = False
            continue  # 页码（页脚注区到此结束）
        # 脚注区状态机：独立注号行开启，注区持续到页码行
        if re.fullmatch(r'[①-⑳]', s):
            flush()
            in_note = True
            cur = s
            continue
        if in_note:
            sqn2 = squash(s)
            m2 = re.fullmatch(r'[①-⑳](.*)', sqn2)
            if m2 and len(sqn2) < 40:
                flush()
                cur = s
                continue
            if cur is not None and len(cur) > 1000:
                # 注文异常过长：视为误入注区，退出注模式
                flush()
                in_note = False
            cur = cur + s if cur is not None else s
            continue
        core = re.sub(r'^[■◆◇·.]+\s*', '', s)
        sqc = squash(core)
        if sqc in ('词与物', '人文科学的考古学', '目录', '前言') or re.fullmatch(r'[■]+', sqc) \
                or sqc.startswith('词与物') and len(sqc) <= 8 or sqc.startswith('译者的话') and len(sqc) <= 24:
            continue  # 页眉（前言/译者的话页眉亦剔除）
        # OCR残形编题（按位置归属下一章块首）
        sq = squash(core)
        hit = PART_LINES.get(i)
        if hit and hit[2][0] <= i < hit[2][1]:
            flush()
            cur_ch = hit[1]
            chapters[cur_ch][1].append(('h', hit[0]))
            continue
        # 章题页眉重复：真实章题已由章界切换处理，其余章题形行一律视为页眉
        if re.match(r'^第[一二三四五六七八九十]+章', sq):
            continue
        # 节题
        sqn = sq.replace('「', '一')
        m = re.match(r'^(第[一二三四五六七八九十]+节)(.*)$', sqn)
        if m and len(sqn) <= 30:
            flush()
            t = m.group(1) + (' ' + m.group(2) if m.group(2) else '')
            chapters[cur_ch][1].append(('h', t))
            continue
        # 起段：行首≥2空格
        if re.match(r'^\s{2,}', lines[i]) or cur is None:
            flush()
            cur = s
        else:
            cur += s
    flush()

    os.makedirs(OUT_DIR, exist_ok=True)
    meta_toc = []
    chapter_titles = []
    sec_total = 0
    for i, (title, blocks) in enumerate(chapters):
        content = []
        for kind, text in blocks:
            t = re.sub(r'\s{2,}', ' ', text).strip()
            if t:
                content.append({'type': 'text', 'value': t})
        ch = dict(index=i, title=title, paragraphMode='source', content=content)
        with open(f'{OUT_DIR}/{i}.json', 'w', encoding='utf-8') as f:
            json.dump(ch, f, ensure_ascii=False, indent=1)
        chapter_titles.append(title)

    # toc：part + chapter + section
    toc2 = []
    pending_part = None
    for i, (title, blocks) in enumerate(chapters):
        part = CH_BOUNDARIES[i][3]
        if part:
            pending_part = part
        if pending_part:
            toc2.append(dict(type='part', title=pending_part, index=i, level=0))
            pending_part = None
        toc2.append(dict(type='chapter', title=title, index=i, level=1))
        for bi, (kind, text) in enumerate(blocks):
            if kind == 'h' and re.match(r'^第[一二三四五六七八九十]+ ?节', text):
                toc2.append(dict(type='section', title=text, index=i, sec=bi, level=2))
                sec_total += 1

    meta = dict(
        bookId='95dc5ef91f2c',
        title='词与物',
        author='米歇尔·福柯',
        region='西方',
        chapterCount=len(chapters),
        chapterTitles=chapter_titles,
        toc=toc2,
    )
    with open(f'{OUT_DIR}/meta.json', 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)

    for i, (title, blocks) in enumerate(chapters):
        chars = sum(len(t) for _, t in blocks)
        print(f'ch{i} {title}: {len(blocks)} blocks, {chars} chars')
    print('sections:', sec_total)
    print('total chars:', sum(len(t) for _, bs in chapters for _, t in bs))


if __name__ == '__main__':
    main()
