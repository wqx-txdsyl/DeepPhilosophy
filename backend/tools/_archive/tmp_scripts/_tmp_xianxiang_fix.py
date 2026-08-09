# -*- coding: utf-8 -*-
"""现象学的观念 章节重建 (2026-08-10):
- 前置区(总序+编者引论 p4-p13) 重新 OCR + 行级页眉清洗
- 正文 12 章: 讲座的思路/第一讲~第五讲/附录/文章的考证性补充/人名索引/第一版译者引言/第二版译者后记
- 非章首段段首剥页眉+页码 (OCR running-head 粘合)
- 双端写回 meta/detail + books.json
"""
import sys, io, os, json, re, time, shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dp_pdf_import as imp

BID = 'e2a4c4f78c40'
BASE = r'F:\program\Python\DeepPhilosophy\DeepPhilosophy'
BD = os.path.join(BASE, 'backend/data/book_chapters', BID)
FP = r'F:\philosophy\西方\埃德蒙德·胡塞尔\现象学的观念.pdf'

# ── 1. 前置区: OCR p4-p13 (总序+编者引论), 行级清洗, 每页 1 段 ──
def ocr_front_pages():
    import fitz
    doc = fitz.open(FP)
    front_paras = []
    for i in range(4, 14):
        pix = doc[i].get_pixmap(matrix=fitz.Matrix(1.2, 1.2))
        img = os.path.join(os.environ['TEMP'], 'front_%04d.png' % i)
        pix.save(img)
        text = imp.ocr_page(img)
        os.remove(img)
        # 行级清洗: 页眉行/孤立页码行剥除
        rows = []
        for ln in text.split('\n'):
            s = ln.strip()
            if not s:
                continue
            if re.match(r'^(?:《胡塞尔文集》总序|编者引论|现象学的观念|讲座的思路|X[IVX1]+|iv)$', s):
                continue
            if re.match(r'^[IVXLCivxlc\d]{1,5}$', s):
                continue
            rows.append(s)
        para = imp.merge_lines('\n'.join(rows))
        if para.strip():
            front_paras.append(para.strip())
        print('  p%02d -> %d 行 %d 字' % (i, len(rows), len(para)), flush=True)
    doc.close()
    return front_paras

# ── 2. 正文: 已有章节文件拼接 (页序已确认连续正确) ──
flow = []
for fn in sorted(os.listdir(BD), key=lambda f: int(f.split('.')[0]) if f.split('.')[0].isdigit() else 9999):
    if fn == 'meta.json' or not fn.endswith('.json'):
        continue
    ch = json.load(open(os.path.join(BD, fn), encoding='utf-8'))
    for b in ch['content']:
        flow.append(b['value'])
body = '\n\n'.join(flow)

# 丢弃前置区残留 (目录尾+书名页): 从 '讲座的思路' 正文起
start = body.index('讲座的思路生活和科学中的自然的思维')
body = body[start:]

# 切点 (marker 唯一性已验证)
CUTS = [
    ('讲座的思路生活和科学中的自然的思维', '讲座的思路'),
    ('第一讲', '第一讲 自然的思维态度与科学'),
    ('第二讲', '第二讲 认识批判的开端：对所有知识的质疑'),
    ('第三讲', '第三讲 认识论还原的实行：排除一切超越之物'),
    ('第四讲', '第四讲 通过意向性扩展研究范围'),
    ('第五讲', '第五讲 时间意识的构造'),
    ('在认识中自然是被给予的', '附录'),
    ('文章的考证性补充', '文章的考证性补充'),
    ('人名索引', '人名索引'),
    ('第一版译者引言', '第一版译者引言'),
    ('第二版译者后记', '第二版译者后记'),
]

# ── 3. 段首清洗 ──
HDR_RE = re.compile(
    r'^(?:\d{0,3}(现象学的观念|讲座的思路|第一讲|第二讲|第三讲|第四讲|第五讲|'
    r'附录[一二三四五六七八九十\d]*|文章的考证性补充|关于文章的构成|关于文章的考证性注释|'
    r'人名索引|第一版译者引言|第一版译著引言|第二版译者后记)\d{0,3}\s*)')
PAGE_RE = re.compile(r'^\d{1,3}\s+(?=[\u4e00-\u9fff])')
COPYRIGHT_RE = re.compile(r'^(?:http|www\.|\u5b9a\u4ef7[:\uff1a])')   # \u7248\u6743\u9875\u6bb5

def strip_para(p, first, title):
    if not first or title == '讲座的思路':
        p = HDR_RE.sub('', p, count=1)
    p = p.lstrip()
    p = PAGE_RE.sub('', p, count=1)      # '79 在认识中...' -> '在认识中...'
    return p

# ── 4. 切章 ──
paras = body.split('\n\n')
paras = [p.strip() for p in paras if p.strip()]

pos = []
idx = 0
for marker, title in CUTS:
    while idx < len(paras) and marker not in paras[idx]:
        idx += 1
    pos.append((idx, marker, title))
    if idx >= len(paras):
        print('切点未命中: %r (共 %d 段)' % (marker, len(paras)), flush=True)
        for k, pp in enumerate(paras[-6:]):
            print('  尾段[%d]: %s' % (len(paras)-6+k, pp[:40].replace('\n','|')), flush=True)
    idx += 1
# 确认全部命中
assert all(p < len(paras) for p, _, _ in pos), '切点未全部命中: %s' % pos

chapters = []
for i, (p, marker, title) in enumerate(pos):
    end = pos[i + 1][0] if i + 1 < len(pos) else len(paras)
    seg = [strip_para(paras[j], first=(j == p), title=title) for j in range(p, end)]
    seg = [s for s in seg if s and not COPYRIGHT_RE.match(s)]
    chapters.append({'title': title, 'paras': seg})

# 前置章
front = ocr_front_pages()
chapters.insert(0, {'title': '编者引论与总序', 'paras': front})

for c in chapters:
    n = len(c['paras'])
    print('%s: %d 段' % (c['title'], n), flush=True)
    print('  首段:', json.dumps(c['paras'][0][:46], ensure_ascii=False), flush=True)
    print('  尾段:', json.dumps(c['paras'][-1][:46], ensure_ascii=False), flush=True)

# ── 5. 写盘 (双端) ──
toc_titles = [c['title'] for c in chapters]
toc_obj = [{'type': 'chapter', 'title': t, 'index': i} for i, t in enumerate(toc_titles)]
blocks_chs = [{'title': c['title'], 'content': [{'type': 'text', 'value': p} for p in c['paras']], 'index': i}
              for i, c in enumerate(chapters)]
meta = {'bookId': BID, 'title': '现象学的观念', 'author': '埃德蒙德·胡塞尔', 'toc': toc_obj,
        'cover': None, 'chapterCount': len(chapters), 'chapterTitles': toc_titles}
# 保留现有 cover
old_meta_fp = os.path.join(BD, 'meta.json')
if os.path.exists(old_meta_fp):
    old = json.load(open(old_meta_fp, encoding='utf-8'))
    meta['cover'] = old.get('cover')

for pre in (os.path.join(BASE, 'backend/data/book_chapters'),
            os.path.join(BASE, 'app/public/backend/data/book_chapters')):
    bd = os.path.join(pre, BID)
    if os.path.exists(bd):
        shutil.rmtree(bd)
    os.makedirs(bd, exist_ok=True)
    for ch in blocks_chs:
        json.dump(ch, open(os.path.join(bd, '%d.json' % ch['index']), 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump(meta, open(os.path.join(bd, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print('章节文件双端写回: %d 章' % len(chapters), flush=True)

# detail 双端 (保留 summary/tags)
for pre in (os.path.join(BASE, 'backend/data/book_detail'),
            os.path.join(BASE, 'app/public/book_detail')):
    dfp = os.path.join(pre, BID + '.json')
    d = json.load(open(dfp, encoding='utf-8')) if os.path.exists(dfp) else {}
    d.update({k: meta[k] for k in ['bookId', 'title', 'author', 'toc', 'chapterCount', 'chapterTitles']})
    d['cover'] = d.get('cover') or meta.get('cover')
    d.setdefault('region', '西方'); d.setdefault('file_type', 'pdf'); d.setdefault('extract', 'ocr-fixed')
    json.dump(d, open(dfp, 'w', encoding='utf-8'), ensure_ascii=False)
print('detail 双端写回', flush=True)

# books.json
bjf = os.path.join(BASE, 'app/public/books.json')
bj = json.load(open(bjf, encoding='utf-8'))
items = bj if isinstance(bj, list) else bj.get('books', [])
for it in items:
    if it.get('id') == BID:
        it['chapterCount'] = len(chapters)
        break
json.dump(bj, open(bjf, 'w', encoding='utf-8'), ensure_ascii=False)
print('books.json 更新', flush=True)

# 统计
lens = sorted(len(p) for c in chapters for p in c['paras'])
print('\n总段数: %d, 段长中位: %d' % (len(lens), lens[len(lens) // 2]), flush=True)
longs = [p for c in chapters for p in c['paras'] if len(p) > 2000]
print('超长段(>2000字): %d 个' % len(longs), flush=True)
