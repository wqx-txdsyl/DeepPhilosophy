# -*- coding: utf-8 -*-
"""批量排查 epub 入库丢章 v2（哲学的慰藉 #67 先例）
可靠判据：ncx 条目标题出现在 epub 正文（块级标题形态）但入库数据中没有对应章节
  → 真丢章。ncx 条目在正文里根本找不到 → 该书 ncx 粒度粗/与内容无关，忽略。
1) title 模糊匹配 F:/philosophy 下 epub；2) 读 ncx 非垃圾条目
3) 正文块文本 vs 入库章节（标题 + 首块 + 全部文本）双重判定
用法: python _epub_missing_check.py
"""
import json, glob, re, os, zipfile, html as html_mod

BD = 'f:/program/Python/PhiAgent/backend/data/book_detail'
BC = 'f:/program/Python/PhiAgent/backend/data/book_chapters'
PHI = 'F:/philosophy'

def norm(s):
    s = s or ''
    s = re.sub(r'（.*?）|\(.*?\)|【.*?】', '', s)
    s = re.sub(r'[·•\-—_—\s:：,，。.!！?？"\'"`~*、；;]', '', s)
    return s.lower()

# 1) epub 索引
epubs = glob.glob(f'{PHI}/**/*.epub', recursive=True)
epub_norm = {}
for e in epubs:
    name = os.path.splitext(os.path.basename(e))[0]
    n = norm(name)
    epub_norm.setdefault(n, []).append(e)
    if len(n) >= 4:
        epub_norm.setdefault(n[:4], []).append(e)

def match_epub(title):
    t = norm(title)
    if t in epub_norm:
        return epub_norm[t][0]
    if len(t) >= 4 and t[:4] in epub_norm:
        return epub_norm[t][0] if len(epub_norm[t[:4]]) == 1 else None
    return None

SKIP_LABELS = {'关于本书', '目录', 'coverpage', '封面', '版权页', '版权信息', '开始',
               'start', 'text00000', 'camera', 'images'}
_HTML_TAG = re.compile(r'<[^>]+>')
_BR = re.compile(r'<br\s*/?>', re.I)

def el_text(seg):
    seg = _BR.sub('\n', seg)
    seg = _HTML_TAG.sub('', seg)
    seg = html_mod.unescape(seg)
    return re.sub(r'\s+', '', seg)

def body_texts(z, htmls):
    """全部块文本（去空白）"""
    out = []
    for f in htmls:
        try:
            h = z.read(f).decode('utf-8', errors='replace')
        except Exception:
            continue
        for m in re.finditer(r'<(p|table|h[1-6])([^>]*)>(.*?)</\1>', h, re.S):
            tx = el_text(m.group(3))
            if tx:
                out.append(tx)
    return out

suspicious = []
nomatch = []
checked = 0
for f in sorted(glob.glob(f'{BD}/*.json')):
    bid = os.path.basename(f)[:-5]
    try:
        d = json.load(open(f, encoding='utf-8'))
        meta = json.load(open(f'{BC}/{bid}/meta.json', encoding='utf-8'))
    except Exception:
        continue
    if d.get('file_type') != 'epub':
        continue
    if not os.path.isdir(f'{BC}/{bid}'):
        continue
    checked += 1
    ep = match_epub(d.get('title', ''))
    if not ep:
        nomatch.append(d.get('title'))
        continue
    try:
        z = zipfile.ZipFile(ep)
        ncx = [n for n in z.namelist() if n.endswith('.ncx')]
        if not ncx:
            continue
        t = z.read(ncx[0]).decode('utf-8', errors='replace')
        htmls = [n for n in z.namelist() if n.endswith(('.html', '.xhtml'))]
        blocks = body_texts(z, htmls)
    except Exception:
        continue
    labels = []
    for m in re.finditer(r'<navPoint[^>]*>.*?<text>(.*?)</text>.*?</navPoint>', t, re.S):
        lb = html_mod.unescape(re.sub(r'<[^>]+>', '', m.group(1))).strip()
        if lb and norm(lb) not in {norm(s) for s in SKIP_LABELS}:
            labels.append(lb)
    if not labels:
        continue
    # 只取顶层条目（d0：<navPoint> 后直接跟 <navLabel>，无嵌套 navPoint 前缀）
    top_labels = []
    for m in re.finditer(r'<navPoint[^>]*>(?!(?:[^<]*<[^/])*?<navPoint)', t):
        pass
    # 简单法：统计每级缩进深度（用 navPoint 开闭合配平），取深度 0
    opens = [m.start() for m in re.finditer(r'<navPoint[^>]*>', t)]
    closes = [m.start() for m in re.finditer(r'</navPoint>', t)]
    events = sorted([(p, 'o') for p in opens] + [(p, 'c') for p in closes])
    depth = 0
    depth_of = {}
    for pos, k in events:
        if k == 'o':
            depth_of[pos] = depth
            depth += 1
        else:
            depth -= 1
    top_lb = []
    lb_of = {}
    for m in re.finditer(r'<navPoint[^>]*>', t):
        pos = m.start()
        seg_end = t.find('</navPoint>', pos)
        seg = t[pos:seg_end]
        lm = re.search(r'<text>(.*?)</text>', seg, re.S)
        if lm:
            lb = html_mod.unescape(re.sub(r'<[^>]+>', '', lm.group(1))).strip()
            if depth_of.get(pos, 0) == 0:
                top_lb.append(lb)
    top_lb = [lb for lb in top_lb if lb and norm(lb) not in {norm(s) for s in SKIP_LABELS}]
    if not top_lb:
        continue
    labels = top_lb
    # 粒度过滤：顶层条目数与入库章数相当（0.4~2.5 倍）才可能丢章
    n_ratio = len(labels) / max(meta.get('chapterCount', 1), 1)
    if not (0.4 <= n_ratio <= 2.5):
        continue
    # 入库内容：所有章节文本（去空白）+ 标题
    ch_texts = []
    for i in range(meta.get('chapterCount', 0)):
        try:
            ch = json.load(open(f'{BC}/{bid}/{i}.json', encoding='utf-8'))
            for b in ch.get('content', []):
                v = b.get('value') if isinstance(b, dict) else b
                if isinstance(v, str):
                    ch_texts.append(re.sub(r'\s+', '', v))
        except Exception:
            pass
    ch_all = set(ch_texts)
    toc_titles = {norm(tt.get('title', '') if isinstance(tt, dict) else str(tt))
                  for tt in meta.get('toc', [])}
    missing = []
    for lb in labels:
        nl = norm(lb)
        # 1) 正文块级精确命中（作为独立标题块存在）
        found_block = False
        for b in blocks:
            nb = norm(b)
            if nb == nl or nb.startswith(nl) or nl.startswith(nb):
                found_block = True
                break
        if not found_block:
            continue  # 正文里没有 → 忽略（ncx 粒度粗/无关）
        # 2) 入库内容里是否有该标题（标题或正文开头）
        in_lib = nl in toc_titles
        if not in_lib:
            for ct in ch_all:
                if nl and (ct == nl or ct.startswith(nl)):
                    in_lib = True
                    break
        if not in_lib:
            missing.append(lb)
    if missing:
        suspic = {'title': d.get('title'), 'bid': bid, 'ncx': len(labels),
                  'chapters': meta.get('chapterCount'), 'missing': missing}
        suspicious.append(suspic)

print(f"检查 {checked} 本 epub 书")
print(f"\n=== 疑似真丢章 {len(suspicious)} 本 ===")
for s in suspicious:
    print(f"\n{s['title']} | bid {s['bid']} | ncx {s['ncx']} vs 入库 {s['chapters']}")
    for m in s['missing']:
        print(f"  缺: {m[:60]}")
print(f"\n=== 未匹配到 epub {len(nomatch)} 本 ===")
for t in nomatch[:40]:
    print(f"  {t}")
