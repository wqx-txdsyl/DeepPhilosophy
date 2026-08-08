# -*- coding: utf-8 -*-
"""心理学和炼金术 e63a26081cb9 重建（一次性，ncx 三层 part/chapter/section，文件边界切分）
epub: 心理学和炼金术.epub（西方/卡尔·古斯塔夫·荣格/）
ncx 10 条顶层：版权信息/目录/编委会/导读 点金石与自性化/炼金术的宗教与心理学问题导论/
              [part]炼金术中的宗教理念（子级: 第一章~第六章, 各带节）/尾声/译名对照表/译后记/注释
旧数据 6 章 = part 标题"炼金术中的宗教理念"当第一章（第一章 5125 字整个缺失）、
            part 层级丢失、第一~六章平铺、导读/导论/尾声/译后记全缺。
结构:
  SKIP: 版权信息/目录/编委会/译名对照表/注释
  part × 1（炼金术中的宗教理念, level 0, index=第一章 index, 无正文——标题页 split_000 47 字不收集）
  chapter × 9（导读/导论 + 第一~六章 + 尾声/译后记, level 1）
  section × 20（六章子级, level 2, index=所属章 index, sec=章内序号, 内容并入所属章）
  切分: 文件边界（下一"不同文件"条目, 子级同文件锚点跳过；第一章 = split_001+part0006+part0007）
  剥标题: strip_title 串联累加（章首标题块）+ 节标题块级精确匹配剥离（norm 全等, ≥4 字）
用法: python _xr_xlxj_rebuild.py [--dry]
"""
import zipfile, re, json, os, sys, html as html_mod, shutil

EP = 'F:/philosophy/西方/卡尔·古斯塔夫·荣格/心理学和炼金术.epub'
SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters/e63a26081cb9"
DST = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/e63a26081cb9"

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
flat = []
def flatten(nodes):
    for n in nodes:
        flat.append(n)
        flatten(n['children'])
flatten(tree)
print(f"ncx 条目: {len(flat)}（顶层 {len(tree)}，含子级）")

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

def resolve_fname(src):
    f, _, _ = src.partition('#')
    if PREFIX and f.startswith(PREFIX):
        return f
    elif PREFIX:
        return PREFIX + f
    return f

htmls_by_name = sorted((n for n in z.namelist() if n.endswith(('.html', '.xhtml'))),
                       key=lambda n: [int(x) if x.isdigit() else x for x in re.split(r'(\d+)', n)])
# 按 ncx 全序（含子级）构建文件列表——子级条目（第一~六章/节）的文件也在书脊顺序里，
# 只按顶层会把这些 split 文件排到尾声之后，第六章区间起点反超终点
htmls = []
seen = set()
for node in flat:
    f = resolve_fname(node['src'])
    if f in htmls_by_name and f not in seen:
        htmls.append(f)
        seen.add(f)
for f in htmls_by_name:
    if f not in seen:
        htmls.append(f)
        seen.add(f)
blocks_by_file = {}
for f in htmls:
    blocks_by_file[f] = extract_blocks(f)
print(f"html 文件: {len(htmls)}（按 ncx 顶层顺序）")

def tail_skip(fname):
    bl = blocks_by_file[fname]
    t2 = ''.join(b[1] for b in bl)
    if len(t2) <= 12:
        return True
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

def next_split(i):
    """下一章边界 = 下一'level≤1 且不同文件'条目（section 锚点是节首文件，不是章边界——跳过；
    SKIP 条目文件仍是有效边界）"""
    cur = resolve_fname(flat[i]['src'])
    for node2 in flat[i + 1:]:
        if node2['level'] >= 2:
            continue
        f = resolve_fname(node2['src'])
        if f != cur and f in htmls:
            return (htmls.index(f), 0)
    return (len(htmls), 0)

def strip_title(blocks, label, sections):
    """① 串联累加剥章首标题块 → ② 节标题块级精确匹配剥离"""
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
    sec_norms = {norm(s) for s in sections if len(norm(s)) >= 4}
    out = []
    dropped = []
    for b in blocks[i:]:
        if norm(b['value']) in sec_norms:
            dropped.append(b['value'])
            continue
        out.append(b)
    return out, dropped

SKIP_N = [norm(s) for s in ('版权信息', '目录', '编委会', '译名对照表', '注释')]

toc = []
files = {}
warns = []
ch_index = 0
all_dropped = []
pending_parts = []
sec_count = 0

def resolve_parts():
    while pending_parts:
        toc.append({"type": "part", "title": pending_parts.pop(0), "index": ch_index, "level": 0})

for i, node in enumerate(flat):
    lv = node['level']
    if lv == 2:
        continue  # section 在所属章处理时收集
    f = resolve_fname(node['src'])
    nl = norm(node['label'])
    if nl in SKIP_N:
        print(f"skip: {node['label']}")
        continue
    if lv == 0 and node['children']:
        pending_parts.append(node['label'])
        print(f"part 待定: {node['label']}（{len(node['children'])} 章）")
        continue
    if f not in htmls:
        warns.append(f"!! 无文件: {node['label']} → {node['src']}")
        continue
    fi = htmls.index(f)
    nf, nb = next_split(i)
    blocks = collect(fi, 0, nf, nb)
    sections = [c['label'] for c in node['children']]
    blocks, dropped = strip_title(blocks, node['label'], sections)
    all_dropped.extend((node['label'], d) for d in dropped)
    if not blocks:
        warns.append(f"!! 空章节跳过: {node['label']}")
        continue
    resolve_parts()
    toc.append({"type": "chapter", "title": node['label'], "index": ch_index, "level": 1})
    for k, sl in enumerate(sections, 1):
        toc.append({"type": "section", "title": sl, "index": ch_index, "sec": k, "level": 2})
        sec_count += 1
    files[ch_index] = {"index": ch_index, "title": node['label'], "content": blocks}
    ch_index += 1
if pending_parts:
    warns.append(f"!! part 无后继章: {pending_parts}")

print(f"\n章节总数: {len(files)} | toc 条目: {len(toc)}（part {sum(1 for tt in toc if tt['type']=='part')} + chapter {len(files)} + section {sec_count}）| 警告: {len(warns)}")
for w in warns:
    print("⚠", w)
print("\n被剥的节标题块:")
for ch, d in all_dropped:
    print(f"  [{ch[:18]}] {d!r}")
total_chars = 0
for idx, ch in files.items():
    nc = sum(len(b['value']) for b in ch['content'])
    total_chars += nc
    print(f"  {idx:2d} {ch['title'][:32]:34s} {nc:7d} 字")
print(f"\n总: {len(files)} 章, {total_chars} 字符（旧 6 章）")
for tt in toc:
    ind = ' ' * 2 * tt.get('level', 1)
    print(f"{ind}[{tt['type']} {tt.get('sec','')}] {tt['title'][:40]}")
print("标题首:", files[0]['title'], "| 末:", files[len(files) - 1]['title'])
for tgt in ('导读 点金石与自性化', '第一章 炼金术的基本概念', '第二章 炼金工作的精神本性', '第六章 炼金术在宗教史中的象征作用', '译后记'):
    for idx, ch in files.items():
        if ch['title'] == tgt:
            print(f"首块[{tgt[:14]}]:", ch['content'][0]['value'][:36])
            break

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
    "bookId": old_meta.get("bookId") or "e63a26081cb9",
    "title": old_meta.get("title") or "心理学和炼金术",
    "author": old_meta.get("author") or "卡尔·古斯塔夫·荣格",
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
