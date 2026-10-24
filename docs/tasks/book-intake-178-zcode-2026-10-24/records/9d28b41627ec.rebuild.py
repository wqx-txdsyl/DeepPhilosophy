# -*- coding: utf-8 -*-
"""重建《西田幾多郎哲學選輯Ⅰ》(9d28b41627ec) 章节结构。

来源：extra-062 source.pdf（207页，黃文宏譯，公版PDF文字层）。
问题：现有8章把凡例条目当章题，且選文解說之后整本（五篇選文＋年譜＋後記）
全部埋在一个806块章节里，页码/页眉/旁页码粘进段落。

方法：pdfplumber 坐标级提取，按字号分层：
  >=13.5 选文大标题；12 正文/书名/序题/章题（居中行独立成块）；
  10 章末脚注区（按注号分组）；9 正文上标注号（按x精确回插）；
  10.6 边栏旁页码（剔除）；11 页脚页码（剔除）。//与////为旁页码锚点记号（剔除）。
"""
import json
import os
import re
from collections import defaultdict

import pdfplumber

PDF = '/Users/sen/Downloads/raw/incoming-codex/raw-text-handoff-20261023/extras/extra-062/source.pdf'
OUT_DIR = 'backend/data/book_chapters/9d28b41627ec'

CJK_C = '\u3000-\u9fff\uff00-\uffef\u2e80-\u2eff\u3040-\u30ff\u31f0-\u4dbf\uf900-\ufaff'
CJK = '[' + CJK_C + ']'

CHAPTERS = [
    (2,   '凡例'),
    (3,   '一、生平與著作'),
    (13,  '二、選文解說'),
    (22,  '自著序'),
    (76,  '〈絕對自由意志〉'),
    (90,  '〈種種世界〉'),
    (98,  '〈場所〉（1926）'),
    (142, '〈場所邏輯與宗教的世界觀〉（1945）'),
    (199, '西田幾多郎年譜'),
    (206, '譯者後記'),
]


def is_cjk(ch):
    return bool(ch) and bool(re.match(CJK, ch))


def clean_spaces(s):
    s = re.sub(r'(?<=' + CJK_C + r']) (?=' + CJK_C + r'])', '', s)
    s = re.sub(r' (?=[，。；：、）」』】〉〕”])', '', s)
    s = re.sub(r'(?<=[（「『【〈〔“]) ', '', s)
    return s.strip()


def join_row(ws, markers):
    """一行正文：剔纯斜杠词，size9上标注号按x回插。返回(text, x0, x1)。"""
    line_words = [w for w in ws if not re.fullmatch(r'[/%]+', w['text'])]
    if not line_words:
        return '', 0, 0
    items = [(w['x0'], 0, w['text'], w['x1']) for w in line_words]
    for m in markers:
        items.append((m['x0'] + 0.6, 1, m['text'], m['x1']))
    items.sort(key=lambda it: (it[0], it[1]))
    out = ''
    prev = None  # (x1, prio, text)
    for x, prio, t, x1 in items:
        t = re.sub(r'/+', '', t)  # 旁页码锚点记号（粘连或独立词一并剔）
        if not t:
            continue
        if prev is not None:
            px1, pprio, pt = prev
            a, b = pt[-1:], t[:1]
            if prio == 1 or pprio == 1:
                pass  # 上标紧贴
            elif re.fullmatch(r'[A-Za-z0-9]', a or ' ') and re.fullmatch(r'[A-Za-z0-9]', b or ' '):
                if x - px1 >= 1.0:
                    out += ' '
            elif is_cjk(a) and is_cjk(b):
                pass
            else:
                out += ' '
        out += t
        prev = (x1, prio, t)
    return out, min(w['x0'] for w in line_words), max(w['x1'] for w in line_words)


class Page:
    def __init__(self, pdf, pi):
        self.pi = pi
        p = pdf.pages[pi]
        words = p.extract_words(extra_attrs=['size'])
        self.big = [w for w in words if w['size'] >= 13.5]
        self.main = [w for w in words if 11.5 <= w['size'] <= 12.5]
        self.markers = [w for w in words if 8.5 <= w['size'] <= 9.5]
        self.side = [w for w in words if 10.4 <= w['size'] <= 10.8]
        self.foot = [w for w in words if 9.6 <= w['size'] <= 10.3]
        self.footers = [w for w in words if 10.85 <= w['size'] <= 11.6]

    @staticmethod
    def rows(words, tol=4.0, merge_gap=8.0):
        rs = defaultdict(list)
        for w in words:
            rs[round(w['top'] / tol)].append(w)
        buckets = []
        for key in sorted(rs):
            ws = rs[key]
            top = min(w['top'] for w in ws)
            if buckets and top - buckets[-1][0] < merge_gap:
                buckets[-1] = (buckets[-1][0], buckets[-1][1] + ws)
            else:
                buckets.append((top, ws))
        return buckets


def main():
    pdf = pdfplumber.open(PDF)
    n = len(pdf.pages)
    starts = [c[0] for c in CHAPTERS] + [n]

    dropped = defaultdict(int)
    results = []
    for ci, (cstart, ctitle) in enumerate(CHAPTERS):
        cend = starts[ci + 1]
        blocks = []
        for pi in range(cstart, cend):
            page = Page(pdf, pi)
            dropped['side_refs'] += len(page.side)
            dropped['page_footers'] += len(page.footers)
            for top, ws in Page.rows(page.main):
                mtops = [m for m in page.markers if abs(m['top'] - top - 2.5) < 6]
                text, x0, x1 = join_row(ws, mtops)
                if not text.strip():
                    continue
                centered = x0 > 180 and x1 < 470 and len(text.strip()) <= 42
                kind = 'sep' if centered else 'row'
                blocks.append(dict(page=pi, top=top, x0=x0, x1=x1,
                                   text=text.strip(), kind=kind))
            for top, ws in Page.rows(page.big, tol=6.0, merge_gap=15.0):
                t = re.sub(r'[/]+', '', ''.join(
                    w['text'] for w in sorted(ws, key=lambda w: w['x0']))).strip()
                if t:
                    blocks.append(dict(page=pi, top=top, x0=min(w['x0'] for w in ws),
                                       x1=max(w['x1'] for w in ws), text=t, kind='big'))
            frows = []
            used_markers = []
            for top, ws in Page.rows(page.main):
                for m in page.markers:
                    if abs(m['top'] - top - 2.5) < 6:
                        used_markers.append(id(m))
            # 未被正文行消费的size9词：脚注区注号（x<105）→ 独立注号行
            for m in page.markers:
                if id(m) in used_markers:
                    continue
                if m['x0'] < 105 and re.fullmatch(r'\d{1,3}', m['text']):
                    frows.append((m['top'], m['text']))
            for top, ws in Page.rows(page.foot):
                text, _, _ = join_row(ws, [])
                text = clean_spaces(text)
                if text:
                    frows.append((top, text))
            frows.sort()
            units = []
            for top, text in frows:
                if re.fullmatch(r'\d{1,3}', text):
                    units.append(text)
                elif units:
                    units[-1] += text
                else:
                    units.append(text)
            for u in units:
                blocks.append(dict(page=pi, top=10 ** 7, x0=0, x1=0, text=u, kind='note'))
        blocks.sort(key=lambda b: (b['page'], b['top']))

        paras = []
        cur = None
        body_left = 90.0 if cstart < 13 else 85.0
        for b in blocks:
            t = b['text'].strip()
            if not t:
                continue
            if b['kind'] == 'big' and t == ctitle:
                continue
            if b['kind'] == 'sep' and t == ctitle:
                continue
            if b['kind'] in ('big', 'sep', 'note'):
                if cur:
                    paras.append(dict(kind='p', text=cur))
                    cur = None
                paras.append(dict(kind=b['kind'], text=clean_spaces(t) if b['kind'] != 'note' else t))
                continue
            if cur is None:
                cur = t
            elif (b['x0'] - body_left) >= 13 or re.match(r'^【', t):
                paras.append(dict(kind='p', text=cur))
                cur = t
            else:
                a, bb = cur[-1:], t[:1]
                if re.fullmatch(r'[A-Za-z0-9]', a or ' ') and re.fullmatch(r'[A-Za-z0-9]', bb or ' '):
                    cur += ' ' + t
                else:
                    cur += t
        if cur:
            paras.append(dict(kind='p', text=cur))
        if ctitle == '凡例':
            text = ''.join(p['text'] for p in paras)
            if text.startswith('凡例'):
                text = text[len('凡例'):]
            paras = [dict(kind='p', text=seg.strip())
                     for seg in re.split(r'(?<=[。；])(?=[一二三四五六七八九十]+、)', text)
                     if seg.strip()]
        results.append((ctitle, paras))

    def rebuild_years(paras):
        out = []
        for p in paras:
            if p['kind'] != 'p':
                out.append(p)
                continue
            for line in re.split(r'(?=1[89]\d{2} ?年（|20\d{2} ?年（)', p['text']):
                line = line.strip()
                if line:
                    out.append(dict(kind='p', text=line))
        return out

    for i, (title, paras) in enumerate(results):
        if title == '西田幾多郎年譜':
            results[i] = (title, rebuild_years(paras))

    os.makedirs(OUT_DIR, exist_ok=True)
    meta_toc = []
    chapter_titles = []
    for i, (title, paras) in enumerate(results):
        content = [{'type': 'text', 'value': clean_spaces(p['text']) if p['kind'] == 'p' else p['text']}
                   for p in paras]
        ch = dict(index=i, title=title, paragraphMode='source', content=content)
        with open(f'{OUT_DIR}/{i}.json', 'w', encoding='utf-8') as f:
            json.dump(ch, f, ensure_ascii=False, indent=1)
        chapter_titles.append(title)
        meta_toc.append(dict(type='chapter', title=title, index=i, level=1))

    # —— section 锚点 ——
    def find_idx(content, pred, start=0):
        for k in range(start, len(content)):
            if pred(content[k]['value']):
                return k
        return None

    sections = []
    c3 = json.load(open(f'{OUT_DIR}/3.json', encoding='utf-8'))['content']
    k = 0
    while True:
        k = find_idx(c3, lambda v: re.fullmatch(r'《[^》]+》', v.strip()), k)
        if k is None:
            break
        book = c3[k]['value'].strip()
        nxt = c3[k + 1]['value'].strip() if k + 1 < len(c3) else ''
        if re.fullmatch(r'[^《》]{0,16}（\d{4}）|序', nxt):
            stitle = book + clean_spaces(nxt)
        elif nxt.startswith('【'):
            stitle = book + '（題解）'
        else:
            stitle = book
        sections.append((3, k, stitle))
        k += 1
    c4 = json.load(open(f'{OUT_DIR}/4.json', encoding='utf-8'))['content']
    star = find_idx(c4, lambda v: bool(re.fullmatch(r'※[\s※]*', v.strip())))
    if star is not None:
        sections.append((4, 1, '《自覺中的直觀與反省》第40節'))
        sections.append((4, star + 1, '《自覺中的直觀與反省》第41節'))
    for ci in (6, 7):
        cc = json.load(open(f'{OUT_DIR}/{ci}.json', encoding='utf-8'))['content']
        k = 0
        while True:
            k = find_idx(cc, lambda v: bool(re.fullmatch(r'第[一二三四五六七八九十]+章', v.strip())), k)
            if k is None:
                break
            sections.append((ci, k, cc[k]['value'].strip()))
            k += 1

    for ci, sec, stitle in sections:
        meta_toc.append(dict(type='section', title=stitle, index=ci, sec=sec, level=2))

    meta = dict(
        bookId='9d28b41627ec',
        title='西田几多郎哲学选辑Ⅰ',
        author='西田几多郎',
        region='东方',
        chapterCount=len(results),
        chapterTitles=chapter_titles,
        toc=meta_toc,
    )
    with open(f'{OUT_DIR}/meta.json', 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)

    for i, (title, paras) in enumerate(results):
        chars = sum(len(p['text']) for p in paras)
        print(f'ch{i} {title}: {len(paras)} blocks, {chars} chars')
    print('sections:', len(sections))
    for ci, sec, st in sections:
        print(f'  sec ch{ci}#{sec} {st}')
    print('dropped apparatus:', dict(dropped))
    print('total kept chars:', sum(len(p['text']) for _, ps in results for p in ps))


if __name__ == '__main__':
    main()
