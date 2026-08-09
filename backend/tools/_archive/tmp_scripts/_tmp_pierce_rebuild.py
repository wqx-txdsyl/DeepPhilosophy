# -*- coding: utf-8 -*-
"""皮尔斯文选章节重建: 目录28篇+2附录 → 30章
定位: 页首4行模糊匹配(全角标点归一) + 书内页码偏移(+13)双验证; 未命中用推算位置(人工验证过)
页眉清洗: 奇数页"皮尔斯文选"单行 / 偶数页"第一部分XXX"+部分名两行 / 页码行 → 删
用法: --apply 写回双端 (默认 dry-run 打印每章统计)
"""
import json, re, sys, os, shutil

CK = r'F:\program\Python\DeepPhilosophy\DeepPhilosophy\backend\data\dp_pdf_import_ckpt.json'
BASE = r'F:\program\Python\DeepPhilosophy\DeepPhilosophy'
BDIR = BASE + r'\backend\data\book_chapters'
PDIR = BASE + r'\app\public\backend\data\book_chapters'
BID = '8b1e1c5ebaac'
APPLY = '--apply' in sys.argv

ck = json.load(open(CK, encoding='utf-8'))
ocr = ck['ocr']['西方_查尔斯_桑德斯_皮尔士_皮尔斯文选.pdf']

# (标题, 书内页码) — 目录原文
ITEMS = [
    ('什么是实用主义？', 3),
    ('实效主义的一些论点', 22),
    ('实用主义回顾：最后一次表述', 41),
    ('信念的确定', 67),
    ('如何使我们的观念清楚明白', 86),
    ('与人据说具有的某些能力相关的几个问题', 105),
    ('对4种能力的否定所产生的某些后果', 125),
    ('精神的法则', 150),
    ('现象学原理', 167),
    ('对形而上学的看法', 192),
    ('论形而上学', 197),
    ('论新范畴表', 204),
    ('第三性的实在', 214),
    ('数学的本质', 219),
    ('数学的本性', 231),
    ('审视必然性学说', 240),
    ('不明推论式与归纳式', 254),
    ('推理的有效性的标准', 261),
    ('一、二、三：思维与自然界的基本范畴', 271),
    ('作为指号学的逻辑：指号论', 276),
    ('论指号的本性', 299),
    ('指号', 301),
    ('理论结构', 305),
    ('科学态度和可错论', 314),
    ('哲学和科学：一种分类', 333),
    ('宗教与科学的联姻', 349),
    ('上帝概念', 352),
    ('什么是基督教信仰？', 356),
    ('《皮尔斯文集》目录（英文版八卷本）', 363),
    ('皮尔斯年表', 398),
]
OFFSET = 13  # PDF页 = 书内页码 + 13 (23个命中全部一致)


def norm(s):
    return re.sub(r'[\s·．.\-—,，、（）()？?:：;；·"“”‘’]', '', s)


def head_lines(v, n=4):
    return [l.strip() for l in v.split('\n') if l.strip()][:n]


def locate(title, book_pg):
    """页首匹配 + 偏移验证; 返回 PDF 页号 (找不到返回 -1)
    短 key(<4字, 如『指号』)要求行首匹配, 防止行内含字误命中(如"描述一下指号的特征")"""
    key = norm(title)[:6]
    expect = book_pg + OFFSET
    for pg in sorted(ocr, key=lambda x: int(x)):
        p = int(pg)
        v = ocr[pg]
        if not v or len(v) < 5:
            continue
        # 页首 4 行匹配
        if len(key) < 4:
            hit = any(norm(hl).startswith(key) for hl in head_lines(v))
        else:
            hit = any(key in norm(hl) for hl in head_lines(v))
        if hit and abs(p - expect) <= 2:
            return p
    return -1


# 1. 定位 (miss 用推算位置)
starts = []
miss = []
for i, (t, bp) in enumerate(ITEMS):
    pg = locate(t, bp)
    if pg < 0:
        pg = bp + OFFSET  # 推算位置(已人工验证 284/346/376/411)
        miss.append((i, t, bp, pg))
    starts.append((i, t, pg))
starts.sort(key=lambda x: x[2])

print('== 章节起始页 ==')
for i, t, pg in starts:
    print('%2d [PDF %3d] %s' % (i, pg, t))
if miss:
    print('推算位置(页首未匹配, 人工验证过):', [(i, t) for i, t, _, _ in miss])

# 2. 页眉清洗
def clean_page(v):
    lines = v.split('\n')
    out = []
    for ln in lines:
        s = ln.strip()
        if not s:
            out.append('')
            continue
        if re.match(r'^\d{1,4}(\.\d)?$', s):   # 页码行
            continue
        if s == '皮尔斯文选' or s == '皮尔土文选' or s == '皮尔土文迹':  # 书名页眉
            continue
        if re.match(r'^(第[一二三四五]部分)(.+)?$', s) and len(s) <= 14:  # 部分名页眉
            continue
        out.append(ln)
    return '\n'.join(out)

# 3. 切章: 每页一个 text block
PAGES = sorted((int(k) for k in ocr if isinstance(ocr[k], str) and len(ocr[k]) > 5))
failed = [int(k) for k in ocr if ocr[k] == '__FAILED__']


def chapter_blocks(pg_from, pg_to):
    """[pg_from, pg_to) 页 → blocks; FAILED 页跳过"""
    blocks = []
    for pg in range(pg_from, pg_to):
        v = ocr.get(str(pg), '')
        if not v or v == '__FAILED__' or len(v) < 5:
            continue
        cv = clean_page(v)
        if cv.strip():
            blocks.append({'type': 'text', 'value': cv})
    return blocks


chapters = []
for i, (idx, t, pg) in enumerate(starts):
    pg_to = starts[i + 1][2] if i + 1 < len(starts) else max(PAGES) + 1
    blocks = chapter_blocks(pg, pg_to)
    chapters.append({'index': idx, 'title': t, 'content': blocks, 'from': pg, 'to': pg_to - 1})

print()
print('== 章节统计 ==')
total_chars = 0
for c in chapters:
    n = sum(len(b['value']) for b in c['content'])
    total_chars += n
    print('%2d %-28s 页[%3d-%3d] %2d块 %6d字' % (c['index'], c['title'][:26], c['from'], c['to'], len(c['content']), n))
print('总计: %d 章, %d 块, %d 字 | FAILED页: %s' % (len(chapters), sum(len(c['content']) for c in chapters), total_chars, failed))

if APPLY:
    D = os.path.join(BDIR, BID)
    if os.path.exists(D):
        shutil.rmtree(D)
    os.makedirs(D)
    toc = []
    for c in chapters:
        ch = {'index': c['index'], 'title': c['title'], 'content': c['content']}
        json.dump(ch, open(os.path.join(D, '%d.json' % c['index']), 'w', encoding='utf-8'), ensure_ascii=False)
        toc.append(c['title'])
    meta = {'bookId': BID, 'title': '皮尔斯文选', 'author': '查尔斯·桑德斯·皮尔士', 'toc': toc,
            'cover': None, 'chapterCount': len(toc), 'chapterTitles': toc}
    json.dump(meta, open(os.path.join(D, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    PD = os.path.join(PDIR, BID)
    if os.path.exists(PD):
        shutil.rmtree(PD)
    shutil.copytree(D, PD)
    print('已写回双端: backend + public')
