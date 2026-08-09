# -*- coding: utf-8 -*-
"""论存在者与本质（托马斯·阿奎那，段德智译）重建：OCR 原始页 → 17 章
- 目录锚点（正文区书内页 = PDF页 - 7，全验证）：引言@1(PDF8)/第一章@4(11)/第二章@11(18)/
  第三章@24(31)/第四章@31(38)/第五章@44(51)/第六章@51(58)/结论@59(66)/附录一@60(67)/
  附录二@157(164)/附录三@160(167)/附录四@163(170)/附录五@169(176)/附录六@175(182)/
  附录七@181(188)/译后记@187(194)；出版说明区独立页码（PDF4=书内i）
- 页眉体系：偶数页=「论存在者与本质」（书名页眉）；奇数页=章名页眉（完整或截断变体）；
  页脚无页码行（OCR 未提取）；章首页=跨行大标题（首行截断+次行续）
- 页 0-3 封面/CIP/拉丁原版扉页、6-7 目录丢弃
- 附录一（67-163，97页长文）散文 reflow（内部「一、…」五节标题独立段）；
  附录二~七（164-193，对照表）行式保留；其余散文 reflow
"""
import json, os, re, shutil

bid = 'e1fabd8e802c'
CK = 'f:/program/Python/PhiAgent/backend/data/dp_pdf_import_ckpt.json'
OUT = os.path.dirname(os.path.abspath(__file__))
SAFE = '西方_托马斯_阿奎那_论存在者与本质.pdf'

ck = json.load(open(CK, encoding='utf-8'))
pages = dict(ck['ocr'][SAFE])

CH = {
    4: '出版说明',
    8: '引言',
    11: '第一章“存在者”与“本质”这两个词的普遍意义',
    18: '第二章 作为在复合实体中所发现的本质',
    31: '第三章 本质与属相、种相和种差的关系',
    38: '第四章 作为在独立实体中所发现的本质',
    51: '第五章 在不同实体中所发现的本质',
    58: '第六章 作为在偶性中所发现的本质',
    66: '结论',
    67: '附录一 西方形而上学传统中的一部经典之作——对托马斯《论存在者与本质》的一个当代解读',
    164: '附录二 人名外中文对照表',
    167: '附录三 人名中外文对照表',
    170: '附录四 著作名外中文对照表',
    176: '附录五 著作名中外文对照表',
    182: '附录六 主要术语外中文对照表',
    188: '附录七 主要术语中外文对照表',
    194: '译后记',
}
SKIP = {0, 1, 2, 3, 6, 7}   # 封面/CIP/拉丁扉页(0-3)、目录(6-7)
STRIP = {
    4: ['汉译世界学术名著丛书', '（120年纪念版·分科本）', '出版说明'],
    5: ['出版说明'],
    8: ['引言'],
    11: ['第一章“存在者”与“本质”', '这两个词的普遍意义'],
    18: ['第二章作为在复合实体中', '所发现的本质'],
    31: ['第三章 本质与属相、种相和', '种差的关系'],
    38: ['第四章作为在独立实体中', '所发现的本质'],
    51: ['第五章在不同实体中所发现的本质'],
    58: ['第六章作为在偶性中所发现的本质'],
    66: ['结论'],
    67: ['附录一', '西方形而上学传统中的一部经典之作'],
    164: ['附录二', '人名外中文对照表'],
    167: ['附录三', '人名中外文对照表'],
    170: ['附录四', '著作名外中文对照表'],
    176: ['附录五', '著作名中外文对照表'],
    182: ['附录六', '主要术语外中文对照表'],
    188: ['附录七', '主要术语中外文对照表'],
    194: ['译后记'],
}
BOOK_HDR = '论存在者与本质'                       # 偶数页书名页眉
CH_HDR = re.compile(r'^第[一二三四五六]章[^。！？]{1,30}$')     # 奇数页章名页眉（含截断）
FULU_HDR = re.compile(r'^附录[一二三四五六七][^。！？]{1,25}$')  # 附录区页眉
SIMPLE_HDR = {'引言', '结论', '译后记'}
FAILED = re.compile(r'^__FAILED__\s*$')

def clean(txt, strip):
    out = []
    for ln in txt.split('\n'):
        s = ln.strip()
        if not s or s in strip or s == BOOK_HDR or s in SIMPLE_HDR or FAILED.match(s):
            continue
        if CH_HDR.match(s) or FULU_HDR.match(s):
            continue
        out.append(s)
    return '\n'.join(out)

NUM_LINE = re.compile(r'^[一二三四五六七八九十百千\d]{1,3}\s*$')
ENTRY = re.compile(r'^（[一二三四五六七八九十百千\d]{1,3}[)）]')

def reflow(text):
    out, buf = [], ''
    for ln in text.split('\n'):
        s = ln.strip()
        if not s:
            if buf:
                out.append(buf)
                buf = ''
            continue
        if not re.search(r'[一-鿿]', s):            # 拉丁文/希腊文/纯符号行独立成段
            if buf:
                out.append(buf)
                buf = ''
            out.append(s)
            continue
        if s[0] in '*△①':                          # 脚注行独立成段
            if buf:
                out.append(buf)
                buf = ''
            out.append(s)
            continue
        if re.match(r'^[一二三四五六七八九十百]+、[^。！？]{1,25}$', s):   # 节标题（一、…）独立成段
            if buf:
                out.append(buf)
                buf = ''
            out.append(s)
            continue
        if NUM_LINE.match(s):
            if buf:
                out.append(buf)
                buf = ''
            out.append(s)
            continue
        if buf and ENTRY.match(s):
            out.append(buf)
            buf = ''
        buf = (buf + s) if buf else s
        if s[-1] in '。！？；：」』）】"':
            out.append(buf)
            buf = ''
    if buf:
        out.append(buf)
    return '\n\n'.join(out)

clean_pages = {}
for k in sorted(pages, key=int):
    k = int(k)
    if k in SKIP:
        continue
    t = clean(pages[str(k)], STRIP.get(k, []))
    if t.strip():
        clean_pages[k] = t

order = sorted(CH)
maxp = max(clean_pages) + 1
chapters, chapter_titles = [], []
for i, k in enumerate(order):
    end = order[i + 1] if i + 1 < len(order) else maxp
    parts = [clean_pages[j] for j in range(k, end) if j in clean_pages]
    if k >= 164:                   # 附录二~七：对照表行式保留
        text = '\n'.join(parts)
    else:                          # 出版说明/引言/正文/附录一/译后记：reflow
        text = reflow('\n'.join(parts))
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    chapters.append({'index': i, 'title': CH[k],
                     'content': [{'type': 'text', 'value': text}]})
    chapter_titles.append(CH[k])
    print('章%d %s: %d 字' % (i, CH[k][:25], len(text)))

outdir = os.path.join(OUT, '_xr_out_cunzai')
shutil.rmtree(outdir, ignore_errors=True)
os.makedirs(outdir, exist_ok=True)
for i, ch in enumerate(chapters):
    json.dump(ch, open(os.path.join(outdir, '%d.json' % i), 'w', encoding='utf-8'), ensure_ascii=False)
toc = [{'type': 'chapter', 'title': t, 'index': i, 'level': 1}
       for i, t in enumerate(chapter_titles)]
meta = {'bookId': bid, 'title': '论存在者与本质',
        'author': '托马斯·阿奎那', 'toc': toc, 'cover': '/covers/%s_cover.webp' % bid,
        'chapterCount': len(chapters), 'chapterTitles': chapter_titles}
json.dump(meta, open(os.path.join(outdir, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print('输出 %d 章 + meta → %s' % (len(chapters), outdir))
