# -*- coding: utf-8 -*-
"""马克思恩格斯文集 7729ccdecb0f 重建（一次性，ncx 锚点切分，十卷平铺 → 卷/册/篇/章/节多级）
epub: 马克思恩格斯文集.epub  ncx 1234 条（11 根：总目录 + 十卷；链式层级 d0 卷/d1 文章/d2/d3/d4）
旧数据 951 章 = d1 文章 + d2/d3/d4 节全平铺，卷级标题缺失（仅"第X卷说明"）。
结构:
  d0 卷 → part(0)；"总目录" SKIP
  d1 匹配 ^第X[册篇]（资本论册/篇）→ part(1)；d1 其他（文章/说明/编审人员）→ chapter
  d2 匹配 ^第X[编篇] → part(2)；^第X章 → chapter（资本论三卷的章）
     ^[一二三四五六七八九十]+[\s　]（共产党宣言一/二/三）→ section；其他有子 → chapter；无子 → section
  d3/d4 → section
  section 挂当前 ch_index；part index = 该 part 下第一个 chapter 的 index
用法: python _xr_maen_rebuild.py [--dry]
"""
import zipfile, re, json, os, sys, html as html_mod, shutil, bisect

EP = 'F:/philosophy/西方/卡尔·马克思/马克思恩格斯文集.epub'
SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters/7729ccdecb0f"
DST = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/7729ccdecb0f"

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
RANGE_RE = re.compile(r'^第[一二三四五六七八九十百]+[册篇]')
BUAN_RE = re.compile(r'^第[一二三四五六七八九十百]+[编篇]')
ZHANG_RE = re.compile(r'^第[一二三四五六七八九十百]+章')
NUM_HEAD = re.compile(r'^[一二三四五六七八九十]+[\s　]')

def is_part1(n):
    return n['level'] == 1 and bool(RANGE_RE.match(n['label']))

def is_part2(n):
    return n['level'] == 2 and bool(BUAN_RE.match(n['label']))

def is_ch2(n):
    """d2 章类 → chapter（^第X章；其他有子）；编/篇 → part(2) 排除"""
    if n['level'] == 2 and BUAN_RE.match(n['label']):
        return False
    if n['level'] == 2 and (ZHANG_RE.match(n['label']) or (n['children'] and not NUM_HEAD.match(n['label']))):
        return True
    return False

def is_chapter(n):
    if n['level'] == 1 and not is_part1(n):
        return True
    if is_ch2(n):
        return True
    # d3 章（资本论三卷的章，如"第一章 商品"）→ chapter
    if n['level'] == 3 and ZHANG_RE.match(n['label']):
        return True
    return False

part_labels = []
for n in flat:
    if n['level'] == 0 and n['label'] != '总目录':
        part_labels.append(norm(n['label']))
    if is_part1(n) or is_part2(n):
        part_labels.append(norm(n['label']))
part_labels.append(norm('总目录'))
print(f"ncx 条目: {len(flat)} | part 标题: {len(part_labels)}")

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

for i, node in enumerate(flat):
    # d0 卷 → part(0)；总目录 SKIP
    if node['level'] == 0:
        if node['label'] == '总目录':
            continue
        toc.append({"type": "part", "title": node['label'], "level": 0, "index": ch_index})
        continue
    # d1 册/篇 → part(1)
    if is_part1(node):
        toc.append({"type": "part", "title": node['label'], "level": 1, "index": ch_index})
        continue
    # d2 编/篇 → part(2)
    if is_part2(node):
        toc.append({"type": "part", "title": node['label'], "level": 2, "index": ch_index})
        continue
    # d2/d3/d4 节 → section（挂当前章 index）
    if node['level'] >= 2 and not is_chapter(node):
        toc.append({"type": "section", "title": node['label'],
                    "index": ch_index, "level": 2})
        continue
    # chapter（d1 文章 / d2 章）
    seq = seg_text(node['src'])
    if not seq:
        warns.append(f"!! 无锚点: {node['label']}")
        continue
    fi, bi = seq[0]
    nf, nb = next_split(i)
    if os.environ.get('DBG'):
        end_str = f"{htmls[nf]}:{nb}" if nf < len(htmls) else "END"
        print(f"  DBG [{node['label'][:20]}] {htmls[fi]}:{bi} → {end_str}")
    blocks = collect(fi, bi, nf, nb)
    while blocks and head_eq(blocks[0]["value"], node['label']):
        blocks = blocks[1:]
    keep = []
    for blk in blocks:
        if norm(blk["value"]) in part_labels:
            continue
        keep.append(blk)
    blocks = keep
    dedup = []
    for blk in blocks:
        if dedup and norm(dedup[-1]["value"]) == norm(blk["value"]):
            continue
        dedup.append(blk)
    if not dedup:
        warns.append(f"!! 空章节跳过: {node['label']} src={node['src']} 区间[{fi},{bi})-({nf},{nb})")
        continue
    title = re.sub(r'\d+$', '', node['label'])
    toc.append({"type": "chapter", "title": title, "index": ch_index, "level": 1})
    files[ch_index] = {"index": ch_index, "title": title, "content": dedup}
    ch_index += 1

print(f"\n章节总数: {len(files)} | toc 条目: {len(toc)}")
print(f"警告: {len(warns)}")
for w in warns:
    print("⚠", w)
total_chars = 0
for idx, ch in files.items():
    nc = sum(len(b['value']) for b in ch['content'])
    total_chars += nc
print(f"\n总: {len(files)} 章, {total_chars} 字符（旧 6,565,573）")
if os.environ.get('DBG'):
    # 打印第 9 卷全部 chapter 字数
    for idx, ch in files.items():
        if 277 <= idx < 293:
            nc = sum(len(b['value']) for b in ch['content'])
            print(f"  [{idx}] {ch['title'][:30]} {nc}字")
# 按卷（part0）累计字数
vols = [(tt['title'], tt['index']) for tt in toc if tt['type'] == 'part' and tt['level'] == 0]
for vi, (vname, vstart) in enumerate(vols):
    vend = vols[vi + 1][1] if vi + 1 < len(vols) else len(files)
    vsum = sum(sum(len(b['value']) for b in files[i]['content']) for i in range(vstart, vend) if i in files)
    print(f"  卷{vi+1} {vname[:14]}: [{vstart},{vend}) {vsum}字")
for tt in toc:
    if tt['type'] == 'part':
        print(("  " * tt['level']) + f"[{tt['level']}] {tt['title'][:30]}")
print(f"toc 类型统计: part0={sum(1 for t in toc if t['type']=='part' and t['level']==0)} "
      f"part1={sum(1 for t in toc if t['type']=='part' and t['level']==1)} "
      f"part2={sum(1 for t in toc if t['type']=='part' and t['level']==2)} "
      f"chapter={sum(1 for t in toc if t['type']=='chapter')} "
      f"section={sum(1 for t in toc if t['type']=='section')}")

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
    "bookId": old_meta.get("bookId") or "7729ccdecb0f",
    "title": old_meta.get("title") or "马克思恩格斯文集",
    "author": old_meta.get("author") or "卡尔·马克思、弗里德里希·恩格斯",
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
