# -*- coding: utf-8 -*-
"""沙发上的哲学家 1712b01d0856 重建（一次性，ncx 锚点切分，章+节两级）
epub: 沙发上的哲学家.epub（西方/里克·杜菲尔/）
ncx 顶层 14 条：版权页/目录/导论/第一章~第八章/结语/专业词汇/译名对照表
旧数据 13 章 = 版权页 + 12 章（缺"导论"，第一章~第八章的"第X章"标题全丢只剩节标题）
结构:
  SKIP: 版权页/目录
  chapter × 12: 导论 / 第一章~第八章 / 结语 / 专业词汇 / 译名对照表（ncx 顶层, level 1）
  section × 9: 导论下的"哲学是我最喜欢的电视剧" + 每章 1 节（ncx 子级, level 2,
               index=所属章 index, sec=章内序号, 内容并入所属章不单独切分）
用法: python _xr_shafa_philosopher_rebuild.py [--dry]
"""
import zipfile, re, json, os, sys, html as html_mod, shutil, bisect

EP = 'F:/philosophy/西方/里克·杜菲尔/沙发上的哲学家.epub'
SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters/1712b01d0856"
DST = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/1712b01d0856"
SKIP = {"版权页", "目录"}

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
print(f"ncx 条目: {len(flat)}（顶层 {len(tree)}）")

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
    raw = []
    ids = {}
    for m in re.finditer(r'<(p|table|h[1-6]|blockquote)[^>]*>(.*?)</\1>', h, re.S):
        tag, inner = m.group(1), m.group(2)
        if tag == 'p':
            text = el_text(inner)
        elif tag == 'table':
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', inner, re.S)
            text = '  '.join(
                '  '.join(el_text(c) for c in re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', r, re.S))
                for r in rows)
        else:
            text = el_text(inner)
        if text:
            raw.append([m.start(), m.end(), text])
    # 嵌套 blockquote 去重：外层包含内层且文本相同 → 丢外层
    raw.sort(key=lambda x: (x[0], x[1]))
    drop = set()
    for i in range(len(raw)):
        for j in range(i + 1, len(raw)):
            if raw[j][0] >= raw[i][1]:
                break
            if raw[j][1] <= raw[i][1] and raw[j][2] == raw[i][2]:
                drop.add(i)
                break
    blocks = [(raw[k][0], raw[k][2]) for k in range(len(raw)) if k not in drop]
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

def tail_skip(fname):
    """尾部垃圾文件（书名页/目录页/CSS 页）——最后一章收集到文件尾时过滤"""
    bl = blocks_by_file[fname]
    t = ''.join(b[1] for b in bl)
    if len(t) <= 12:
        return True                          # 书名页（如"沙发上的哲学家"）
    if 'Table of Contents' in t:
        return True                          # 重复目录页
    if '@page' in t or re.search(r'body\s*\{', t):
        return True                          # CSS 样式页
    return False

def collect(fi, bi, end_fi, end_bi):
    blocks = []
    for kf in range(fi, end_fi + 1):
        if kf >= len(htmls):
            break
        if tail_skip(htmls[kf]):
            continue
        bl = blocks_by_file[htmls[kf]]
        start = bi if kf == fi else 0
        e = end_bi if kf == end_fi else len(bl)
        for kbi in range(start, e):
            blocks.append({"type": "text", "value": bl[kbi][1]})
    return blocks

def next_split(node_i):
    """找下一个顶层（level==0）条目的锚点"""
    for node2 in flat[node_i + 1:]:
        if node2['level'] != 0 or node2['label'] in SKIP:
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
warns = []
ch_index = 0

for node in flat:
    if node['level'] != 0:
        continue
    if node['label'] in SKIP:
        continue
    # chapter（ncx 顶层）
    seq = seg_text(node['src'])
    if not seq:
        warns.append(f"!! 无锚点: {node['label']}")
        continue
    fi, bi = seq[0]
    nf, nb = next_split(flat.index(node))
    blocks = collect(fi, bi, nf, nb)
    while blocks and head_eq(blocks[0]["value"], node['label']):
        blocks = blocks[1:]
    if not blocks:
        warns.append(f"!! 空章节跳过: {node['label']}")
        continue
    toc.append({"type": "chapter", "title": node['label'], "index": ch_index, "level": 1})
    files[ch_index] = {"index": ch_index, "title": node['label'], "content": blocks}
    ch_index += 1
    # section（ncx 子级，内容并入所属章）
    for sec_i, child in enumerate(node['children'], 1):
        if not child['label']:
            continue
        toc.append({"type": "section", "title": child['label'],
                    "index": ch_index - 1, "sec": sec_i, "level": 2})

print(f"\n章节总数: {len(files)} | toc 条目: {len(toc)} | 警告: {len(warns)}")
for w in warns:
    print("⚠", w)
total_chars = 0
for idx, ch in files.items():
    nc = sum(len(b['value']) for b in ch['content'])
    total_chars += nc
    print(f"  {idx:2d} {ch['title'][:30]:32s} {nc:7d} 字")
print(f"\n总: {len(files)} 章, {total_chars} 字符（旧 13 章含版权页）")
for tt in toc:
    ind = ' ' * 2 * (tt.get('level', 1) - 1)
    print(f"{ind}[{tt['type']} {tt.get('sec','')}] {tt['title'][:40]}")
print("标题前3:", [files[i]['title'][:24] for i in range(3)])
print("标题末3:", [files[i]['title'][:24] for i in range(len(files) - 3, len(files))])

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
    "bookId": old_meta.get("bookId") or "1712b01d0856",
    "title": old_meta.get("title") or "沙发上的哲学家",
    "author": old_meta.get("author") or "里克·杜菲尔",
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
