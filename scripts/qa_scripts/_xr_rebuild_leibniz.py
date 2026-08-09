# -*- coding: utf-8 -*-
"""最伟大的思想家 - 莱布尼茨（[美]加勒特·汤姆森 著，李素霞 杨富斌 译）重建：OCR 原始页 → 16 章
- 目录锚点（书内页 = PDF页 - 15，页17=002 验证）：总序@PDF5、序言@PDF10、
  一千零一个困惑@16 / 新方法@32 / 逻辑学：思想的符号系统@40 / 真理和实体@50 / 物理学迷宫@68 /
  空间和时间@84 / 心灵和原因@94 / 单子@106 / 上帝@116 / 伦理学@130 / 政治学@140 /
  关于洛克@148 / 中国@160 / 参考书目@170
- 目录页码 OCR 残体（章号+页码连读）：1001=001、2017=017、3025=025、4035=035、5053=053、
  6069=069、7079=079、8091=091、9101=101、10 115=115、11 125=125、12133=133、13145=145
- 页脚规律：偶数页=页码(罗马/阿拉伯)+On Leibniz残体+莱布尼茨残体（004Oe Leibeiz |莱布尼茨）；
  奇数页=章名残体+页码（干零一个困感005）；序言区同（总序IⅢ）
- 页 0-4 封面/版权/简介、12-15 目录、169 FAILED、175 编委页丢弃
- 参考书目区(170-174)行式保留；总序/序言/正文散文区 reflow；正文小节标题独立段（目录小节名）
"""
import json, os, re, shutil

bid = '75efcbb151b7'
CK = 'f:/program/Python/PhiAgent/backend/data/dp_pdf_import_ckpt.json'
OUT = os.path.dirname(os.path.abspath(__file__))
SAFE = '西方_戈特弗里德_威廉_莱布尼茨_最伟大的思想家_-_莱布尼茨.pdf'

ck = json.load(open(CK, encoding='utf-8'))
pages = dict(ck['ocr'][SAFE])

CH = {
    5: '总序', 10: '序言',
    16: '一千零一个困惑', 32: '新方法', 40: '逻辑学：思想的符号系统',
    50: '真理和实体', 68: '物理学迷宫', 84: '空间和时间', 94: '心灵和原因',
    106: '单子', 116: '上帝', 130: '伦理学', 140: '政治学', 148: '关于洛克',
    160: '中国', 170: '参考书目',
}
ONL = ['On Leibniz', 'OnLeibniz']
STRIP = {
    5: ['总', '序'],
    10: ['序', 'Preface', '言'],
    16: ONL + ['一千零一个困惑'],
    32: ['2', '新方法'],
    40: ONL + ['号系统', '逻辑学：思想的符号系统', '逻辑学：思想的符'],   # 章名页眉 OCR 残体"号系统"
    50: ONL + ['真理和实体'],
    68: ['5', '物理学迷宫'],
    84: ONL + ['空间和时间'],
    94: ONL + ['心灵和原因'],
    106: ['8', '单子'],
    116: ONL + ['上帝'],
    130: ['10', '伦理学'],
    140: ['11', '政治学'],
    148: ['12', '关于洛克'],
    160: ['13', '中国'],
    170: ONL + ['参考书目'],
}
PAGE_FOOT = re.compile(r'^[IVXLicvxlⅠ-Ⅻ\d]{1,4}\s*O\w*\s*[A-Za-z]*\s*\|?\s*[^。！？]{0,8}\s*$')
# 偶数页页脚：页码(罗马/阿拉伯) + On残体 + 莱布尼茨残体（残体含 莱布尼&/深布尼沙/茅布尼次 等）
ODD_FOOT = re.compile(r'^[^。！？]{1,25}(?:[IVXLicvxlⅠ-Ⅻ]{1,3}|\d{2,3})\s*$')
# 奇数页页脚：章名残体+页码（页码2-3位或罗马；正文行尾4位数年份如1716不误删）
ONLINE = re.compile(r'^On\s?[A-Za-z]*\s*$')   # 章首页书名行
FAILED = re.compile(r'^__FAILED__\s*$')

# 正文小节标题（目录小节名）——独立行 → 独立段
SECTIONS = {
    '美因斯', '巴黎', '汉诺威（一）', '布伦瑞克', '汉诺威（二）',
    '通向形而上学之路', '实体',
    '组合艺术', '命题算法', '二进位制数学',
    '主谓形式', '真理的本性', '实体的同一性', '必然真理和偶然真理', '关系',
    '反驳笛卡尔', '引力和物质', '新选择', '连续体的迷宫', '结论', '附录：数学',
    '对绝对时间的反驳', '时空的非实在性',
    '机械论的范围', '实体性的点', '因果论',
    '单子', '单子和因果性', '单子是一面镜子', '共时相似性',
    '和谐', '创世', '对上帝的证明',
    '反对概念误用', '三个层次', '问题及其解决方法',
    '国家主权',
    '新论', '形而上学和神学', '灵魂', '本质主义',
    '与白晋的通信联系', '论中国自然神学', '历史背景',
}

def clean(txt, strip):
    out = []
    for ln in txt.split('\n'):
        s = ln.strip()
        if not s or s in strip or FAILED.match(s):
            continue
        if PAGE_FOOT.match(s) or ODD_FOOT.match(s) or ONLINE.match(s):
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
        if not re.search(r'[一-鿿]', s):            # 拉丁文/纯符号行独立成段
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
        if s in SECTIONS:                           # 小节标题独立成段
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
    if k <= 4 or 12 <= k <= 15 or k in (169, 175):
        continue  # 封面/版权/简介(0-4)、目录(12-15)、FAILED(169)、编委页(175)
    t = clean(pages[str(k)], STRIP.get(k, []))
    if t.strip():
        clean_pages[k] = t

order = sorted(CH)
maxp = max(clean_pages) + 1
chapters, chapter_titles = [], []
for i, k in enumerate(order):
    end = order[i + 1] if i + 1 < len(order) else maxp
    parts = [clean_pages[j] for j in range(k, end) if j in clean_pages]
    if k == 170:                       # 参考书目区：行式保留
        text = '\n'.join(parts)
    else:                              # 总序/序言/正文：reflow
        text = reflow('\n'.join(parts))
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    chapters.append({'index': i, 'title': CH[k],
                     'content': [{'type': 'text', 'value': text}]})
    chapter_titles.append(CH[k])
    print('章%d %s: %d 字' % (i, CH[k][:25], len(text)))

outdir = os.path.join(OUT, '_xr_out_leibniz')
shutil.rmtree(outdir, ignore_errors=True)
os.makedirs(outdir, exist_ok=True)
for i, ch in enumerate(chapters):
    json.dump(ch, open(os.path.join(outdir, '%d.json' % i), 'w', encoding='utf-8'), ensure_ascii=False)
toc = [{'type': 'chapter', 'title': t, 'index': i, 'level': 1}
       for i, t in enumerate(chapter_titles)]
meta = {'bookId': bid, 'title': '莱布尼茨',
        'author': '戈特弗里德·威廉·莱布尼茨', 'toc': toc, 'cover': '/covers/%s_cover.webp' % bid,
        'chapterCount': len(chapters), 'chapterTitles': chapter_titles}
json.dump(meta, open(os.path.join(outdir, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print('输出 %d 章 + meta → %s' % (len(chapters), outdir))
