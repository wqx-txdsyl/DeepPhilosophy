# -*- coding: utf-8 -*-
"""马基雅维利语录 96a84c0450cd 修复（一次性，ncx 锚点切分，3 部 part + 条目标题首句化）
epub: 马基雅维利语录.epub  ncx 187 条（致读者 + 3 部 + 183 条编号 01~57×3）
旧数据 184 章 = 致读者 + 01~183 纯数字标题平铺，部标题（君主篇/国家篇/人间篇）缺失。
修复:
 1) 3 部 → part(0)
 2) 条目标题 = 正文首句（截断 45 字），编号块（^\d+$）跳过
 3) 致读者 → chapter
用法: python _xr_maji_rebuild.py [--dry]
"""
import zipfile, re, json, os, sys, html as html_mod, shutil, bisect

EP = 'F:/philosophy/西方/马基雅维利/马基雅维利语录.epub'
SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters/96a84c0450cd"
DST = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/96a84c0450cd"

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
part_labels = [norm(n['label']) for n in flat if n['level'] == 0 and n['children']]
print(f"ncx 条目: {len(flat)} | part: {len(part_labels)}")

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

NUM_ONLY = re.compile(r'^\d{1,3}$')

def next_split(node_i):
    for node2 in flat[node_i + 1:]:
        if node2['level'] != 1:
            continue
        s2 = seg_text(node2['src'])
        if s2:
            return s2[0]
    return (len(htmls), 0)

toc = []
files = {}
ch_index = 0
warns = []

for i, node in enumerate(flat):
    # 部 → part(0)
    if node['level'] == 0 and node['children']:
        toc.append({"type": "part", "title": node['label'], "level": 0, "index": ch_index})
        continue
    # 致读者 / 条目 → chapter
    seq = seg_text(node['src'])
    if not seq:
        warns.append(f"!! 无锚点: {node['label']}")
        continue
    fi, bi = seq[0]
    nf, nb = next_split(i)
    blocks = collect(fi, bi, nf, nb)
    # 首块 = 编号块（^\d+$）跳过
    if blocks and NUM_ONLY.match(blocks[0]["value"]):
        blocks = blocks[1:]
    # 部标题块剥离
    keep = []
    for blk in blocks:
        if norm(blk["value"]) in part_labels:
            continue
        keep.append(blk)
    blocks = keep
    if not blocks:
        warns.append(f"!! 空章节跳过: {node['label']} src={node['src']} 区间[{fi},{bi})-({nf},{nb})")
        continue
    if node['label'] == '致读者':
        title = '致读者'
    else:
        first = blocks[0]["value"]
        title = first[:45] + ('…' if len(first) > 45 else '')
    toc.append({"type": "chapter", "title": title, "index": ch_index, "level": 1})
    files[ch_index] = {"index": ch_index, "title": title, "content": blocks}
    ch_index += 1

print(f"\n章节总数: {len(files)} | toc 条目: {len(toc)}")
print(f"警告: {len(warns)}")
for w in warns:
    print("⚠", w)
total_chars = 0
for idx, ch in files.items():
    nc = sum(len(b['value']) for b in ch['content'])
    total_chars += nc
print(f"\n总: {len(files)} 章, {total_chars} 字符（旧 49,012）")
for tt in toc:
    if tt['type'] == 'part':
        print(("  " * tt['level']) + f"[{tt['level']}] {tt['title']}")
print("示例标题:", [files[i]['title'][:20] for i in range(1, 4)])

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
    "bookId": old_meta.get("bookId") or "96a84c0450cd",
    "title": old_meta.get("title") or "马基雅维利语录",
    "author": old_meta.get("author") or "马基雅维利",
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
