# -*- coding: utf-8 -*-
"""精神现象学章节重建: 页边原书页码锚点切 8 大章
锚点: [11]序言 [68]导论 [82]意识 [137]自我意识 [178]理性 [324]精神 [495]宗教 [575]绝对知识
dry-run 打印锚点定位验证 + 各章预览; --apply 双端写回
"""
import json, os, sys, re, shutil, hashlib, io

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

BASE = r'F:/program/Python/DeepPhilosophy/DeepPhilosophy'
CKPT = os.path.join(BASE, 'backend/data/dp_pdf_import_ckpt.json')
BID = '053203b03b6c'
KEY = '西方_格奥尔格_威廉_弗里德里希_黑格尔_精神现象学.pdf'

# (锚点页码, 章标题) 按序言→绝对知识; 前 34 页(3篇导读+译者序)为第 0 章
ANCHORS = [
    (0, '导读与译者序', True),   # 页 0 起, 特殊: 到序言前
    (11, '序言', False),
    (68, '导论', False),
    (82, '第一部分 意识', False),
    (137, '第二部分 自我意识', False),
    (178, '第三部分 理性', False),
    (324, '第四部分 精神', False),
    (495, '第五部分 宗教', False),
    (575, '第六部分 绝对知识', False),
]

ckpt = json.load(open(CKPT, encoding='utf-8'))
pages = ckpt['ocr'][KEY]
n_pages = len(pages)
# 页文本(页内行), 含失败标记页
page_lines = []  # (页号, [行])
for i in range(n_pages):
    t = pages.get(str(i), '')
    lines = [l.strip() for l in t.split('\n') if l.strip()]
    page_lines.append((i, lines))

def find_anchor(no):
    """找含 [no] 的短行所在页/行; OCR 页码可能带空格 [ 178]; 返回 (页号, 行文本) 或 None"""
    pat = re.compile(r'\[\s*%d\s*\]' % no)
    hits = []
    for pgi, lines in page_lines:
        for ln in lines:
            if pat.search(ln) and len(ln) < 60:
                hits.append((pgi, ln))
    return hits[:3]

print('== 锚点定位 ==')
locs = []
for no, title, is_front in ANCHORS:
    if is_front:
        locs.append((no, title, 0, '(页0起)'))
        print('  ✓ [%d] %-20s 页0 起' % (no, title))
        continue
    hits = find_anchor(no)
    if not hits:
        print('  ✗ [%d] %s 未找到!' % (no, title))
        continue
    pgi, ln = hits[0]
    locs.append((no, title, pgi, ln))
    print('  ✓ [%d] %-20s 页%d: %s' % (no, title, pgi, ln[:40]))

# 锚点递增验证
prev = -1
ok = True
for no, title, pgi, ln in locs:
    if pgi < prev:
        print('  ✗ 锚点顺序错乱: [%d] 页%d 在 [%d] 页%d 之前' % (no, pgi, prev_anchor, prev))
        ok = False
    prev, prev_anchor = pgi, no
if not ok:
    sys.exit(1)

# 页眉/页脚清洗 (行级, 2026-08-09 正文深度检查后升级):
#   a. 书眉 "精神现象学" 精确行 → 删
#   b. OCR 变体页眉 "一/1/厂/I精神现象学" (删首字符后==精神现象学) → 删
#   c. 页脚页码独立数字行 → 删 (正文无整行纯数字)
#   d. 章名/导言区页眉 (原书每页顶部, 出现 >=3 页) → 删; 白名单外分散行 (节标题 a./b./c.,
#      "者注" 注释标记) 保留
HEADER = '精神现象学'
HEADER_VARIANTS = ['一精神现象学', '1精神现象学', '厂精神现象学', 'I精神现象学']
PAGEHEAD_NAMES = [
    # 章名页眉 (每页顶部, 原书偶数页)
    '第一章感性确定性，或“这一个”和意谓', '第二章知觉，或物与错觉',
    '第三章力与知性，现象和超感性世界', '第四章自身确定性的真理',
    '第五章理性的确定性和真理', '第六章精神', '第七章宗教', '第八章绝对知识',
    # 导言区页眉
    '序言', '导论', '译者序', '总序', '主要译名对照及索引',
    # 章首页标题行 (锚点页重复章标题, 粘正文首段)
    '第一部分 意识', '第二部分 自我意识',
    '第三部分（AA） 理性', '第三部分（BB） 精神',
    '第三部分(CC) 宗教', '第三部分(DD) 绝对知识',
]
import re as _re

def clean_line(ln):
    """返回 True = 该行是页眉/页脚/页边码残渣应删"""
    if ln == HEADER:
        return True
    if ln in HEADER_VARIANTS:
        return True
    if _re.fullmatch(r'\d{1,3}', ln):      # 页脚页码
        return True
    if _re.fullmatch(r'\[\s*\d+\s*\]', ln):  # 页边原书页码标记 (柏拉图 Stephanus 码同例, 删)
        return True
    if ln in PAGEHEAD_NAMES:               # 页眉/章首标题行
        return True
    if ln == '+++':                        # 目录页装饰分隔符 (仅页 33)
        return True
    return False

def para_end(line):
    """段落边界判断: 行尾是句号类标点 (剥闭合引号/括号后) = 原书段尾
    (原书段内断行在词间, 行尾不会放句号; 中文排版句号只在段尾)"""
    s = line.strip()
    while s and s[-1] in '”』」)）】':
        s = s[:-1]
    return bool(s) and s[-1] in '。？！…'

def build_paras(lines):
    """按行尾句号切段落: 返回 [段落文本...], 段内 \n 连接, 段间 \n\n"""
    paras, cur = [], []
    for ln in lines:
        cur.append(ln)
        if para_end(ln):
            paras.append('\n'.join(cur))
            cur = []
    if cur:
        paras.append('\n'.join(cur))
    return [p for p in paras if p.strip()]

# 章节切分: 锚点页到下一锚点页(不含); 第 0 章=页 0 到序言锚点前
# 段落重建: 跨页连续行流, 行级清洗后按行尾句号切段 (OCR 丢失段首缩进, 行尾句号是唯一可靠段界)
chapters = []
for k in range(len(locs)):
    no, title, pgi, _ = locs[k]
    end = locs[k + 1][2] if k + 1 < len(locs) else n_pages
    stream = []
    for pi in range(pgi, end):
        if pi >= 541:          # 书末 "主要译名对照及索引" 起页 (德文页码对应表, 对电子书无价值)
            break
        if 31 <= pi <= 34:     # 书前目录页 (页 31"目录"标题, 32-34 目录条目), 电子书有 toc 导航, 跳过
            continue
        t = pages.get(str(pi), '')
        if not t or t == '__FAILED__':
            continue
        for ln in t.split('\n'):
            s = ln.strip()
            if s and not clean_line(s):
                stream.append(s)
    # 章首标题行组剥离 (行级): 章首页 "第一部分"+"意识"/"第三部分"+"（AA）"+"理性" 等
    # 开头连续短行(无句号, 含"部分"或 <=4字) → 删; 正文行(长行/句号尾)即停
    i = 0
    while i < len(stream) and i < 4 and not para_end(stream[i]):
        if '部分' in stream[i] or len(stream[i]) <= 4:
            i += 1
        else:
            break
    del stream[:i]
    text = '\n\n'.join(build_paras(stream))
    chapters.append({'title': title, 'pages': (pgi, end), 'text': text})

print()
print('== 章节预览 ==')
total = 0
for k, ch in enumerate(chapters):
    t = ch['text']
    total += len(t)
    head = re.sub(r'\s+', ' ', t)[:60]
    # FAILED 页计数
    nf = sum(1 for pi in range(ch['pages'][0], ch['pages'][1]) if not pages.get(str(pi)) or pages.get(str(pi)) == '__FAILED__')
    print('[%d] %-22s 页%d-%d 字数:%-7d FAILED页:%d  首: %s' % (
        k, ch['title'], ch['pages'][0], ch['pages'][1] - 1, len(t), nf, head))
print('总字数:', total)

if '--apply' not in sys.argv:
    print()
    print('(dry-run 完成 — 加 --apply 双端写回)')
    sys.exit(0)

# 写章节文件 (backend + public); 先读旧 meta 保留封面
D = os.path.join(BASE, 'backend/data/book_chapters', BID)
P = os.path.join(BASE, 'app/public/backend/data/book_chapters', BID)
_old_cover = None
_om_fp = os.path.join(D, 'meta.json')
if os.path.exists(_om_fp):
    _old_cover = json.load(open(_om_fp, encoding='utf-8')).get('cover')
for d in (D, P):
    if os.path.exists(d):
        shutil.rmtree(d)
    os.makedirs(d, exist_ok=True)
titles = []
for k, ch in enumerate(chapters):
    paras = [p.strip() for p in re.split(r'\n\s*\n', ch['text']) if p.strip()]
    blocks = [{'type': 'text', 'value': p} for p in paras]
    data = {'title': ch['title'], 'content': blocks, 'index': k}
    json.dump(data, open(os.path.join(D, '%d.json' % k), 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump(data, open(os.path.join(P, '%d.json' % k), 'w', encoding='utf-8'), ensure_ascii=False)
    titles.append(ch['title'])

toc_obj = [{'type': 'chapter', 'title': t, 'index': i} for i, t in enumerate(titles)]
meta = {'bookId': BID, 'title': '精神现象学', 'author': '格奥尔格·威廉·弗里德里希·黑格尔',
        'toc': toc_obj, 'cover': _old_cover, 'chapterCount': len(chapters), 'chapterTitles': titles}
for d in (D, P):
    json.dump(meta, open(os.path.join(d, 'meta.json'), 'w', encoding='utf-8'), ensure_ascii=False)

# book_detail 双端 (保留 summary/tags/region 等)
for pre in (os.path.join(BASE, 'backend/data/book_detail'), os.path.join(BASE, 'app/public/book_detail')):
    fp = os.path.join(pre, BID + '.json')
    if os.path.exists(fp):
        detail = json.load(open(fp, encoding='utf-8'))
        detail['toc'] = toc_obj
        detail['chapterCount'] = len(chapters)
        detail['chapterTitles'] = titles
        json.dump(detail, open(fp, 'w', encoding='utf-8'), ensure_ascii=False)

# books.json chapterCount
bj = json.load(open(os.path.join(BASE, 'app/public/books.json'), encoding='utf-8'))
items = bj if isinstance(bj, list) else bj.get('books', [])
for it in items:
    if it.get('id') == BID:
        it['chapterCount'] = len(chapters)
        break
json.dump(bj, open(os.path.join(BASE, 'app/public/books.json'), 'w', encoding='utf-8'), ensure_ascii=False)

print()
print('✓ 已写回: %d 章, 双端章节 + meta + book_detail + books.json' % len(chapters))
