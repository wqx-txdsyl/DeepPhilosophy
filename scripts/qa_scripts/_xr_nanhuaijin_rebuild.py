# -*- coding: utf-8 -*-
"""南怀瑾经典合集（共24册）a26240ee8f45 重建（一次性，书=part/章=chapter/节=section）
epub: 南怀瑾经典合集（共24册）.epub  简体正文  ncx 3075 条
结构: d0=24 书（part）；d1=章/讲题（chapter），d2=节（section），d3+ 只入内容；
      论语别裁 多一层册（d1=上册/下册=part，d2=chapter，d3=section）
      跳过 书名页/目录/总目录/版权页（各书前置页）
注: 易经杂说/药师经/静坐修道 等 d1 全平铺讲题 → 全部为 chapter（ncx 真实结构）
用法: python _xr_nanhuaijin_rebuild.py [--dry]
"""
import zipfile, re, json, os, sys, html as html_mod, shutil, bisect

EP = 'F:/philosophy/东方/南怀瑾/南怀瑾经典合集（共24册）.epub'
SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters/a26240ee8f45"
DST = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/a26240ee8f45"
SKIP = {"书名页", "目录", "总目录", "版权页", "版权", "封面", "内容简介", "南怀瑾先生著述目录"}

z = zipfile.ZipFile(EP)
ncx_name = [n for n in z.namelist() if n.endswith('.ncx')][0]
PREFIX = ncx_name.rsplit('/', 1)[0] + '/' if '/' in ncx_name else ''
t = z.read(ncx_name).decode('utf-8')

def norm(s):
    return re.sub(r"\s+", "", s or "")

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
    lb = re.search(r'<text>(.*?)</text>', seg, re.S)
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

def flatten(nodes, acc=None):
    if acc is None:
        acc = []
    for n in nodes:
        acc.append(n)
        flatten(n['children'], acc)
    return acc

flat = flatten(tree)
print(f"ncx 条目: {len(flat)}")

_HTML_TAG = re.compile(r'<[^>]+>')
_BR = re.compile(r'<br\s*/?>', re.I)

def el_text(seg):
    seg = _BR.sub('\n', seg)
    seg = _HTML_TAG.sub('', seg)
    seg = html_mod.unescape(seg)
    seg = re.sub(r'[ \t\xa0]+', ' ', seg)
    return seg.strip()

def extract_blocks(fname):
    h = z.read(fname).decode('utf-8')
    blocks = []
    for m in re.finditer(r'<(p|table|h[1-6])([^>]*)>(.*?)</\1>', h, re.S):
        tag, inner = m.group(1), m.group(3)
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

htmls = sorted((n for n in z.namelist() if n.endswith(('.html', '.xhtml'))),
               key=lambda n: [int(x) if x.isdigit() else x for x in re.split(r'(\d+)', n)])
blocks_by_file, ids_by_file = {}, {}
for f in htmls:
    blocks_by_file[f], ids_by_file[f] = extract_blocks(f)
print(f"html 文件: {len(htmls)}")

def anchor_order():
    d = {}
    for fi, f in enumerate(htmls):
        blocks = blocks_by_file[f]
        starts = [b[0] for b in blocks]
        dm = {}
        for aid, off in ids_by_file[f].items():
            bi = bisect.bisect_right(starts, off) - 1
            dm[aid] = (fi, max(bi, 0))
        d[f] = dm
    return d

ANCH = anchor_order()

def seg_text(src):
    f, _, aid = src.partition('#')
    if PREFIX and f.startswith(PREFIX):
        pass
    elif PREFIX:
        f = PREFIX + f
    if f in htmls:
        if aid and aid in ANCH.get(f, {}):
            return [ANCH[f][aid]]
        if aid:
            print(f"  !! 锚点缺失: {src}")
        return [(htmls.index(f), 0)]
    return []

SKIP_NORMS = {norm(k) for k in SKIP}

def collect(fi, bi, end_fi, end_bi):
    blocks = []
    for kf in range(fi, end_fi + 1):
        if kf >= len(htmls):
            break
        bl = blocks_by_file[htmls[kf]]
        start = bi if kf == fi else 0
        e = end_bi if kf == end_fi else len(bl)
        for kbi in range(start, e):
            off, kind, text = bl[kbi]
            blocks.append({"type": "text", "value": text})
    return blocks

def next_split(node_i, cl):
    """下一章切分点：root/SKIP/chapter 层；跳过 section 及更深（否则区间为空）"""
    for node2 in flat[node_i + 1:]:
        if node2['level'] >= cl + 1:
            continue
        s2 = seg_text(node2['src'])
        if s2:
            return s2[0]
    return (len(htmls), 0)

def head_eq(b0, title):
    n0, nt = norm(b0), norm(title)
    return n0 == nt or (n0.startswith(nt) and len(n0) - len(nt) <= 4)

def detect_cl(root):
    """册层判定：d1 含 （上册）/（下册） 等 → chapter 从 d2 开始"""
    for c in root['children']:
        cn = norm(c['label'])
        if cn.endswith(("（上册）", "（下册）", "（中册）")) or cn in ("上册", "中册", "下册"):
            return 2
    return 1

toc = []
files = {}
ch_index = 0
warns = []
cl = 1
cur_secs = []  # 当前 chapter 挂载的 section 缓冲
prev_parts = []  # [(nl, anchor)] part 栈（书 + 册）

for i, node in enumerate(flat):
    nl = norm(node['label'])
    if node['level'] == 0:
        cl = detect_cl(node)
        if nl in SKIP_NORMS:
            cl = -1  # 总目录 root：整棵跳过
            prev_parts = []
            continue
        toc.append({"type": "part", "title": node['label'], "level": 0, "index": ch_index})
        seq0 = seg_text(node['src'])
        prev_parts = [(nl, seq0[0] if seq0 else None)]
        continue
    if cl < 0:
        continue
    if nl in SKIP_NORMS:
        prev_parts = []  # 书名页/目录 等切分点：重置 part 锚点
        continue
    if cl == 2 and node['level'] == 1:
        # 册层 = part
        toc.append({"type": "part", "title": node['label'], "level": 1, "index": ch_index})
        s1 = seg_text(node['src'])
        prev_parts.append((nl, s1[0] if s1 else None))
        continue
    if node['level'] == cl:
        # chapter：先挂载上一 chapter 的 sections（遍历顺序=节在章之后）
        for s in cur_secs:
            toc.append(s)
        cur_secs = []
        seq = seg_text(node['src'])
        if not seq:
            warns.append(f"!! 无锚点: {node['label']}")
            continue
        fi, bi = seq[0]
        end_fi, end_bi = next_split(i, cl)
        # 起点：最近同文件的 part 锚点（中间无块才并入）
        pl_nls = []
        start = (fi, bi)
        for pnl, pa in reversed(prev_parts):
            if pa and pa[0] == fi:
                mid = collect(pa[0], pa[1], fi, bi)
                if not mid:
                    start = pa
                    for p2, p2a in prev_parts:
                        if p2a and p2a[0] == fi:
                            pl_nls.append(p2)
                break
        blocks = collect(start[0], start[1], end_fi, end_bi)
        while True:
            bv = norm(blocks[0]["value"]) if blocks else None
            if not bv:
                break
            if nl and head_eq(blocks[0]["value"], nl):
                blocks = blocks[1:]
                continue
            matched_part = False
            for pn in pl_nls:
                if head_eq(blocks[0]["value"], pn):
                    blocks = blocks[1:]
                    matched_part = True
                    break
            if matched_part:
                continue
            break
        prev_parts = []
        # 尾部 SKIP 标题块清理
        while blocks and norm(blocks[-1]["value"]) in SKIP_NORMS:
            blocks = blocks[:-1]
        dedup = []
        for blk in blocks:
            if dedup and norm(dedup[-1]["value"]) == norm(blk["value"]):
                continue
            dedup.append(blk)
        if not dedup:
            warns.append(f"!! 空章节跳过: {node['label']}")
            cur_secs.clear()
            continue
        toc.append({"type": "chapter", "title": node['label'], "index": ch_index, "level": 1})
        for s in cur_secs:
            toc.append(s)
        cur_secs = []
        files[ch_index] = {"index": ch_index, "title": node['label'], "content": dedup}
        ch_index += 1
    elif node['level'] == cl + 1:
        # section 挂 toc（紧跟当前 chapter）
        cur_secs.append({"type": "section", "title": node['label'], "index": ch_index, "level": 2})
    # 更深层级只入内容（不切分）

for s in cur_secs:  # 最后一章的 sections
    toc.append(s)

print(f"\n章节总数: {len(files)} | toc 条目: {len(toc)}")
print(f"警告: {len(warns)}")
for w in warns:
    print("⚠", w)
total_chars = 0
for idx, ch in files.items():
    nb = len(ch['content']); nc = sum(len(b['value']) for b in ch['content'])
    total_chars += nc
    first = ch['content'][0]['value'][:30] if ch['content'] else '(空)'
    print(f"  [{idx}] {ch['title'][:26]} {nb}块 {nc}字 | {first}…")
print(f"\n总: {len(files)} 章, {total_chars} 字符")

if '--dry' in sys.argv:
    sys.exit(0)

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
    "bookId": old_meta.get("bookId") or "a26240ee8f45",
    "title": old_meta.get("title") or "南怀瑾经典合集（共24册）",
    "author": old_meta.get("author") or "南怀瑾",
    "toc": toc,
    "cover": old_meta.get("cover"),
    "chapterCount": len(files),
    "chapterTitles": [ch["title"] for ch in files.values()],
}
json.dump(meta, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print(f"✓ 写入 {SRC}: {len(files)} 章 + meta.json")

shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
print("✓ 同步 DP")
