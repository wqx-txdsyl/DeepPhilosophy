# -*- coding: utf-8 -*-
"""写给每个人的哲学书 98e830eac187 按 epub ncx 重建（一次性，上/下篇包裹）
epub: 雅斯贝尔斯 14 堂哲学思维课.epub  ncx 18 条（全平）
映射: 自定义——d0 匹配"上篇/下篇"=part，其他 d0=chapter（第X讲/译者序），d1=section
      跳过 版权
用法: python _xr_utopia_rebuild.py [--dry]
"""
import zipfile, re, json, os, sys, html as html_mod, shutil, bisect

EP = 'F:/philosophy/西方/卡尔·雅斯贝尔斯/写给每个人的哲学书：雅斯贝尔斯的14堂哲学思维课.epub'
SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters/98e830eac187"
DST = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/98e830eac187"
SKIP = {"版权信息", "版权", "版权页", "目录", "封面", "总目录"}

z = zipfile.ZipFile(EP)
NCX = [n for n in z.namelist() if n.endswith('.ncx')][0]
PREFIX = NCX.rsplit('/', 1)[0] + '/' if '/' in NCX else ''

def norm(s):
    return re.sub(r"\s+", "", s or "")

# ────────── 1. ncx 树 ──────────
t = z.read(NCX).decode('utf-8')
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
    lb = re.search(r'<text>(.*?)</text>', seg)
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

# ────────── 2. 文本提取 ──────────
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
        tag, attrs, inner = m.group(1), m.group(2), m.group(3)
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

# ────────── 3. 组装（上篇/下篇 → part 包裹） ──────────
R_VOL = re.compile(r'^(上篇|下篇)')
toc = []
files = {}
ch_index = 0
warns = []

for node in tree:  # 全部 d0 平铺
    if norm(node['label']) in SKIP:
        continue
    if R_VOL.match(node['label']):
        # 篇标题页无正文，只做 part 标记
        toc.append({"type": "part", "title": node['label'], "level": 0, "index": ch_index})
        continue
    seq = seg_text(node['src'])
    if not seq:
        warns.append(f"!! 无锚点: {node['label']} ({node['src']})")
        continue
    fi, bi = seq[0]
    end_fi, end_bi = None, None
    idx_flat = flat.index(node) if node in flat else -1
    for f2 in flat[idx_flat + 1:]:
        if f2["level"] == 0 and norm(f2["label"]) not in SKIP:
            s2 = seg_text(f2['src'])
            if s2:
                end_fi, end_bi = s2[0]
                break
    if end_fi is None:
        end_fi, end_bi = len(htmls), 0
    blocks = []
    for kf in range(fi, end_fi + 1):
        if kf >= len(htmls):
            break
        bl = blocks_by_file[htmls[kf]]
        start = bi if kf == fi else 0
        end = end_bi if kf == end_fi else len(bl)
        for kbi in range(start, end):
            off, kind, text = bl[kbi]
            blocks.append({"type": "text", "value": text})
    if blocks and norm(blocks[0]["value"]) == norm(node['label']):
        blocks = blocks[1:]
    if not blocks:
        warns.append(f"!! 空章节: {node['label']} ({node['src']})")
    dedup = []
    for blk in blocks:
        if dedup and norm(dedup[-1]["value"]) == norm(blk["value"]):
            continue
        dedup.append(blk)
    blocks = dedup
    secs = []
    for s in node['children']:
        secs.append({"type": "section", "title": s['label'], "index": ch_index, "level": 2})
    toc.append({"type": "chapter", "title": node['label'], "index": ch_index, "level": 1})
    toc.extend(secs)
    files[ch_index] = {"index": ch_index, "title": node['label'], "content": blocks}
    ch_index += 1

print(f"\n章节总数: {len(files)} | toc 条目: {len(toc)}")
print(f"警告: {len(warns)}")
for w in warns:
    print("⚠", w)

total_blocks = sum(len(ch['content']) for ch in files.values())
total_chars = sum(sum(len(b['value']) for b in ch['content']) for ch in files.values())
print(f"\n总: {len(files)} 章, {total_blocks} 块, {total_chars} 字符")
for idx, ch in files.items():
    nb = len(ch['content']); nc = sum(len(b['value']) for b in ch['content'])
    first = ch['content'][0]['value'][:38] if ch['content'] else '(空)'
    print(f"  [{idx}] {ch['title'][:38]} {nb}块 {nc}字 | {first}…")

if '--dry' in sys.argv:
    sys.exit(0)

# ────────── 4. 备份 + 写盘 ──────────
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
    "bookId": old_meta.get("bookId") or "86ed11857f43",
    "title": old_meta.get("title") or "乌托邦",
    "author": old_meta.get("author") or "托马斯·莫尔",
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
