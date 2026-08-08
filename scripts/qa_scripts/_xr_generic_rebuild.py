# -*- coding: utf-8 -*-
"""通用 ncx 分层重建（d0=part/chapter 混合，d1=chapter，d2=section）
支持: #130 新教伦理 / #61 哲学·科学·常识 / #134 柏拉图哲学作品集
映射: d0 匹配 PART_RE → part（锚点并入下一 chapter 起点）；
      其余 d0 → chapter（前置序言等）；d1/d2 → section（不切分内容）
      跳过 SKIP 条目（不产生 toc，内容仍按锚点区间保留）
用法: python _xr_generic_rebuild.py {130|61|134} [--dry]
"""
import zipfile, re, json, os, sys, html as html_mod, shutil, bisect

BOOKS = {
    '130': dict(
        EP='F:/philosophy/西方/马克斯·韦伯/新教伦理与资本主义精神.epub',
        SRC="f:/program/Python/PhiAgent/backend/data/book_chapters/278a154690ce",
        DST="f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/278a154690ce",
        bid="278a154690ce", title="新教伦理与资本主义精神", author="马克斯·韦伯",
        SKIP={"书名页", "目录", "版权页", "英文版权页", "索引", "附录"},
        PART_RE=r'^第[一二三四五]部分'),
    '61': dict(
        EP='F:/philosophy/东方/陈嘉映/哲学·科学·常识.epub',
        SRC="f:/program/Python/PhiAgent/backend/data/book_chapters/92c62220d4a3",
        DST="f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/92c62220d4a3",
        bid="92c62220d4a3", title="哲学·科学·常识", author="陈嘉映",
        SKIP={"封面", "文前"},
        PART_RE=r'^[上下]篇$'),
    '134': dict(
        EP='F:/philosophy/西方/柏拉图/柏拉图哲学作品集（套装6册）.epub',
        SRC="f:/program/Python/PhiAgent/backend/data/book_chapters/d54981640212",
        DST="f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/d54981640212",
        bid="d54981640212", title="柏拉图哲学作品集", author="柏拉图",
        SKIP={"总目录", "封面", "目录", "插页"},
        PART_RE=None),  # d0 全为册（part）
}

key = sys.argv[1] if len(sys.argv) > 1 else '130'
B = BOOKS[key]
dry = '--dry' in sys.argv

z = zipfile.ZipFile(B['EP'])

def norm(s):
    return re.sub(r"\s+", "", s or "")

ncx_name = [n for n in z.namelist() if n.endswith('.ncx')][0]
t = z.read(ncx_name).decode('utf-8')
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

flat = flatten(tree)  # 全部层级（d0/d1/d2）
print(f"ncx 条目: {len(flat)}")

# ────────── 文本提取 ──────────
PREFIX = ''
ncx_name = [n for n in z.namelist() if n.endswith('.ncx')][0]
if '/' in ncx_name:
    PREFIX = ncx_name.rsplit('/', 1)[0] + '/'

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

# ────────── 组装 ──────────
PART_RE = re.compile(B['PART_RE']) if B['PART_RE'] else None
toc = []
files = {}
ch_index = 0
warns = []
prev_part_anchor = None

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

SKIP_NORMS = {norm(k) for k in B['SKIP']}

def next_split(node_i):
    """下一个切分点（part/chapter/SKIP）的锚点——SKIP 也切分（内容丢弃），
    避免尾部章吞入索引/版权页"""
    for node2 in flat[node_i + 1:]:
        if node2['level'] >= 2:
            continue  # section 不切分
        s2 = seg_text(node2['src'])
        if s2:
            return s2[0]
    return (len(htmls), 0)

def head_eq(b0, title):
    """首块是否等于标题（容忍脚注圈码后缀如 新教教派与资本主义精神[1]）"""
    n0, nt = norm(b0), norm(title)
    return n0 == nt or (n0.startswith(nt) and len(n0) - len(nt) <= 4)

def collect_secs(node):
    out = []
    for s in node['children']:
        if norm(s['label']) in {norm(k) for k in B['SKIP']}:
            continue
        out.append({"type": "section", "title": s['label'], "index": ch_index, "level": 2})
    return out

prev_part_label = None

for i, node in enumerate(flat):
    nl = norm(node['label'])
    if nl in SKIP_NORMS:
        continue
    if node['level'] >= 2:
        continue  # section 节点不切分（内容并入章）
    seq = seg_text(node['src'])
    if not seq:
        warns.append(f"!! 无锚点: {node['label']}")
        continue
    fi, bi = seq[0]
    is_part = node['level'] == 0 and (PART_RE is None or PART_RE.match(node['label']))
    if is_part:
        toc.append({"type": "part", "title": node['label'], "level": 0, "index": ch_index})
        prev_part_anchor = (fi, bi)
        prev_part_label = nl
        continue
    # chapter：终点 = 下一个切分点（part/chapter/SKIP）
    end_fi, end_bi = next_split(i)
    start = prev_part_anchor if prev_part_anchor is not None else (fi, bi)
    prev_part_anchor = None
    blocks = collect(start[0], start[1], end_fi, end_bi)
    # 首块删除：chapter 标题 与 前一个 part 标题（part 锚点并入起点，可能连排）
    while True:
        if blocks and nl and head_eq(blocks[0]["value"], nl):
            blocks = blocks[1:]
            continue
        if blocks and prev_part_label and head_eq(blocks[0]["value"], prev_part_label):
            blocks = blocks[1:]
            continue
        break
    prev_part_label = None
    # 尾部 SKIP 标题块清理（索引/英文版权页 等切分点块）
    while blocks and norm(blocks[-1]["value"]) in SKIP_NORMS:
        blocks = blocks[:-1]
    dedup = []
    for blk in blocks:
        if dedup and norm(dedup[-1]["value"]) == norm(blk["value"]):
            continue
        dedup.append(blk)
    if not dedup:
        warns.append(f"!! 空章节跳过: {node['label']}")
        continue
    toc.append({"type": "chapter", "title": node['label'], "index": ch_index, "level": 1})
    toc.extend(collect_secs(node))
    files[ch_index] = {"index": ch_index, "title": node['label'], "content": dedup}
    ch_index += 1

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

if dry:
    sys.exit(0)

if os.path.isdir(B['SRC']):
    suf = "_old_bad"
    i2 = 2
    while os.path.isdir(B['SRC'] + suf):
        suf = f"_old_bad{i2}"
        i2 += 1
    os.rename(B['SRC'], B['SRC'] + suf)
    print(f"备份旧数据 → {os.path.basename(B['SRC']) + suf}")
os.makedirs(B['SRC'])
old_meta = {}
old_bid = B['SRC'] + "_old_bad"
if os.path.isdir(old_bid) and os.path.exists(os.path.join(old_bid, "meta.json")):
    old_meta = json.load(open(os.path.join(old_bid, "meta.json"), encoding="utf-8"))
for idx, ch in files.items():
    json.dump(ch, open(os.path.join(B['SRC'], f"{idx}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
meta = {
    "bookId": old_meta.get("bookId") or B['bid'],
    "title": old_meta.get("title") or B['title'],
    "author": old_meta.get("author") or B['author'],
    "toc": toc,
    "cover": old_meta.get("cover"),
    "chapterCount": len(files),
    "chapterTitles": [ch["title"] for ch in files.values()],
}
json.dump(meta, open(os.path.join(B['SRC'], "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print(f"✓ 写入 {B['SRC']}: {len(files)} 章 + meta.json")

shutil.rmtree(B['DST'], ignore_errors=True)
shutil.copytree(B['SRC'], B['DST'])
print("✓ 同步 DP")
