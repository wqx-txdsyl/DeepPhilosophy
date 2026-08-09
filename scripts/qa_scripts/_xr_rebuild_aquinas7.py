# -*- coding: utf-8 -*-
"""神学大全第一集第7卷重建：OCR 原始页 → 23 章（问题103-119 论上帝的管理 + 附录一~五 + 译后记）
- 页 0-8（封面/版权/版本/目录/扉页）丢弃；正文从页 9 开始
- 问题起始页：清洗后首行 '问题N' 独立行 且 页内含 （共X条）
- 附录/译后记锚点页：248/277/282/287/297/333（目录页对照）
- 清洗：偶页页眉(^\d{1,4}第.卷论上帝的管理) / 奇页页眉(^问题N论…N) / 附录页眉(^附录N…N) / 译后记页眉(^N译后记) / 栏标
"""
import json, os, re

bid = '9ed36aca09c5'
CK = 'f:/program/Python/PhiAgent/backend/data/dp_pdf_import_ckpt.json'
OUT = os.path.dirname(os.path.abspath(__file__))
SAFE = '西方_托马斯_阿奎那_神学大全_第一集_第7卷.pdf'

ck = json.load(open(CK, encoding='utf-8'))
pages = ck['ocr'][SAFE]

EVEN_HDR = re.compile(r'^\d{1,4}第.卷论上帝的管理\s*$')               # 偶页页眉
ODD_HDR = re.compile(r'^问题\d+论[^\n]{0,40}\d{1,4}\s*$')              # 奇页页眉
APP_HDR = re.compile(r'^附录[一二三四五][：:（(《\S][^\n]{0,40}\d{1,4}\s*$')  # 附录页眉（含页码）
EPI_HDR = re.compile(r'^[\d０-９]{1,4}译后记\s*$')                     # 译后记页眉（页码在前）
EPI_TTL = re.compile(r'^译后记\s*$')                                    # 译后记正文标题行
MARG = re.compile(r'^\d{3,4}[a-z]?\s*$')                                # 栏标 438b/439a
Q = re.compile(r'^问[题題]\s*(\d{1,3})\s*$')

# 附录/译后记锚点（目录页对照）：(起始页, 标题)
APPENDS = [(248, '附录一：《永恒之父通谕》'), (277, '附录二：第一集及其各卷结构图'),
           (282, '附录三：人名对照表'), (287, '附录四：著作名对照表'),
           (297, '附录五：主要术语对照表'), (333, '译后记')]

def clean_page(txt):
    lines = []
    for ln in txt.split('\n'):
        s = ln.strip()
        if not s:
            continue
        if EVEN_HDR.match(s) or ODD_HDR.match(s) or APP_HDR.match(s) \
                or EPI_HDR.match(s) or MARG.match(s):
            continue
        lines.append(s)
    return '\n'.join(lines)

# ── 1. 清洗全部页 ──
clean = {}
for k in sorted(pages, key=int):
    if int(k) < 9:
        continue
    clean[int(k)] = clean_page(pages[k])

# ── 2. 问题起始页 ──
q_pages = {}
for k in sorted(clean):
    txt = clean[k]
    lines = txt.split('\n')
    m = Q.match(lines[0] if lines else '')
    if m and '（共' in txt:
        q = int(m.group(1))
        if 103 <= q <= 119 and q not in q_pages:
            q_pages[q] = k
print('问题起始页 (%d):' % len(q_pages))
for q in sorted(q_pages):
    print('  问题%3d @页%3d' % (q, q_pages[q]))

# ── 3. 切分点（问题 + 附录/译后记）──
bounds = [(q, k) for q, k in sorted(q_pages.items(), key=lambda x: x[1])]
bounds += [(None, k) for k, t in APPENDS]
bounds.sort(key=lambda x: x[1])
# 去重（附录锚点可能撞问题页——不会，问题都 < 248）
all_pages = max(clean) + 1

# ── 4. 标题 ──
def extract_q_title(txt):
    lines = txt.split('\n')
    parts, started = [], False
    for ln in lines:
        if not started:
            if Q.match(ln.strip()):
                started = True
            continue
        if '（共' in ln and '条）' in ln:
            break
        if MARG.match(ln.strip()):
            continue
        parts.append(ln.strip())
    return re.sub(r'\s+', '', ''.join(parts))

titles = {}
for q, k in bounds:
    if q is not None:
        titles[k] = ('问题%d %s' % (q, extract_q_title(clean[k])))
    else:
        titles[k] = dict(APPENDS)[k]
for k, t in sorted(titles.items()):
    print('页%3d: %s' % (k, t))

# ── 5. 切分内容 ──
order = [k for _, k in bounds]
content = {}
for i, k in enumerate(order):
    end = order[i + 1] if i + 1 < len(order) else all_pages
    parts = [clean[j] for j in range(k, end) if j in clean]
    content[k] = '\n\n'.join(parts)

# ── 6. 生成章节 + meta ──
chapters, chapter_titles = [], []
for i, k in enumerate(order):
    title = titles[k]
    text = re.sub(r'\n{3,}', '\n\n', content[k]).strip()
    chapters.append({'index': i, 'title': title,
                     'content': [{'type': 'text', 'value': text}]})
    chapter_titles.append(title)
    print('章%d [%s]: %d 字' % (i, title[:30], len(text)))

outdir = os.path.join(OUT, '_xr_out_aquinas7')
os.makedirs(outdir, exist_ok=True)
for i, ch in enumerate(chapters):
    json.dump(ch, open(os.path.join(outdir, '%d.json' % i), 'w', encoding='utf-8'), ensure_ascii=False)
toc = [{'type': 'chapter', 'title': t, 'index': i, 'level': 1}
       for i, t in enumerate(chapter_titles)]
meta = {'bookId': bid, 'title': '神学大全　第一集　第7卷',
        'author': '托马斯·阿奎那', 'toc': toc, 'cover': '/covers/%s_cover.webp' % bid,
        'chapterCount': len(chapters), 'chapterTitles': chapter_titles}
json.dump(meta, open(os.path.join(outdir, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print('输出 %d 章 + meta → %s' % (len(chapters), outdir))
