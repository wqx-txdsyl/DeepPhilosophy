# -*- coding: utf-8 -*-
"""历史主义贫困论 d54046539e0d 按 epub ncx 重建（一次性，一~四=chapter，数字节=section）
epub: 卡尔·波普尔/历史主义贫困论.epub  ncx 44 条（全平，filepos 锚点）
映射: d0 匹配"^[一二三四]　"（四学说）=chapter，d0 匹配"^\\d+\\."（1-33 节）=section 归其下，
      导论/附录/译名对照表=独立 chapter；跳过 封面/书名页/版权页/目录
用法: python _xr_popper_rebuild.py [--dry]
"""
import zipfile, re, json, os, sys, html as html_mod, shutil, bisect

EP = 'F:/philosophy/西方/卡尔·波普尔/历史主义贫困论.epub'
SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters/d54046539e0d"
DST = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/d54046539e0d"
SKIP = {"封面", "书名页", "版权页", "目录", "总目录", "版权"}

z = zipfile.ZipFile(EP)
NCX = [n for n in z.namelist() if n.endswith('.ncx')][0]
PREFIX = NCX.rsplit('/', 1)[0] + '/' if '/' in NCX else ''

def norm(s):
    return re.sub(r"\s+", "", s or "")

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
flat = [n for n in tree]
ALL_LABELS = {norm(n['label']) for n in flat}
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

# ────────── 组装：四学说=chapter，数字节=section ──────────
R_PART = re.compile(r'^[一二三四五六七八九十]　')   # 一　历史主义的反自然主义学说
R_SEC = re.compile(r'^\d+\.')                        # 1.概括
toc = []
files = {}
ch_index = 0
warns = []
cur = None  # {title, start, secs}

def flush(end):
    global cur, ch_index
    if cur is None:
        return
    fi, bi = cur['start']
    end_fi, end_bi = end
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
    while blocks and norm(blocks[0]["value"]) != norm(cur['title']) and norm(blocks[0]["value"]) in ALL_LABELS:
        blocks = blocks[1:]  # 目录页残行（等于其他 ncx 条目标题）
    if blocks and norm(blocks[0]["value"]) == norm(cur['title']):
        blocks = blocks[1:]
    dedup = []
    for blk in blocks:
        if dedup and norm(dedup[-1]["value"]) == norm(blk["value"]):
            continue
        dedup.append(blk)
    if not dedup:
        warns.append(f"!! 空章节: {cur['title']}")
    toc.append({"type": "chapter", "title": cur['title'], "index": ch_index, "level": 1})
    for sn in cur['secs']:
        toc.append({"type": "section", "title": sn, "index": ch_index, "level": 2})
    files[ch_index] = {"index": ch_index, "title": cur['title'], "content": dedup}
    ch_index += 1
    cur = None

for node in flat:
    if norm(node['label']) in SKIP:
        continue
    seq = seg_text(node['src'])
    if not seq:
        warns.append(f"!! 无锚点: {node['label']} ({node['src']})")
        continue
    label = node['label']
    if R_SEC.match(label):
        # 数字节 → 挂当前 chapter 的 section（不切分内容）
        if cur is not None:
            cur['secs'].append(label)
        else:
            warns.append(f"!! 节无归属章: {label}")
        continue
    # 新 chapter（四学说/导论/附录/译名对照表）
    flush(seq[0])
    cur = {'title': label, 'start': seq[0], 'secs': []}
flush((len(htmls), 0))

print(f"\n章节总数: {len(files)} | toc 条目: {len(toc)}")
print(f"警告: {len(warns)}")
for w in warns:
    print("⚠", w)
for idx, ch in files.items():
    nb = len(ch['content']); nc = sum(len(b['value']) for b in ch['content'])
    first = ch['content'][0]['value'][:30] if ch['content'] else '(空)'
    print(f"  [{idx}] {ch['title'][:24]} {nb}块 {nc}字 | {first}…")
total_chars = sum(sum(len(b['value']) for b in ch['content']) for ch in files.values())
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
    "bookId": old_meta.get("bookId") or "d54046539e0d",
    "title": old_meta.get("title") or "历史主义贫困论",
    "author": old_meta.get("author") or "卡尔·波普尔",
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
