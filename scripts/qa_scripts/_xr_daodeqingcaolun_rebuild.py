# -*- coding: utf-8 -*-
"""道德情操论 21a479c4978d 重建（一次性，ncx 锚点切分，篇/章标题缺失修复）
epub: 道德情操论.epub  ncx 79 条（d0 14 + d1 25 + d2 40）
旧数据 45 章问题: 第二篇/第六篇/第七篇 篇标题缺失、第一篇第一章(论合宜感)/第二篇第三章/
  第六篇第二章/第七篇第二三章 章标题缺失、前折页/版权页/后折页垃圾页
结构:
  d0 篇(part level0) 7 个；译者序/告读者/结论 → chapter；前折页/书名页/版权页/目录 SKIP
  d1 章 → chapter（11 个）
  d2 节 → section(level2)（40 个，标题块保留在章内容中）
用法: python _xr_daodeqingcaolun_rebuild.py [--dry]
"""
import zipfile, re, json, os, sys, html as html_mod, shutil, bisect

EP = 'F:/philosophy/西方/亚当·斯密/道德情操论.epub'
SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters/21a479c4978d"
DST = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/21a479c4978d"
SKIP = {"前折页", "书名页", "版权页", "目录", "后折页"}

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
# 预处理：无章之篇（子全为节）→ 篇整体降级为 chapter（next_split 需提前知道）
for n in flat:
    if n['level'] == 0 and n['children']:
        n['_as_chapter'] = not any(c['children'] for c in n['children'])
part_labels = [norm(n['label']) for n in flat
               if n['level'] == 0 and n['children'] and not n['_as_chapter']]
part_labels += [norm(s) for s in SKIP]
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

def is_section_like(n):
    """d1 无子节点时：'第X节'/'引言' → section；'第X章'/其他 → chapter"""
    if n['level'] != 1 or n['children']:
        return False
    return bool(re.match(r'^第[一二三四五六七八九十百]+节', n['label'])) or n['label'] == '引言'

def is_chapter(n):
    if n.get('_as_chapter', False):
        return True
    if n['level'] == 0 and not n['children'] and n['label'] not in SKIP:
        return True
    if n['level'] == 1 and not is_section_like(n):
        return True
    return False

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

part_index = None  # 最近一个 part 的 index（=其下第一个 chapter）
for i, node in enumerate(flat):
    # SKIP（前折页/书名页/版权页/目录/后折页）
    if node['label'] in SKIP:
        continue
    # part（d0 篇）；无章之篇（子全为节）→ 篇整体降级为 chapter
    if node['level'] == 0 and node['children']:
        if node['_as_chapter']:
            pass  # 落入 chapter 分支
        else:
            toc.append({"type": "part", "title": node['label'], "level": 0, "index": ch_index})
            part_index = ch_index
            continue
    # section（d2 节 / d1 节类）
    if node['level'] >= 2 or is_section_like(node):
        toc.append({"type": "section", "title": node['label'],
                    "index": ch_index if part_index is None else part_index, "level": 2})
        continue
    # chapter（d1 章 / d0 译者序告读者结论）
    seq = seg_text(node['src'])
    if not seq:
        warns.append(f"!! 无锚点: {node['label']}")
        continue
    fi, bi = seq[0]
    nf, nb = next_split(i)
    if os.environ.get('DBG'):
        print(f"  DBG [{node['label'][:20]}] {htmls[fi]}:{bi} → {htmls[nf]}:{nb}")
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
    print(f"  [{idx}] {ch['title'][:34]} {len(ch['content'])}块 {nc}字 | {first}…")
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
    "bookId": old_meta.get("bookId") or "21a479c4978d",
    "title": old_meta.get("title") or "道德情操论",
    "author": old_meta.get("author") or "亚当·斯密",
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
