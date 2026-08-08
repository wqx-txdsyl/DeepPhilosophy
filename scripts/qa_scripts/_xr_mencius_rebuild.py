# -*- coding: utf-8 -*-
"""孟子 dd03ec6572e7 按 epub ncx 重建（一次性，篇/章句/节 三级）
epub: 东方/孟子/孟子.epub  ncx 264 条（每节一文件，标题"梁惠王章句上·第一节"）
映射: 标题按·拆分——篇名=part（梁惠王/公孙丑/滕文公/离娄/万章/告子/尽心），
      章句（梁惠王章句上/下…）=chapter，节号=section；跳过 关于本书/目录
用法: python _xr_mencius_rebuild.py [--dry]
"""
import zipfile, re, json, os, sys, html as html_mod, shutil

EP = 'F:/philosophy/东方/孟子/孟子.epub'
SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters/dd03ec6572e7"
DST = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/dd03ec6572e7"
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

def decorate(nodes, level=0):
    out = []
    for node in nodes:
        info = node_info(node)
        info['level'] = level
        info['children'] = decorate(node['children'], level + 1)
        out.append(info)
    return out

tree = decorate(build_tree())
flat = [n for n in tree]  # 全平
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

# ────────── 组装：篇=part / 章句=chapter / 节=section ──────────
R_PIAN = re.compile(r'^(梁惠王|公孙丑|滕文公|离娄|万章|告子|尽心)')
R_JT = re.compile(r'^(梁惠王章句[上下]|公孙丑章句[上下]|滕文公章句[上下]|离娄章句[上下]|万章章句[上下]|告子章句[上下]|尽心章句[上下])·(.+)$')
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
print(f"有效节: {len(seq_all)}")

def flush_chapter(start_fi, title, secs, end_fi):
    global ch_index
    blocks = []
    for kf in range(start_fi, end_fi):
        if kf >= len(htmls):
            break
        for off, kind, text in blocks_by_file[htmls[kf]]:
            blocks.append({"type": "text", "value": text})
    if blocks and norm(blocks[0]["value"]) == norm(title):
        blocks = blocks[1:]
    dedup = []
    for blk in blocks:
        if dedup and norm(dedup[-1]["value"]) == norm(blk["value"]):
            continue
        dedup.append(blk)
    files[ch_index] = {"index": ch_index, "title": title, "content": dedup}
    toc.append({"type": "chapter", "title": title, "index": ch_index, "level": 1})
    for sn in secs:
        toc.append({"type": "section", "title": sn, "index": ch_index, "level": 2})
    ch_index += 1

cur_pian = None
cur_ch = None  # (start_fi, zhangju, [jie标题])
for i, (fi, label) in enumerate(seq_all):
    m = R_JT.match(label)
    if not m:
        warns.append(f"!! 无法解析: {label}")
        continue
    zhangju, jie = m.group(1), m.group(2)
    pian = R_PIAN.match(zhangju).group(1)
    if cur_pian != pian:
        if cur_pian is not None:
            toc.append({"type": "part", "title": cur_pian, "level": 0, "index": ch_index})
        cur_pian = pian
    if cur_ch is not None and cur_ch[1] != zhangju:
        # 章句切换：flush（终点 = 当前节文件）
        flush_chapter(cur_ch[0], cur_ch[1], cur_ch[2], fi)
        cur_ch = None
    if cur_ch is None:
        cur_ch = (fi, zhangju, [])
    cur_ch[2].append(jie)
if cur_pian is not None:
    toc.append({"type": "part", "title": cur_pian, "level": 0, "index": ch_index})
if cur_ch is not None:
    flush_chapter(cur_ch[0], cur_ch[1], cur_ch[2], len(htmls))

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
    "bookId": old_meta.get("bookId") or "dd03ec6572e7",
    "title": old_meta.get("title") or "孟子",
    "author": old_meta.get("author") or "孟子",
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
