# -*- coding: utf-8 -*-
"""常识（托马斯·潘恩，何实译）重建：OCR 原始页 → 12 章
- 目录锚点（书内页 = PDF页 - 5，PDF7=002 验证）：一、政权的起源和目的@001/二@015/三@031/四@059/五附记@079/
  附录@095（仅章首页，无正文不建章）/世界公民潘恩@096/潘恩与三大革命@109/北美的危机@117/自由之树@123/
  独立宣言@127/人权宣言@135 —— 全锚点 PDF 页验证通过（6,20,36,64,84,100,101,114,122,128,132,140）
- 页眉体系：偶数页=常识 COMMONSENSE（书名页眉，常带装饰—行）；奇数页=「一、章名」章名页眉；
  短文区正文页=「附录」页眉；页脚=书内页码（002/096/109/139 等独立数字行）
- 章首页（6,20,36,64,84,100）=英文原版扉页复刻+中文标题，整页丢弃；短文首页（101,114,122,128,132,140）
  页眉 COMMONSENSE/附录 + 标题行 STRIP，正文保留
- 正文中「—」独立行是「一」字 OCR 残体（当一个—人单独生存）→ 并入前一行续拼；
  页眉区「—」装饰行（邻接页眉行/页首页尾）→ 删除
- 页 0-5 封面/CIP/朱学勤评语/语录/作者简介/目录、145 广告页丢弃
- 自由之树（128-131）诗歌行式保留；其余散文 reflow；页 0-5 无正式总序不建前置章
"""
import json, os, re, shutil

bid = 'f184edd21ac7'
CK = 'f:/program/Python/PhiAgent/backend/data/dp_pdf_import_ckpt.json'
OUT = os.path.dirname(os.path.abspath(__file__))
SAFE = '西方_托马斯_潘恩_常识.pdf'

ck = json.load(open(CK, encoding='utf-8'))
pages = dict(ck['ocr'][SAFE])

CH = {
    7: '一、政权的起源和目的，兼论英国政体',
    21: '二、论君主政体和世袭制',
    37: '三、我看北美目前的形势',
    65: '四、北美目前的能力，附带谈一些杂感',
    85: '五、附记',
    101: '"世界公民"潘恩',
    114: '潘恩与三大革命',
    122: '北美的危机',
    128: '自由之树',
    132: '独立宣言',
    140: '人权宣言',
}
SKIP = {0, 1, 2, 3, 4, 5, 6, 20, 36, 64, 84, 100, 145}  # 前置页/章首页/广告页
STRIP = {
    101: ['COMMONSENSE', '“世界公民”潘恩', '"世界公民"潘恩'],
    141: ['DECLARAT', 'DESDROITSDELIGMM', 'AI'],   # 《人权宣言》全文子标题页：英文横幅残体删，中文章标题独立段
    114: ['附录', '潘恩与三大革命'],
    122: ['附录', '北美的危机'],
    128: ['附录', '自由之树'],
    132: ['附录', '独立宣言'],
    140: ['附录', '人权宣言'],
}
HEADER = {'常识', 'COMMONSENSE', 'COMMONSENSE;', 'COMMON SENSE', 'COMMON SENSE;', '附录'}
CH_HEADER = re.compile(r'^[一二三四五]、[^。！？]{1,45}$')   # 奇数页章名页眉
PAGE_NUM = re.compile(r'^\d{1,4}$')                          # 页脚书内页码（002/096/139）
FAILED = re.compile(r'^__FAILED__\s*$')
DASH = '—'

def is_hdr(s, strip):
    return (s in HEADER or CH_HEADER.match(s) or PAGE_NUM.match(s)
            or s in strip or FAILED.match(s))

def clean(txt, strip):
    lines = [ln.strip() for ln in txt.split('\n')]
    n = len(lines)
    drop = [False] * n
    for i, s in enumerate(lines):
        if not s or drop[i]:
            continue
        if is_hdr(s, strip):
            drop[i] = True
        elif s == DASH:
            # 装饰「—」：邻接（跳过已删行）页眉行/「—」行/页首/页尾 → 删；
            # 正文中（上下均正文）→ 保留（“一”字残体，reflow 时并入前一行）
            up = dn = None
            j = i - 1
            while j >= 0:
                if lines[j] and not drop[j]:
                    up = lines[j]
                    break
                j -= 1
            j = i + 1
            while j < n:
                if lines[j] and not drop[j]:
                    dn = lines[j]
                    break
                j += 1
            if (up is None or dn is None or up == DASH or dn == DASH
                    or is_hdr(up, strip) or is_hdr(dn, strip)):
                drop[i] = True
    return '\n'.join(l for l, d in zip(lines, drop) if l and not d)

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
        if s == DASH:                      # “一”字残体：并入前一行续拼
            buf += s
            continue
        if not re.search(r'[一-鿿]', s):   # 拉丁文/纯符号行独立成段
            if buf:
                out.append(buf)
                buf = ''
            out.append(s)
            continue
        if s[0] in '*△①':                  # 脚注行独立成段
            if buf:
                out.append(buf)
                buf = ''
            out.append(s)
            continue
        if re.match(r'^《[^。！？]{2,12}》全文$', s):        # 子标题页（《人权宣言》全文）独立成段
            if buf:
                out.append(buf)
                buf = ''
            out.append(s)
            continue
        if re.match(r'^[一二三四五六七八九十百]+、[^。！？]{1,25}$', s):   # 节标题独立成段
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
    if k == 128:                       # 自由之树：诗歌行式保留
        text = '\n'.join(parts)
    else:                              # 散文区：reflow
        text = reflow('\n'.join(parts))
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    chapters.append({'index': i, 'title': CH[k],
                     'content': [{'type': 'text', 'value': text}]})
    chapter_titles.append(CH[k])
    print('章%d %s: %d 字' % (i, CH[k][:25], len(text)))

outdir = os.path.join(OUT, '_xr_out_changshi')
shutil.rmtree(outdir, ignore_errors=True)
os.makedirs(outdir, exist_ok=True)
for i, ch in enumerate(chapters):
    json.dump(ch, open(os.path.join(outdir, '%d.json' % i), 'w', encoding='utf-8'), ensure_ascii=False)
toc = [{'type': 'chapter', 'title': t, 'index': i, 'level': 1}
       for i, t in enumerate(chapter_titles)]
meta = {'bookId': bid, 'title': '常识',
        'author': '托马斯·潘恩', 'toc': toc, 'cover': '/covers/%s_cover.webp' % bid,
        'chapterCount': len(chapters), 'chapterTitles': chapter_titles}
json.dump(meta, open(os.path.join(outdir, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print('输出 %d 章 + meta → %s' % (len(chapters), outdir))
