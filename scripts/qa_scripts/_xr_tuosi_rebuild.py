# -*- coding: utf-8 -*-
"""陀思妥耶夫斯基集（全九册）343df8697039 重建（一次性，ncx 锚点切分，481 章"一/二/三"平铺）
epub: 陀思妥耶夫斯基集（全九册）.epub  ncx 616 条（d0 69 / d1 220 / d2 327）
旧数据 481 章 = 节级"一/二/三"全平铺，作品/部/章标题全部丢失。
结构:
  作品 marker（d0 无子，7 部）→ part(0)
  d0 有子：'第X部' 有章子 → part(1)；子全为节 → 整部降级 chapter（同道德情操论无章之篇）
          '第X章'/'尾?声'/序文（子为节）→ chapter，子节 → section
  d0 无子：版权信息/世界名著名译文库总序 SKIP；作品 marker part(0)；其余（序/附录/译后记/篇目）→ chapter
  d1 有子 → chapter；d1 无子 '一/二' → section；'第X部/章' → chapter（无节章）
  d2 → section
  标题尾部页码后缀（如"第一章 地下室201"）→ 去除
用法: python _xr_tuosi_rebuild.py [--dry]
"""
import zipfile, re, json, os, sys, html as html_mod, shutil, bisect

EP = 'F:/philosophy/西方/费奥多尔·陀思妥耶夫斯基/陀思妥耶夫斯基集（全九册）.epub'
SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters/343df8697039"
DST = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/343df8697039"
SKIP = {"版权信息", "“世界名著名译文库”总序"}
WORKS = {"罪与罚", "白痴", "群魔", "卡拉马佐夫兄弟", "被侮辱与被损害的", "少年",
         "地下室手记：陀思妥耶夫斯基中篇小说选"}

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
CN_RE = re.compile(r'^第[一二三四五六七八九十百]+[部章]')
NUM_RE = re.compile(r'^[一二三四五六七八九十]+$')

def is_section_like(n):
    """节类：标题为纯数字（一/二/三）或长标题且无子，且非 部/章 标题"""
    if n['children']:
        return False
    if CN_RE.match(n['label']):
        return False
    return True

# 预处理：d0 有子节点的分类（部/章/序文）
for n in flat:
    if n['level'] == 0 and n['children']:
        n['_as_chapter'] = all(is_section_like(c) for c in n['children'])
    else:
        n['_as_chapter'] = False
part_labels = [norm(n['label']) for n in flat
               if n['level'] == 0 and n['children'] and not n['_as_chapter']]
part_labels += [norm(s) for s in SKIP]
print(f"ncx 条目: {len(flat)} | part 候选: {len(part_labels)}")

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

def is_chapter(n):
    if n.get('_as_chapter', False):
        return True
    if n['level'] == 0:
        return not n['children'] and n['label'] not in SKIP and n['label'] not in WORKS
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
part_stack = []  # 最近 part 的 index

for i, node in enumerate(flat):
    if node['label'] in SKIP:
        continue
    # 作品 marker → part(0)
    if node['level'] == 0 and not node['children'] and node['label'] in WORKS:
        toc.append({"type": "part", "title": node['label'], "level": 0, "index": ch_index})
        part_stack.append(ch_index)
        continue
    # d0 有子：'第X部' 有章子 → part(1)；子全节 → 降级 chapter
    if node['level'] == 0 and node['children']:
        if node['_as_chapter']:
            pass  # 落入 chapter 分支
        else:
            toc.append({"type": "part", "title": node['label'], "level": 1, "index": ch_index})
            part_stack.append(ch_index)
            continue
    # section（d2 / d1 节类 / 降级部的节子）
    if node['level'] >= 2 or (node['level'] == 1 and is_section_like(node)):
        idx = part_stack[-1] if part_stack else ch_index
        toc.append({"type": "section", "title": node['label'], "index": idx, "level": 2})
        continue
    # chapter
    seq = seg_text(node['src'])
    if not seq:
        warns.append(f"!! 无锚点: {node['label']}")
        continue
    fi, bi = seq[0]
    nf, nb = next_split(i)
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
        warns.append(f"!! 空章节跳过: {node['label']} src={node['src']} 区间[{fi},{bi})-({nf},{nb}) 区间块{len(blocks)}")
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
print(f"\n总: {len(files)} 章, {total_chars} 字符")
# part 结构
for tt in toc:
    if tt['type'] == 'part':
        print(("  " * tt['level']) + f"[{tt['level']}] {tt['title']}")

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
    "bookId": old_meta.get("bookId") or "343df8697039",
    "title": old_meta.get("title") or "陀思妥耶夫斯基集（全九册）",
    "author": old_meta.get("author") or "费奥多尔·陀思妥耶夫斯基",
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
