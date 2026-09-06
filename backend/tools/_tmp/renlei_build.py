# -*- coding: utf-8 -*-
"""人类理解论 (44a32441dabe) 构建: OCR → 四卷, 页眉章号重建章界, 按分章标准注入。"""
import re, os, json, shutil

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mia_batch', 'renlei_ocr.txt')
BID = '44a32441dabe'

t = open(SRC, encoding='utf-8').read()
L = t.split('\n')
n = len(L)

CN = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10,
      '十一': 11, '十二': 12, '十三': 13, '十四': 14, '十五': 15, '十六': 16, '十七': 17, '十八': 18,
      '十九': 19, '二十': 20, '二十一': 21, '二十二': 22, '二十三': 23, '二十四': 24, '二十五': 25,
      '二十六': 26, '二十七': 27, '二十八': 28, '二十九': 29, '三十': 30, '三十一': 31, '三十二': 32,
      '三十三': 33, '三十四': 34}
def cn2num(s):
    s = s.strip()
    return CN.get(s, None)

HEAD = re.compile(r'^第([一二三四五六七八九十]+)章')
VOL = re.compile(r'^第([一二三四])卷')

# 卷边界(实测): 前部0-895(标题+前言+目录, 弃), 卷一896, 卷二2876, 卷三12335, 卷四16265-末
VOLS = [('第一卷', 896, 2876), ('第二卷', 2876, 12335), ('第三卷', 12335, 16265), ('第四卷', 16265, len(L))]

chapters, toc, chapter_titles = [], [], []

# 前置: 序言(致读者) — L85-630 之间找 "致读者" 或译者前言; 实测 L42-630 为出版说明/译者前言/序, 简化: 取 L42-634 为 '前言与目录' 拆分太碎, 直接丢弃目录区 L630-896
# 前置章: 从 L42 到目录开始前(~L630)
pre_lines = L[42:630]
pre_paras, cur = [], []
for l in pre_lines:
    s = l.strip()
    if not s:
        if cur: pre_paras.append(''.join(cur)); cur = []
        continue
    cur.append(s.strip())
if cur: pre_paras.append(''.join(cur))
# 滤掉目录行(带页码点)
pre_paras = [p for p in pre_paras if not re.search(r'[·.]\s*[·.\s]*\d+\s*$', p) and len(p) > 3]
blocks = [{'type': 'text', 'value': p} for p in pre_paras]
chapters.append({'index': 0, 'title': '出版说明·译者前言·序言', 'content': blocks})
chapter_titles.append('出版说明·译者前言·序言')
toc.append({'type': 'chapter', 'title': '出版说明·译者前言·序言', 'index': 0})
print(f'前置: {len(pre_paras)}段 {sum(len(p) for p in pre_paras)}字')

for vname, va, vb in VOLS:
    # 收集页眉行 (章号, 标题文本, 位置)
    heads = []
    for i in range(va, vb):
        s = L[i].strip()
        m = HEAD.match(s)
        if m and len(s) < 50:
            num = cn2num(m.group(1))
            if num is None: continue
            heads.append((num, s, i))
    if not heads:
        print(f'!! {vname} 无页眉'); continue
    # 重建章界: 遍历页眉, 章号应从1递增; 相同章号重复=页眉重复; 章号跳跃向上=新章
    segments = []  # (章号, 起位置)
    for num, s, i in heads:
        if segments and num <= segments[-1][0]:
            continue  # 页眉重复或乱序回退, 忽略
        segments.append((num, i))
    # 章标题: 用每组(相同章号连续区)的最长页眉文本
    chs_meta = []
    for k, (num, start) in enumerate(segments):
        end = segments[k + 1][1] if k + 1 < len(segments) else vb
        # 取该区间的最长页眉文本作标题
        cands = [s for (num2, s, i) in heads if num2 == num]
        title = max(cands, key=len) if cands else f'第{num}章'
        chs_meta.append((num, title, start, end))
    for k, (num, title, a2, b2) in enumerate(chs_meta):
        paras, cur = [], []
        for i in range(a2, min(b2, n)):
            s = L[i].strip()
            if HEAD.match(s) and len(s) < 50:
                continue  # 页眉剔除
            if not s:
                if cur: paras.append(''.join(cur)); cur = []
                continue
            cur.append(s)
        if cur: paras.append(''.join(cur))
        paras = [p for p in paras if len(p) >= 2]
        if not paras:
            continue
        t_clean = re.sub(r'\s+', '', title)
        t_clean = re.sub(r'^第[一二三四]+卷', '', t_clean)
        t_final = f'{vname}　{t_clean}'
        blocks = [{'type': 'text', 'value': p} for p in paras]
        ci = len(chapters)
        chapters.append({'index': ci, 'title': t_final, 'content': blocks})
        chapter_titles.append(t_final)
        if k == 0 or True:
            toc.append({'type': 'chapter', 'title': t_final, 'index': ci})
        total = sum(len(b['value']) for b in blocks)
        print(f'{t_final}: {len(blocks)}段 {total}字')

meta = {
    'bookId': BID, 'title': '人类理解论', 'author': '约翰·洛克', 'region': '西方',
    'toc': toc, 'cover': f'/covers/{BID}_cover.webp',
    'chapterCount': len(chapters), 'chapterTitles': chapter_titles,
}
src_dir = os.path.join(BASE, 'backend', 'data', 'book_chapters', BID)
if os.path.exists(src_dir):
    shutil.rmtree(src_dir)
os.makedirs(src_dir)
for ch in chapters:
    json.dump(ch, open(os.path.join(src_dir, f"{ch['index']}.json"), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump(meta, open(os.path.join(src_dir, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
mirror = os.path.join(BASE, 'app', 'public', 'backend', 'data', 'book_chapters', BID)
if os.path.exists(mirror):
    shutil.rmtree(mirror)
shutil.copytree(src_dir, mirror)
fe_detail = os.path.join(BASE, 'app', 'public', 'book_detail', f'{BID}.json')
d = json.load(open(fe_detail, encoding='utf-8'))
d['chapterCount'] = len(chapters)
d['chapterTitles'] = chapter_titles
d['toc'] = toc
d['file_type'] = 'pdf'
for p in [fe_detail, os.path.join(BASE, 'backend', 'data', 'book_detail', f'{BID}.json')]:
    json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
size = sum(len(b['value'].encode('utf-8')) for ch in chapters for b in ch['content'])
print(f'人类理解论注入完成: {len(chapters)}章 {size}B')
