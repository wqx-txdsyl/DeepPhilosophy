# -*- coding: utf-8 -*-
"""黄帝内经 507977116b57 修复（一次性，ncx 锚点切分，拆素问/灵枢两部 + 去前缀）
epub: 黄帝内经.epub  ncx 165 条（关于本书/目录/CoverPage 垃圾 + 素问 81 篇 + 灵枢 81 篇平铺）
旧数据 164 章 = 关于本书 + 目录 + 素问 81 + 灵枢 81（"素问·/灵枢·"前缀混标题），部级缺失。
结构:
  SKIP: 关于本书/目录/CoverPage
  part(0) × 2: 素问（81 篇）/ 灵枢（81 篇）
  chapter × 162: 标题去 "素问·/灵枢·" 前缀（上古天真论/四气调神大论/…九针十二原/…痈疽）
用法: python _xr_huangdineijing_rebuild.py [--dry]
"""
import zipfile, re, json, os, sys, html as html_mod, shutil, bisect

EP = 'F:/philosophy/东方/佚名/黄帝内经.epub'
SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters/507977116b57"
DST = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/507977116b57"
SKIP = {"关于本书", "目录", "CoverPage"}
VOLS = [("素问", "素问·"), ("灵枢", "灵枢·")]

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

def next_split(node_i):
    for node2 in flat[node_i + 1:]:
        if node2['label'] in SKIP:
            continue
        s2 = seg_text(node2['src'])
        if s2:
            return s2[0]
    return (len(htmls), 0)

def head_eq(b0, title):
    n0, nt = norm(b0), norm(title)
    if n0 == nt or (n0.startswith(nt) and len(n0) - len(nt) <= 4):
        return True
    return False

toc = []
files = {}
ch_index = 0
warns = []
vol_i = 0

for i, node in enumerate(flat):
    if node['label'] in SKIP:
        continue
    # 部 part：按顺序触发（素问 → 灵枢）
    if vol_i < len(VOLS) and node['label'].startswith(VOLS[vol_i][1]):
        vol_name = VOLS[vol_i][0]
        toc.append({"type": "part", "title": vol_name, "level": 0, "index": ch_index})
        vol_i += 1
    # chapter
    seq = seg_text(node['src'])
    if not seq:
        warns.append(f"!! 无锚点: {node['label']}")
        continue
    fi, bi = seq[0]
    nf, nb = next_split(i)
    blocks = collect(fi, bi, nf, nb)
    while blocks and head_eq(blocks[0]["value"], node['label']):
        blocks = blocks[1:]
    if not blocks:
        warns.append(f"!! 空章节跳过: {node['label']}")
        continue
    title = node['label'][3:] if node['label'][:3] in ('素问·', '灵枢·') else node['label']
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
print(f"\n总: {len(files)} 章, {total_chars} 字符（旧 193,508，含关于本书836+目录1026）")
for tt in toc:
    if tt['type'] == 'part':
        print(("  " * tt['level']) + f"[{tt['level']}] {tt['title']} → index {tt['index']}")
print("标题前3:", [files[i]['title'] for i in range(3)])
print("标题中间:", [files[i]['title'] for i in range(80, 83)])
print("标题末3:", [files[i]['title'] for i in range(len(files) - 3, len(files))])

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
    "bookId": old_meta.get("bookId") or "507977116b57",
    "title": old_meta.get("title") or "黄帝内经",
    "author": old_meta.get("author") or "佚名",
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
