# -*- coding: utf-8 -*-
"""康德著作集（套装10册）309de54e4392 整册重建（一次性）
epub 源: 康德著作集（套装10册）（汉译世界学术名著丛书）ncx 441 条完整目录
方案:
- ncx depth0 = 册 → part；depth1 = chapter（内容聚合为文件）；depth2 = section（toc 标记）；depth3+ 仅作切分点
- 跳过 总目录/封面/版权/版权页/目录 类条目（内容丢弃）
- 文本提取: 每个 chapter 内容 = 从该章锚点(含)到下一锚点(不含)的全部块级元素文本（跨 html）
- 输出覆盖 {bid}/（先备份为 _old_bad），同步 DP
用法: python _xr_kant_workset.py [--dry]
"""
import zipfile, re, json, os, sys, html as html_mod, shutil

EP = 'F:/philosophy/西方/伊曼努尔·康德/康德著作集（套装10册）（汉译世界学术名著丛书） - 康德.epub'
SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters/309de54e4392"
DST = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/309de54e4392"
SKIP = {"总目录", "封面", "版权", "版权页", "目录"}

z = zipfile.ZipFile(EP)

def norm(s):
    return re.sub(r"\s+", "", s or "")

# ────────── 1. 解析 ncx 树（括号配对） ──────────
t = z.read('toc.ncx').decode('utf-8')
opens = [m.start() for m in re.finditer(r'<navPoint[^>]*>', t)]
closes = [m.start() for m in re.finditer(r'</navPoint>', t)]

def build_tree():
    events = sorted([(p, 'o') for p in opens] + [(p, 'c') for p in closes])
    stack, roots = [], []
    for pos, k in events:
        if k == 'o':
            stack.append({'pos': pos, 'children': []})
        else:
            node = stack.pop()
            node['end'] = pos
            if stack:
                stack[-1]['children'].append(node)
            else:
                roots.append(node)
    return roots

def node_info(node):
    seg = t[node['pos']:node['end']]
    lb = re.search(r'<text>(.*?)</text>', seg)
    sc = re.search(r'<content src="(.*?)"', seg)
    return {
        'label': html_mod.unescape(lb.group(1)) if lb else '',
        'src': sc.group(1) if sc else '',
    }

def decorate(nodes, level=0):
    out = []
    for node in nodes:
        info = node_info(node)
        info['level'] = level
        info['children'] = decorate(node['children'], level + 1)
        out.append(info)
    return out

tree = decorate(build_tree())
books = [b for b in tree]
print(f"册数: {len(books)}")

# ────────── 2. 文本提取（块级元素 → 段） ──────────
_HTML_TAG = re.compile(r'<[^>]+>')
_BR = re.compile(r'<br\s*/?>', re.I)

def el_text(seg):
    """块内文本: 去标签、<br> 换行、unescape、压缩空白"""
    seg = _BR.sub('\n', seg)
    seg = _HTML_TAG.sub('', seg)
    seg = html_mod.unescape(seg)
    seg = re.sub(r'[ \t\xa0]+', ' ', seg)
    return seg.strip()

def extract_blocks(fname):
    """html 文件的块级文本: 返回 (blocks, ids)
    blocks: [(start_off, kind, text)]（文档序）
    ids:    {aid: 字节偏移}（含 a/span/div 等所有带 id 元素）
    """
    h = z.read(fname).decode('utf-8')
    blocks = []
    for m in re.finditer(r'<(p|table|h[1-6])([^>]*)>(.*?)</\1>', h, re.S):
        tag, attrs, inner = m.group(1), m.group(2), m.group(3)
        cls = re.search(r'class="([^"]*)"', attrs)
        cls = cls.group(1) if cls else ''
        if tag == 'p':
            text = el_text(inner)
            if text:
                blocks.append((m.start(), 'p', text))
        elif tag == 'table':
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', inner, re.S)
            for r in rows:
                cells = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', r, re.S)
                row_text = '  '.join(el_text(c) for c in cells)
                if row_text:
                    blocks.append((m.start(), 'table', row_text))
        elif tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            text = el_text(inner)
            if text:
                blocks.append((m.start(), 'h', text))
    ids = {}
    for m in re.finditer(r'<[a-zA-Z][^>]*\bid="([^"]+)"', h):
        ids.setdefault(m.group(1), m.start())
    return blocks, ids

# 预载全部 html 的块序列
htmls = sorted((n for n in z.namelist() if n.startswith('text/') and n.endswith('.html')),
               key=lambda n: [int(x) if x.isdigit() else x for x in re.split(r'(\d+)', n)])
blocks_by_file, ids_by_file = {}, {}
for f in htmls:
    blocks_by_file[f], ids_by_file[f] = extract_blocks(f)
print(f"html 文件: {len(htmls)}")

def anchor_order():
    """{aid: (file_rank, block_pos)} — id 偏移 → 其后的第一个块（bisect）"""
    import bisect
    d = {}
    for fi, f in enumerate(htmls):
        blocks = blocks_by_file[f]
        starts = [b[0] for b in blocks]
        for aid, off in ids_by_file[f].items():
            bi = bisect.bisect_right(starts, off) - 1
            d[aid] = (fi, max(bi, 0))
    return d

ANCH = anchor_order()

def seg_text(src):
    """src = 'file#aid' 或 'file' → 该锚点起(含)到下一锚点(不含)的块; 无 aid 用文件首"""
    f, _, aid = src.partition('#')
    seq = []
    if aid and aid in ANCH:
        fi, bi = ANCH[aid]
        seq.append((fi, bi))
    else:
        if aid:
            print(f"  !! 锚点缺失: {src}")
        fi = htmls.index(f) if f in htmls else -1
        if fi < 0:
            return []
        seq.append((fi, 0))
    return seq

# 每个 depth1 条目的起始锚点（文档序）
chapters_global = []
for b in books:
    for c in b['children']:
        chapters_global.append((b, c))

# 排序: 按锚点文档序
def start_pos(c):
    seq = seg_text(c['src'])
    if not seq:
        return (10**9, 10**9)
    return seq[0]

# ────────── 3. 组装 ──────────
toc = []
files = {}
ch_index = 0
warns = []
per_chapter_seen = {}  # 防止重复处理同一 chapter 锚点

for b in books:
    if norm(b['label']) in SKIP:
        continue
    toc.append({"type": "part", "title": b['label'], "level": 0, "index": ch_index})
    # 册内 depth1（按 ncx 顺序 = 文档序）
    chs = b['children']
    prev_end = None
    for ci, c in enumerate(chs):
        if norm(c['label']) in SKIP:
            continue
        # 起点
        seq = seg_text(c['src'])
        if not seq:
            warns.append(f"!! 无锚点: {b['label']} > {c['label']}")
            continue
        fi, bi = seq[0]
        # 终点 = 下一个非 skip depth1 的起点（含册外后续）
        end_fi, end_bi = None, None
        for b2 in books[books.index(b):]:
            for c2 in b2['children']:
                if norm(c2['label']) in SKIP:
                    continue
                s2 = seg_text(c2['src'])
                if not s2:
                    continue
                k2 = (s2[0][0], s2[0][1])
                k1 = (fi, bi)
                if k2 > k1:
                    end_fi, end_bi = k2
                    break
            if end_fi is not None:
                break
        if end_fi is None:
            end_fi, end_bi = len(htmls), 0
        # 收集块
        blocks = []
        for kf in range(fi, end_fi + 1):
            if kf >= len(htmls):
                break
            f = htmls[kf]
            bl = blocks_by_file[f]
            start = bi if kf == fi else 0
            end = end_bi if kf == end_fi else len(bl)
            for kbi in range(start, end):
                off, kind, text = bl[kbi]
                blocks.append({"type": "text", "value": text})
        # 首块若与 chapter 标题重复则跳过（ncx 锚点元素常是标题本身）
        if blocks and norm(blocks[0]["value"]) == norm(c['label']):
            blocks = blocks[1:]
        # 空章节警告
        if not blocks:
            warns.append(f"!! 空章节: {b['label']} > {c['label']} ({c['src']})")
        # 去重: 相邻重复段（切分边界重叠产生）
        dedup = []
        for blk in blocks:
            if dedup and norm(dedup[-1]["value"]) == norm(blk["value"]):
                continue
            dedup.append(blk)
        blocks = dedup
        # section（depth2）
        secs = []
        for s in c['children']:
            secs.append({"type": "section", "title": s['label'], "index": ch_index, "level": 2})
        toc.append({"type": "chapter", "title": c['label'], "index": ch_index, "level": 1})
        toc.extend(secs)
        files[ch_index] = {"index": ch_index, "title": c['label'], "content": blocks}
        ch_index += 1

print(f"\n章节总数: {len(files)} | toc 条目: {len(toc)}")
print(f"警告: {len(warns)}")
for w in warns:
    print("⚠", w)

# ────────── 4. 内容统计抽查 ──────────
total_blocks = 0
total_chars = 0
for idx, ch in files.items():
    nb = len(ch["content"])
    nc = sum(len(b["value"]) for b in ch["content"])
    total_blocks += nb
    total_chars += nc
    first = ch["content"][0]["value"][:30] if ch["content"] else "(空)"
    print(f"  [{idx}] {ch['title'][:34]} {nb}块 {nc}字 | 首: {first}…")
print(f"\n总: {len(files)} 章, {total_blocks} 块, {total_chars} 字符")

if '--dry' in sys.argv:
    sys.exit(0)

# ────────── 5. 备份旧数据 + 写盘 ──────────
if os.path.isdir(SRC):
    suf = "_old_bad"
    i2 = 2
    while os.path.isdir(SRC + suf):
        suf = f"_old_bad{i2}"
        i2 += 1
    os.rename(SRC, SRC + suf)
    print(f"备份旧数据 → {os.path.basename(SRC) + suf}")
os.makedirs(SRC)

old_meta = {}
old_bid = SRC + "_old_bad"
if os.path.isdir(old_bid) and os.path.exists(os.path.join(old_bid, "meta.json")):
    old_meta = json.load(open(os.path.join(old_bid, "meta.json"), encoding="utf-8"))

for idx, ch in files.items():
    json.dump(ch, open(os.path.join(SRC, f"{idx}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
meta = {
    "bookId": old_meta.get("bookId") or "309de54e4392",
    "title": old_meta.get("title") or "康德著作集（套装10册）",
    "author": old_meta.get("author") or "康德",
    "toc": toc,
    "cover": old_meta.get("cover"),
    "chapterCount": len(files),
    "chapterTitles": [ch["title"] for ch in files.values()],
}
json.dump(meta, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print(f"✓ 写入 {SRC}: {len(files)} 章 + meta.json")

# ────────── 6. 同步 DP ──────────
shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
print("✓ 同步 DP")
