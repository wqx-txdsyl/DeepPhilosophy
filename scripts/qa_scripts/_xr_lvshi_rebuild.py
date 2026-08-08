# -*- coding: utf-8 -*-
"""吕氏春秋 78687dc8052a 按 epub ncx 重建（一次性，纪/览/论=chapter，篇【】=section）
epub: 东方/吕不韦/吕氏春秋.epub  ncx 29 条（26 篇平铺，每篇一文件 Chapter417~442）
映射: 每纪/览/论=chapter（文件级）；文件内【篇名】块=section（toc 标记）；跳过 关于本书/目录/CoverPage
用法: python _xr_lvshi_rebuild.py [--dry]
"""
import zipfile, re, json, os, sys, html as html_mod, shutil

EP = 'F:/philosophy/东方/吕不韦/吕氏春秋.epub'
SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters/78687dc8052a"
DST = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/78687dc8052a"
SKIP = {"关于本书", "目录", "CoverPage", "封面", "版权", "版权页", "总目录"}

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

tree = decorate_roots = None

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
    return blocks

htmls = sorted((n for n in z.namelist() if n.endswith(('.html', '.xhtml'))),
               key=lambda n: [int(x) if x.isdigit() else x for x in re.split(r'(\d+)', n)])
blocks_by_file = {f: extract_blocks(f) for f in htmls}
print(f"html 文件: {len(htmls)}")

def seg_file(src):
    f, _, _ = src.partition('#')
    if PREFIX and f.startswith(PREFIX):
        pass
    elif PREFIX:
        f = PREFIX + f
    if f in htmls:
        return htmls.index(f)
    return -1

# ────────── 组装：纪/览/论=chapter（文件），【篇】=section ──────────
R_PIAN = re.compile(r'^【([^】]{1,14})】$')
toc = []
files = {}
ch_index = 0
warns = []

seq_all = []
for node in flat:
    if norm(node['label']) in SKIP:
        continue
    fi = seg_file(node['src'])
    if fi < 0:
        warns.append(f"!! 无文件: {node['label']} ({node['src']})")
        continue
    seq_all.append((fi, node['label']))
seq_all.sort(key=lambda x: x[0])
print(f"有效纪/览/论: {len(seq_all)}")

for i, (fi, label) in enumerate(seq_all):
    end_fi = seq_all[i + 1][0] if i + 1 < len(seq_all) else len(htmls)
    blocks = []
    for kf in range(fi, end_fi):
        if kf >= len(htmls):
            break
        for off, kind, text in blocks_by_file[htmls[kf]]:
            blocks.append({"type": "text", "value": text})
    if blocks and norm(blocks[0]["value"]) == norm(label):
        blocks = blocks[1:]
    dedup = []
    for blk in blocks:
        if dedup and norm(dedup[-1]["value"]) == norm(blk["value"]):
            continue
        dedup.append(blk)
    # 篇【】section
    secs = []
    for blk in dedup:
        m = R_PIAN.match(blk["value"])
        if m:
            secs.append(m.group(1))
    if not dedup:
        warns.append(f"!! 空章节: {label}")
    toc.append({"type": "chapter", "title": label, "index": ch_index, "level": 1})
    for sn in secs:
        toc.append({"type": "section", "title": sn, "index": ch_index, "level": 2})
    files[ch_index] = {"index": ch_index, "title": label, "content": dedup}
    ch_index += 1

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
    "bookId": old_meta.get("bookId") or "78687dc8052a",
    "title": old_meta.get("title") or "吕氏春秋",
    "author": old_meta.get("author") or "吕不韦",
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
