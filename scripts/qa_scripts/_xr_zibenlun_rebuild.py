# -*- coding: utf-8 -*-
"""资本论 53d1b4ff90d2 重建（一次性，ncx 锚点切分，三卷合订本全平铺 → 卷/册/篇/章/节五级）
epub: 资本论.epub  ncx 335 条（4 根：总目录 + 三卷）
结构:
  d0 卷(part level0) 3 个；d0 总目录 SKIP
  d1 册(part level1) 4 个（第一册/第二册/第三册(上)/资本主义生产的总过程(下)）；
     d1 序言/索引/增补（无子节点）→ chapter
  d2 篇(part level2) 18 个
  d3 章 → chapter（99 个）
  d4 节 → section(level2)（195 个，标题块保留在章内容中）
旧数据 225 条 = 节级/章级/篇级标题全平铺，且"篇标题章"内含正文（[7]=第一章开头、
[29]=第四章、[30]=第五章）→ 章节划分不遵循 ncx 边界，必须全重建。
要点:
  1) 章区间 [本章锚点, 下一 chapter 锚点)，跳过中间 part 节点
  2) 区间内混入的 part 标题块（如"第二篇 货币转化为资本"在 第一章 4.拜物教之后）→ 剥离
  3) 章首标题块 head_eq 剥离（含注标记容错）
用法: python _xr_zibenlun_rebuild.py [--dry]
"""
import zipfile, re, json, os, sys, html as html_mod, shutil, bisect

EP = 'F:/philosophy/西方/卡尔·马克思/资本论.epub'
SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters/53d1b4ff90d2"
DST = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/53d1b4ff90d2"

z = zipfile.ZipFile(EP)
ncx = [n for n in z.namelist() if n.endswith('.ncx')][0]
PREFIX = ncx.rsplit('/', 1)[0] + '/' if '/' in ncx else ''
t = z.read(ncx).decode('utf-8')

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
        'children': [],
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
# 分类：part = d0 卷 + d1 有子节点(册) + d2 篇；chapter = d1 无子节点 + d3；section = d4
PART_LV = {0: 0, 1: 1, 2: 2}  # d0 卷→part0, d1 册→part1, d2 篇→part2
part_labels = []
for n in flat:
    if n['level'] in PART_LV and (n['level'] != 1 or n['children']):
        part_labels.append(norm(n['label']))
    if n['level'] == 0 and n['label'] == '总目录':
        part_labels.append(norm(n['label']))  # SKIP 标记
print(f"ncx 条目: {len(flat)} | part 标题: {len([p for p in part_labels if p])}")

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
    ids = {}
    for m in re.finditer(r'<(p|table|h[1-6])([^>]*)>(.*?)</\1>', h, re.S):
        tag, inner = m.group(1), m.group(3)
        if tag == 'p':
            text = el_text(inner)
            if text:
                blocks.append((m.start(), text))
        elif tag == 'table':
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', inner, re.S)
            for r in rows:
                cells = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', r, re.S)
                row_text = '  '.join(el_text(c) for c in cells)
                if row_text:
                    blocks.append((m.start(), row_text))
        elif tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            text = el_text(inner)
            if text:
                blocks.append((m.start(), text))
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

def collect(fi, bi, end_fi, end_bi):
    blocks = []
    for kf in range(fi, end_fi + 1):
        if kf >= len(htmls):
            break
        bl = blocks_by_file[htmls[kf]]
        start = bi if kf == fi else 0
        e = end_bi if kf == end_fi else len(bl)
        for kbi in range(start, e):
            blocks.append({"type": "text", "value": bl[kbi][1]})
    return blocks

def is_chapter(n):
    if n['level'] == 3:
        return True
    if n['level'] == 1 and not n['children']:
        return True
    return False

def next_split(node_i):
    """下一个 chapter 切分点"""
    for node2 in flat[node_i + 1:]:
        if not is_chapter(node2):
            continue
        s2 = seg_text(node2['src'])
        if s2:
            return s2[0]
    return (len(htmls), 0)

def head_eq(b0, title):
    n0, nt = norm(b0), norm(title)
    if n0 == nt or (n0.startswith(nt) and len(n0) - len(nt) <= 4):
        return True
    n0n = norm(re.sub(r'\(\d+\)', '', b0))
    ntn = norm(re.sub(r'\(\d+\)', '', title))
    return n0n == ntn or (n0n.startswith(ntn) and len(n0n) - len(ntn) <= 4)

toc = []
files = {}
ch_index = 0
warns = []
skip_d0_total = True

for i, node in enumerate(flat):
    nl = norm(node['label'])
    # d0 总目录 SKIP
    if node['level'] == 0 and node['label'] == '总目录':
        continue
    # part 节点（d0 卷 / d1 册 / d2 篇）
    if node['level'] in PART_LV and (node['level'] != 1 or node['children']):
        toc.append({"type": "part", "title": node['label'], "level": PART_LV[node['level']], "index": ch_index})
        continue
    # section（d4 节）只挂 toc
    if node['level'] >= 4:
        toc.append({"type": "section", "title": node['label'], "index": ch_index, "level": 2})
        continue
    # chapter（d3 章 / d1 序言索引增补）
    seq = seg_text(node['src'])
    if not seq:
        warns.append(f"!! 无锚点: {node['label']}")
        continue
    fi, bi = seq[0]
    nf, nb = next_split(i)
    blocks = collect(fi, bi, nf, nb)
    # 章首标题块剥离
    while blocks and head_eq(blocks[0]["value"], node['label']):
        blocks = blocks[1:]
    # part 标题块剥离（混入的篇/册/卷标题）
    keep = []
    for blk in blocks:
        nv = norm(blk["value"])
        if nv in part_labels:
            continue
        keep.append(blk)
    blocks = keep
    dedup = []
    for blk in blocks:
        if dedup and norm(dedup[-1]["value"]) == norm(blk["value"]):
            continue
        dedup.append(blk)
    if not dedup:
        warns.append(f"!! 空章节跳过: {node['label']}")
        continue
    toc.append({"type": "chapter", "title": node['label'], "index": ch_index, "level": 1})
    files[ch_index] = {"index": ch_index, "title": node['label'], "content": dedup}
    ch_index += 1

print(f"\n章节总数: {len(files)} | toc 条目: {len(toc)}")
print(f"警告: {len(warns)}")
for w in warns:
    print("⚠", w)
total_chars = 0
for idx, ch in files.items():
    nc = sum(len(b['value']) for b in ch['content'])
    total_chars += nc
    first = ch['content'][0]['value'][:26] if ch['content'] else '(空)'
    print(f"  [{idx}] {ch['title'][:30]} {len(ch['content'])}块 {nc}字 | {first}…")
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
    "bookId": old_meta.get("bookId") or "53d1b4ff90d2",
    "title": old_meta.get("title") or "资本论",
    "author": old_meta.get("author") or "卡尔·马克思",
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
