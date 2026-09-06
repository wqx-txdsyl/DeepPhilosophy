# -*- coding: utf-8 -*-
"""四本 z-lib 扫描书批量构建注入: 语词和对象/狱中札记/科学革命的结构/算术基础"""
import re, os, json, shutil

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
MB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'mia_batch')

def paras_from(lines, a, b):
    paras, cur = [], []
    for i in range(a, min(b, len(lines))):
        s = lines[i].strip()
        if not s:
            if cur: paras.append(''.join(cur)); cur = []
            continue
        cur.append(s)
    if cur: paras.append(''.join(cur))
    return [p for p in paras if len(p) >= 2]

def build(bid, title, author, chapters, toc, file_type='pdf'):
    meta = {'bookId': bid, 'title': title, 'author': author, 'region': '西方',
            'toc': toc, 'cover': f'/covers/{bid}_cover.webp',
            'chapterCount': len(chapters), 'chapterTitles': [c['title'] for c in chapters]}
    src_dir = os.path.join(BASE, 'backend', 'data', 'book_chapters', bid)
    if os.path.exists(src_dir): shutil.rmtree(src_dir)
    os.makedirs(src_dir)
    for ch in chapters:
        json.dump(ch, open(os.path.join(src_dir, f"{ch['index']}.json"), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(meta, open(os.path.join(src_dir, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    mirror = os.path.join(BASE, 'app', 'public', 'backend', 'data', 'book_chapters', bid)
    if os.path.exists(mirror): shutil.rmtree(mirror)
    shutil.copytree(src_dir, mirror)
    fe_detail = os.path.join(BASE, 'app', 'public', 'book_detail', f'{bid}.json')
    d = json.load(open(fe_detail, encoding='utf-8'))
    d['chapterCount'] = len(chapters); d['chapterTitles'] = meta['chapterTitles']; d['toc'] = toc; d['file_type'] = file_type
    for p in [fe_detail, os.path.join(BASE, 'backend', 'data', 'book_detail', f'{bid}.json')]:
        json.dump(d, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    size = sum(len(b['value'].encode('utf-8')) for ch in chapters for b in ch['content'])
    for path, key in [(os.path.join(BASE, 'app', 'public', 'books.json'), None),
                      (os.path.join(BASE, 'backend', 'data', 'books_catalog.json'), 'books')]:
        data = json.load(open(path, encoding='utf-8'))
        items = data if isinstance(data, list) else data[key]
        hit = next(it for it in items if it['id'] == bid)
        hit['chapterCount'] = len(chapters); hit['file_size'] = size; hit['file_type'] = file_type
        json.dump(data, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'✅ {title} ({bid}): {len(chapters)}章 {size}B')

# ============ 1. 语词和对象 (9efee732eaff) ============
L = open(os.path.join(MB, 'yuci_ocr.txt'), encoding='utf-8').read().split('\n')
bnds = [(330, 408, '前言'), (408, 1211, '第一章　语言与真理'), (1211, 3152, '第二章　翻译和意义'),
        (3152, 4940, '第三章　指称的个体发生史'), (4940, 6305, '第四章　指称之异常多变'),
        (6305, 7648, '第五章　严格规整化'), (7648, 9235, '第六章　逃离内涵'), (9235, len(L), '第七章　本体论的判定')]
chs, toc, cts = [], [], []
for i, (a, b, t) in enumerate(bnds):
    blocks = [{'type': 'text', 'value': p} for p in paras_from(L, a, b)]
    chs.append({'index': i, 'title': t, 'content': blocks}); cts.append(t)
    toc.append({'type': 'chapter', 'title': t, 'index': i})
build('9efee732eaff', '语词和对象', '威拉德·范·奥曼·蒯因', chs, toc)

# ============ 2. 狱中札记 (464a5d944002) ============
L = open(os.path.join(MB, 'yuzhongzhaji_ocr.txt'), encoding='utf-8').read().split('\n')
bnds = [(503, 3304, '第一部分　第一章　历史文化问题'), (3304, 8000, '第二部分　第二章　政治随笔'), (8000, len(L), '第三部分　第三章　哲学研究')]
chs, toc, cts = [], [], []
for i, (a, b, t) in enumerate(bnds):
    blocks = [{'type': 'text', 'value': p} for p in paras_from(L, a, b)]
    chs.append({'index': i, 'title': t, 'content': blocks}); cts.append(t)
    toc.append({'type': 'chapter', 'title': t, 'index': i})
build('464a5d944002', '狱中札记', '安东尼奥·葛兰西', chs, toc)

# ============ 3. 科学革命的结构 (36725cea3e3c) 14章 ============
L = open(os.path.join(MB, 'kexuegeming_ocr.txt'), encoding='utf-8').read().split('\n')
CHS = [(1501, 1721, '第一章　绪论：历史的作用'), (1721, 2079, '第二章　通向常规科学之路'),
       (2079, 2414, '第三章　常规科学的本质'), (2414, 2645, '第四章　常规科学即是解谜'),
       (2645, 2881, '第五章　范式的优先性'), (2881, 3281, '第六章　反常与科学发现的突现'),
       (3281, 3601, '第七章　危机与科学理论的突现'), (3601, 4015, '第八章　对危机的反应'),
       (4015, 4514, '第九章　科学革命的本质与必然性'), (4514, 5189, '第十章　革命是世界观的改变'),
       (5189, 5394, '第十一章　革命是无形的'), (5394, 5834, '第十二章　革命的解决'),
       (5834, 6214, '第十三章　通过革命而进步'), (6214, len(L), '第十四章　后记——1969')]
chs, toc, cts = [], [], []
for i, (a, b, t) in enumerate(CHS):
    blocks = [{'type': 'text', 'value': p} for p in paras_from(L, a, b)]
    chs.append({'index': i, 'title': t, 'content': blocks}); cts.append(t)
    toc.append({'type': 'chapter', 'title': t, 'index': i})
build('36725cea3e3c', '科学革命的结构', '托马斯·库恩', chs, toc)

# ============ 4. 算术基础 (c0fc56d645dc) 按节标题分章 ============
L = open(os.path.join(MB, 'suanshu_ocr.txt'), encoding='utf-8').read().split('\n')
# 正文节标题: ^\d{1,2}． 且无页码点线
heads = [(i, l.strip()) for i, l in enumerate(L) if i > 400 and re.match(r'^\d{1,2}[．.]\s*\S', l.strip()) and len(l.strip()) < 45 and not re.search(r'[.·]{2,}', l)]
print('算术基础 节标题:', [(i, s[:24]) for i, s in heads][:20])
# 分组成 4 个大章(按书的自然结构粗分四段) + 节锚点
bounds = [400, 1446, 1829, 2650, len(L)]
part_titles = ['序与问题的提出', '一些著作家关于数概念的意见的批判', '关于单位和一的看法', '数与算术命题的性质']
chs, toc, cts = [], [], []
for pi in range(4):
    a, b = bounds[pi], bounds[pi + 1]
    paras = to_paras_local = []
    cur = ''
    for i in range(a, b):
        s = L[i].strip()
        if not s:
            if cur: to_paras_local.append(cur); cur = ''
            continue
        cur = (cur + s) if cur else s
    if cur: to_paras_local.append(cur)
    blocks = [{'type': 'text', 'value': p} for p in to_paras_local if len(p) >= 2]
    t = part_titles[pi]
    ci = len(chs)
    chs.append({'index': ci, 'title': t, 'content': blocks}); cts.append(t)
    toc.append({'type': 'chapter', 'title': t, 'index': ci})
build('c0fc56d645dc', '算术基础', '戈特洛布·弗雷格', chs, toc)
print('全部构建完成')
