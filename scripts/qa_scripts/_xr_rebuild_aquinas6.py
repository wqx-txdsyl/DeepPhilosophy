# -*- coding: utf-8 -*-
"""神学大全第一集第6卷重建 v2：OCR 原始页 → 28 章（问题75-102 论人）
- 页 0-8（封面/版权/版本/目录/扉页）丢弃；正文从页 9 开始
- 清洗：偶页页眉(^\d{1,4}第6卷论人) / 奇页页眉(^问题\d+论…\d$) / 栏标(^\d{3,4}[a-z]?$)
- 问题起始页：清洗后首行 '问题N' 独立行 且 页内含 （共X条）
"""
import json, os, re

bid = 'f52ed83b99d9'
CK = 'f:/program/Python/PhiAgent/backend/data/dp_pdf_import_ckpt.json'
OUT = os.path.dirname(os.path.abspath(__file__))
SAFE = '西方_托马斯_阿奎那_神学大全_第一集_第6卷.pdf'

ck = json.load(open(CK, encoding='utf-8'))
pages = ck['ocr'][SAFE]

EVEN_HDR = re.compile(r'^\d{1,4}第.卷论人\s*$')  # 偶页页眉（第6卷/第5卷OCR变体，.匹配任意单字符）
ODD_HDR = re.compile(r'^问题\d+论[^\n]{0,40}\d{1,4}\s*$')  # 奇页页眉（缩略标题+页码）
MARG = re.compile(r'^\d{3,4}[a-z]?\s*$')             # 栏标 438b/439a

def clean_page(txt):
    lines = []
    for ln in txt.split('\n'):
        s = ln.strip()
        if not s:
            continue
        if EVEN_HDR.match(s) or ODD_HDR.match(s) or MARG.match(s):
            continue
        lines.append(s)
    return '\n'.join(lines)

# ── 1. 清洗全部页 ──
clean = {}
for k in sorted(pages, key=int):
    if int(k) < 9:
        continue  # 卷首/目录/扉页丢弃
    clean[int(k)] = clean_page(pages[k])

# ── 2. 定位问题起始页 ──
Q_START = re.compile(r'^问[题題]\s*(\d{1,3})\s*$')
q_pages = {}  # 问题号 -> 起始页
for k in sorted(clean):
    txt = clean[k]
    m = Q_START.match(txt.split('\n')[0] if txt else '')
    if m and '（共' in txt:
        q = int(m.group(1))
        if 75 <= q <= 102 and q not in q_pages:
            q_pages[q] = k
print('问题起始页 (%d):' % len(q_pages))
for q in sorted(q_pages):
    print('  问题%3d @页%3d' % (q, q_pages[q]))

# ── 3. 提取标题（问题N 行 → （共X条）行）──
def extract_title(txt):
    lines = txt.split('\n')
    # 标题行 = 从 '问题N' 行之后到含 '（共X条）' 的行
    parts = []
    started = False
    for ln in lines:
        if not started:
            if Q_START.match(ln.strip()):
                started = True
            continue
        if '（共' in ln and '条）' in ln:
            break
        if MARG.match(ln.strip()):
            continue
        parts.append(ln.strip())
    t = re.sub(r'\s+', '', ''.join(parts))  # 标题内不换行不留空
    return t

titles = {}
for q, k in q_pages.items():
    titles[q] = extract_title(clean[k])
for q in sorted(titles):
    print('问题%d 标题: %s' % (q, titles[q]))

# ── 4. 切分内容 ──
order = sorted(q_pages)
q_order_pages = [(q, q_pages[q]) for q in order]
content = {}
for i, (q, k) in enumerate(q_order_pages):
    end = q_order_pages[i + 1][1] if i + 1 < len(q_order_pages) else max(clean) + 1
    parts = [clean[j] for j in range(k, end) if j in clean]
    content[q] = '\n\n'.join(parts)

# ── 5. 生成章节 + meta ──
chapters = []
chapter_titles = []
for i, q in enumerate(order):
    title = '问题%d %s' % (q, titles[q])
    text = re.sub(r'\n{3,}', '\n\n', content[q]).strip()
    chapters.append({'index': i, 'title': title,
                     'content': [{'type': 'text', 'value': text}]})
    chapter_titles.append(title)
    print('章%d 问题%d: %d 字' % (i, q, len(text)))

outdir = os.path.join(OUT, '_xr_out_aquinas6')
os.makedirs(outdir, exist_ok=True)
for i, ch in enumerate(chapters):
    json.dump(ch, open(os.path.join(outdir, '%d.json' % i), 'w', encoding='utf-8'), ensure_ascii=False)
toc = [{'type': 'chapter', 'title': t, 'index': i, 'level': 1}
       for i, t in enumerate(chapter_titles)]
meta = {'bookId': bid, 'title': '神学大全　第一集　第6卷',
        'author': '托马斯·阿奎那', 'toc': toc, 'cover': '/covers/%s_cover.webp' % bid,
        'chapterCount': len(chapters), 'chapterTitles': chapter_titles}
json.dump(meta, open(os.path.join(outdir, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print('输出 %d 章 + meta → %s' % (len(chapters), outdir))
