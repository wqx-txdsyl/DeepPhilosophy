# -*- coding: utf-8 -*-
"""快乐主义 10c315f073ef 重建（一次性，ncx 顶层=part+chapter，文件边界切分）
epub: 快乐主义.epub（西方/伊壁鸠鲁/）
ncx 顶层 9 条：版权信息/卷一 快乐是生活的终极目标/致美诺西斯的信/主要学说/梵蒂冈箴言录/
               卷二 快乐是理性思考的结果/致希罗多德的信/致皮托克勒的信/伊壁鸠鲁：花园中的哲人
旧数据 6 章 = 6 部作品平铺，卷一/卷二 part 丢失；
混入相邻内容（卷二标题残影"快 乐 是 理 性 思 考 的 结 果"、"[全书完]"、出版信息页）、多章首块空。
结构:
  SKIP: 版权信息条目 + guomaipage-5.xhtml（出版信息页，从 htmls 排除）
  part × 2（卷一/卷二, level 0, index=首章 index；卷页空壳仅"卷一"二字, tail_skip 自动过滤）
  chapter × 6（六部作品, level 1）
  切分: 文件边界（每作品独立文件）
  剥标题: strip_title 串联累加（各作品首块=作品标题）
用法: python _xr_kuaile_rebuild.py [--dry]
"""
import zipfile, re, json, os, sys, html as html_mod, shutil

EP = 'F:/philosophy/西方/伊壁鸠鲁/快乐主义.epub'
SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters/10c315f073ef"
DST = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/10c315f073ef"

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
    }

roots = build_tree()
for r in roots:
    info = node_info(r)
    info['children'] = []
    r['info'] = info
flat = [r['info'] for r in roots]
print(f"ncx 顶层: {len(flat)}")

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
    return blocks

htmls = sorted((n for n in z.namelist() if n.endswith(('.html', '.xhtml'))),
               key=lambda n: [int(x) if x.isdigit() else x for x in re.split(r'(\d+)', n)])
# 排除出版信息页（非正文）
htmls = [f for f in htmls if 'guomaipage' not in f]
blocks_by_file = {}
for f in htmls:
    blocks_by_file[f] = extract_blocks(f)
print(f"html 文件: {len(htmls)}")

def tail_skip(fname):
    bl = blocks_by_file[fname]
    t2 = ''.join(b[1] for b in bl)
    if len(t2) <= 12:
        return True                          # 空壳（卷标题页/分割页）
    if 'Table of Contents' in t2 or 'Landmarks' in t2:
        return True
    if '@page' in t2 or re.search(r'body\s*\{', t2):
        return True
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
    for node2 in flat[node_i + 1:]:
        src = node2['src']
        f, _, _ = src.partition('#')
        if PREFIX and f.startswith(PREFIX):
            pass
        elif PREFIX:
            f = PREFIX + f
        if f in htmls:
            return (htmls.index(f), 0)
    return (len(htmls), 0)

def strip_title(blocks, label):
    """串联累加剥章首标题块（各作品首块=作品标题）"""
    nl = norm(label)
    acc = ''
    i = 0
    while i < len(blocks):
        v = norm(blocks[i]['value'])
        if not v:
            i += 1
            continue
        nacc = acc + v
        if nl.startswith(nacc):
            i += 1
            acc = nacc
            if acc == nl:
                break
        elif nacc and nl.endswith(nacc) and i == 0:
            i += 1
            acc = nacc
            if acc == nl:
                break
        else:
            break
    return blocks[i:]

PART_PREFIXES = ('卷一', '卷二')

toc = []
files = {}
warns = []
ch_index = 0

for i, node in enumerate(flat):
    src = node['src']
    f, _, _ = src.partition('#')
    if PREFIX and f.startswith(PREFIX):
        pass
    elif PREFIX:
        f = PREFIX + f
    if f not in htmls:
        warns.append(f"!! 无文件: {node['label']} → {src}")
        continue
    fi = htmls.index(f)
    if norm(node['label']).startswith(norm('版权信息')):
        print(f"skip: {node['label']}")
        continue
    if node['label'].startswith(PART_PREFIXES):
        # part 条目：卷页空壳（tail_skip 过滤），toc 挂 part
        nf, nb = next_split(i)
        blocks = collect(fi, 0, nf, nb)
        if blocks:
            warns.append(f"!! part 卷页含正文? {node['label']} {len(blocks)} 块")
        toc.append({"type": "part", "title": node['label'], "index": ch_index, "level": 0})
        print(f"part: {node['label']}（index={ch_index}, 空壳卷页无正文）")
        continue
    nf, nb = next_split(i)
    blocks = collect(fi, 0, nf, nb)
    blocks = strip_title(blocks, node['label'])
    if not blocks:
        warns.append(f"!! 空章节跳过: {node['label']}")
        continue
    toc.append({"type": "chapter", "title": node['label'], "index": ch_index, "level": 1})
    files[ch_index] = {"index": ch_index, "title": node['label'], "content": blocks}
    ch_index += 1

print(f"\n章节总数: {len(files)} | toc 条目: {len(toc)} | 警告: {len(warns)}")
for w in warns:
    print("⚠", w)
total_chars = 0
for idx, ch in files.items():
    nc = sum(len(b['value']) for b in ch['content'])
    total_chars += nc
    print(f"  {idx:2d} {ch['title'][:30]:32s} {nc:7d} 字")
print(f"\n总: {len(files)} 章, {total_chars} 字符（源正文 47748, 旧 49684）")
for tt in toc:
    ind = ' ' * 2 * tt.get('level', 1)
    print(f"{ind}[{tt['type']} {tt.get('sec','')}] {tt['title'][:40]}")
print("标题首:", files[0]['title'], "| 末:", files[len(files) - 1]['title'])
for idx, ch in files.items():
    print(f"首块[{ch['title'][:12]}]:", ch['content'][0]['value'][:32])

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
    "bookId": old_meta.get("bookId") or "10c315f073ef",
    "title": old_meta.get("title") or "快乐主义",
    "author": old_meta.get("author") or "伊壁鸠鲁",
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
