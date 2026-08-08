# -*- coding: utf-8 -*-
"""幸福之路 921c1dcbdd17 重建（一次性，三书=part，章=chapter，繁体保留）
epub: 幸福之路.epub（繁体） ncx 58 条：d0=3 部（第一部分 不幸之源=幸福之路/
      第二部分 悠闲颂=婚姻与道德/第三部分 论教育），d1=章（每章一文件 chapter1~57）
映射: d0=part；d1=chapter（文件级切分）；跳过 封面
注: 第二部分 ncx 缺第十六章（第十五→第十七跳号，源缺失）；繁体原文保留
用法: python _xr_luoxi_rebuild.py [--dry]
"""
import zipfile, re, json, os, sys, html as html_mod, shutil

EP = 'F:/philosophy/西方/伯特兰·罗素/幸福之路.epub'
SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters/921c1dcbdd17"
DST = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/921c1dcbdd17"
SKIP = {"封面", "目录", "版权页", "书名页"}

z = zipfile.ZipFile(EP)
ncx = [n for n in z.namelist() if n.endswith('.ncx')][0]
PREFIX = ncx.rsplit('/', 1)[0] + '/' if '/' in ncx else ''

def norm(s):
    return re.sub(r"\s+", "", s or "")

t = z.read(ncx).decode('utf-8')
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

def decorate(nodes, level=0):
    out = []
    for node in nodes:
        info = node_info(node)
        info['level'] = level
        info['children'] = decorate(node['children'], level + 1)
        out.append(info)
    return out

tree = decorate(build_tree())
print(f"ncx 部数: {len(tree)}")

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
                blocks.append({"type": "text", "value": text})
        elif tag == 'table':
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', inner, re.S)
            for r in rows:
                cells = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', r, re.S)
                row_text = '  '.join(el_text(c) for c in cells)
                if row_text:
                    blocks.append({"type": "text", "value": row_text})
        elif tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            text = el_text(inner)
            if text:
                blocks.append({"type": "text", "value": text})
    return blocks

def seg_file(src):
    f, _, _ = src.partition('#')
    if PREFIX and f.startswith(PREFIX):
        pass
    elif PREFIX:
        f = PREFIX + f
    if f in htmls:
        return htmls.index(f)
    return -1

htmls = sorted((n for n in z.namelist() if n.endswith(('.html', '.xhtml'))),
               key=lambda n: [int(x) if x.isdigit() else x for x in re.split(r'(\d+)', n)])
blocks_by_file = {f: extract_blocks(f) for f in htmls}
print(f"html 文件: {len(htmls)}")

# ────────── 组装：部=part，章=chapter（文件级） ──────────
toc = []
files = {}
ch_index = 0
warns = []

seq_all = []  # (file_index, label, is_chapter)
for part in tree:
    if norm(part['label']) in {norm(k) for k in SKIP}:
        continue
    toc.append({"type": "part", "title": part['label'], "level": 0, "index": ch_index})
    for c in part['children']:
        if norm(c['label']) in {norm(k) for k in SKIP}:
            continue
        fi = seg_file(c['src'])
        if fi < 0:
            warns.append(f"!! 无文件: {c['label']} ({c['src']})")
            continue
        seq_all.append((fi, c['label'], norm(part['label'])))
seq_all.sort(key=lambda x: x[0])
print(f"有效章: {len(seq_all)}")

for i, (fi, label, part_nl) in enumerate(seq_all):
    end_fi = seq_all[i + 1][0] if i + 1 < len(seq_all) else len(htmls)
    blocks = []
    for kf in range(fi, end_fi):
        if kf >= len(htmls):
            break
        for blk in blocks_by_file[htmls[kf]]:
            blocks.append(blk)
    nl = norm(label)
    # 首块删除：part 重复标题块 + chapter 标题（可能连排）
    while True:
        if blocks and nl and norm(blocks[0]["value"]) == nl:
            blocks = blocks[1:]
            continue
        if blocks and part_nl and norm(blocks[0]["value"]) == part_nl:
            blocks = blocks[1:]
            continue
        break
    dedup = []
    for blk in blocks:
        if dedup and norm(dedup[-1]["value"]) == norm(blk["value"]):
            continue
        dedup.append(blk)
    if not dedup:
        warns.append(f"!! 空章节: {label}")
    toc.append({"type": "chapter", "title": label, "index": ch_index, "level": 1})
    files[ch_index] = {"index": ch_index, "title": label, "content": dedup}
    ch_index += 1

print(f"\n章节总数: {len(files)} | toc 条目: {len(toc)}")
print(f"警告: {len(warns)}")
for w in warns:
    print("⚠", w)
total_chars = 0
for idx, ch in files.items():
    nb = len(ch['content']); nc = sum(len(b['value']) for b in ch['content'])
    total_chars += nc
    first = ch['content'][0]['value'][:30] if ch['content'] else '(空)'
    print(f"  [{idx}] {ch['title'][:26]} {nb}块 {nc}字 | {first}…")
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
    "bookId": old_meta.get("bookId") or "921c1dcbdd17",
    "title": old_meta.get("title") or "幸福之路",
    "author": old_meta.get("author") or "伯特兰·罗素",
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
