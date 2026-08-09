# -*- coding: utf-8 -*-
"""图斯库兰论辩集 文本层重建 (2026-08-09):
- 5 正文章: 页眉章名/书名/页码/孤立脚注标记清洗 + 行拼接 + 句号段界段落重建
- 前置章 '中文译者序与内容简介': 删封面版权(L0-50) + 目录区(L956-985), 其余保留
- 双端写回 meta/detail + books.json chapterCount
"""
import sys, io, os, json, re

# 不包装 stdout (dp_pdf_import 已包装, 双重包装会 I/O closed)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dp_pdf_import as imp

FP = r'F:/philosophy/西方/西塞罗/图斯库兰论辩集.pdf'
BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy'
bid = '4be7b72cf01d'

text = imp.extract_text_layer(FP)
lines = text.split('\n')

# 切点 (已验证): L0985/3217/4444/6085/7525
CUTS = [
    (985, '第一章 论鄙视死亡'),
    (3217, '第二章 论忍受痛苦'),
    (4444, '第三章 论减轻悲伤'),
    (6085, '第四章 论灵魂持久的纷扰'),
    (7525, '第五章 论德性对于幸福生活是自足的'),
]

NOTE_RE = re.compile(r'^[①②③④⑤⑥⑦⑧⑨⑩]+$')      # 孤立脚注标记
PAGE_RE = re.compile(r'^\d{1,3}$')                    # 页码
DOTS_RE = re.compile(r'^…+$')                         # 省略号行
CIP_RE = re.compile(r'^\(\s*[\d\s]+\)\s*$')           # 目录页码 ( 1 )

def para_end(s):
    """段落边界: 剥行尾脚注标记/闭合引号后, 行尾是句号类标点"""
    s = s.strip()
    while s and (s[-1] in '①②③④⑤⑥⑦⑧⑨⑩' or s[-1] in '\u201d\u300d\u300f)）】' or s[-1] in ',，'):
        s = s[:-1]
    return bool(s) and s[-1] in '。？！…'

def build_paras(rows):
    """行拼接 + 段落重建"""
    paras, cur = [], []
    for ln in rows:
        cur.append(ln)
        if para_end(ln):
            paras.append(''.join(cur))
            cur = []
    if cur:
        paras.append(''.join(cur))
    return [p.strip() for p in paras if p.strip()]

def clean_body(rows, title):
    """正文清洗: 删页眉章名/书名/页码/孤立脚注标记"""
    out = []
    for ln in rows:
        s = ln.strip()
        if not s:
            continue
        if s == title:          # 页眉章名
            continue
        if s == '图斯库兰论辩集':  # 章首页页眉书名
            continue
        if PAGE_RE.match(s) or NOTE_RE.match(s) or DOTS_RE.match(s):
            continue
        out.append(ln)
    return out

def clean_preface(rows):
    """前置区清洗: 删目录条目(标题+页码+省略号三行组), 其余保留"""
    out = []
    n = len(rows)
    for i, ln in enumerate(rows):
        s = ln.strip()
        if not s:
            continue
        if s in ('目 录', '目  录'):
            continue
        nxt = rows[i + 1].strip() if i + 1 < n else ''
        nxt2 = rows[i + 2].strip() if i + 2 < n else ''
        # 目录条目: '第X章' + 页码行 + 省略号行
        if re.match(r'^第[一二三四五六七八九十]+章', s) and (CIP_RE.match(nxt) or DOTS_RE.match(nxt)):
            continue
        if CIP_RE.match(s) or DOTS_RE.match(s):
            continue
        if s in ('图斯库兰论辩集',):
            continue
        out.append(ln)
    return out

def to_blocks(paras):
    return [{"type": "text", "value": p} for p in paras]

# ── 1. 前置章: L51(中文译者序) .. L984 ──
pre_rows = [ln for ln in lines[51:985] if ln.strip()]
pre_clean = clean_preface(pre_rows)
pre_paras = build_paras(pre_clean)
print('前置章: %d 行 -> %d 段' % (len(pre_clean), len(pre_paras)))
print('  前 3 段:', json.dumps(pre_paras[:3], ensure_ascii=False)[:180])

# ── 2. 正文 5 章 ──
chapters = [{'title': '中文译者序与内容简介', 'paras': pre_paras}]
for i, (cut, title) in enumerate(CUTS):
    end = CUTS[i + 1][0] if i + 1 < len(CUTS) else len(lines)
    rows = lines[cut + 1:end]
    clean = clean_body(rows, title)
    paras = build_paras(clean)
    chapters.append({'title': title, 'paras': paras})
    print('%s: %d 行 -> %d 段 (%d 字)' % (title, len(clean), len(paras), sum(len(p) for p in paras)))
    print('  首段:', json.dumps(paras[0][:80] if paras else '', ensure_ascii=False))
    print('  尾段:', json.dumps(paras[-1][:80] if paras else '', ensure_ascii=False))

# ── 3. 写盘 (双端) ──
toc_titles = [c['title'] for c in chapters]
toc_obj = [{'type': 'chapter', 'title': t, 'index': i} for i, t in enumerate(toc_titles)]
blocks_chs = [{'title': c['title'], 'content': to_blocks(c['paras']), 'index': i}
              for i, c in enumerate(chapters)]
meta = {'bookId': bid, 'title': '图斯库兰论辩集', 'author': '西塞罗', 'toc': toc_obj,
        'cover': None, 'chapterCount': len(chapters), 'chapterTitles': toc_titles}

for pre in (os.path.join(BASE, 'backend/data/book_chapters'),
            os.path.join(BASE, 'app/public/backend/data/book_chapters')):
    bd = os.path.join(pre, bid)
    if os.path.exists(bd):
        import shutil; shutil.rmtree(bd)
    os.makedirs(bd, exist_ok=True)
    for ch in blocks_chs:
        json.dump(ch, open(os.path.join(bd, '%d.json' % ch['index']), 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump(meta, open(os.path.join(bd, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print('章节文件双端写回: %d 章' % len(chapters))

# detail 双端 (保留 summary/tags)
for pre in (os.path.join(BASE, 'backend/data/book_detail'),
            os.path.join(BASE, 'app/public/book_detail')):
    dfp = os.path.join(pre, bid + '.json')
    d = json.load(open(dfp, encoding='utf-8')) if os.path.exists(dfp) else {}
    d.update({k: meta[k] for k in ['bookId', 'title', 'author', 'toc', 'chapterCount', 'chapterTitles']})
    d['cover'] = d.get('cover') or meta.get('cover')
    d.setdefault('region', '西方'); d.setdefault('file_type', 'pdf'); d.setdefault('extract', 'text-layer-fixed')
    json.dump(d, open(dfp, 'w', encoding='utf-8'), ensure_ascii=False)
print('detail 双端写回')

# books.json
bjf = os.path.join(BASE, 'app/public/books.json')
bj = json.load(open(bjf, encoding='utf-8'))
items = bj if isinstance(bj, list) else bj.get('books', [])
for it in items:
    if it.get('id') == bid:
        it['chapterCount'] = len(chapters)
        break
json.dump(bj, open(bjf, 'w', encoding='utf-8'), ensure_ascii=False)
print('books.json 更新')

# 统计
import collections
lens = sorted(len(p) for c in chapters for p in c['paras'])
print('\n总段数: %d, 段长中位: %d' % (len(lens), lens[len(lens)//2]))
longs = [p for c in chapters for p in c['paras'] if len(p) > 2000]
print('超长段(>2000字): %d 个' % len(longs))
