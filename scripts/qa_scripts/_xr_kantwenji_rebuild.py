# -*- coding: utf-8 -*-
"""康德文集（注释版·套装共10册）390398aff8d0 重建（一次性，册=part/著作=chapter/部卷=section）
epub: 康德文集.epub  ncx 457 条 6 级（d0=10 册，d1=109 著作，d2=156 部卷，d3+ 更深）
拼接标题恢复: 此 epub 父节点标题 = 自身标题 + 各子标题拼接（label 以每个 child.label 结尾，
              逐个去掉后缀即恢复自身标题，如 d1"第一部先验要素论…第二章论时间第二部分…"
              → "第一部先验要素论"）
映射: d0=part（册）；d1=chapter（著作）；d2=section（部/卷）；d3+ 只入内容
      跳过 总目录/版权信息/目录CONTENTS
用法: python _xr_kantwenji_rebuild.py [--dry]
"""
import zipfile, re, json, os, sys, html as html_mod, shutil, bisect

EP = 'F:/philosophy/西方/伊曼努尔·康德/康德文集.epub'
SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters/390398aff8d0"
DST = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/390398aff8d0"
SKIP = {"总目录", "版权信息", "目录CONTENTS", "目录"}

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

def self_title(label, children):
    """拼接标题恢复: label 依次去掉 children label 后缀（子标题拼接）"""
    out = label
    for _ in range(len(children)):
        changed = False
        for ch in children:
            if out.endswith(ch['label']):
                out = out[: -len(ch['label'])]
                changed = True
        if not changed:
            break
    return out.strip() or label

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
        info['title'] = self_title(info['label'], info['children'])
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

SKIP_NORMS = {norm(k) for k in SKIP}

def collect(fi, bi, end_fi, end_bi):
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
    return blocks

def next_split(node_i):
    for node2 in flat[node_i + 1:]:
        if node2['level'] >= 2:
            continue
        if norm(node2['title']) in SKIP_NORMS:
            continue
        s2 = seg_text(node2['src'])
        if s2:
            return s2[0]
    return (len(htmls), 0)

def head_eq(b0, title):
    n0, nt = norm(b0), norm(title)
    return n0 == nt or (n0.startswith(nt) and len(n0) - len(nt) <= 4)

TRANSLATORS = ("李秋零", "苗力田")

def clean_title(s):
    """译者名尾巴剥离（ncx 制作者把译者名写进标题，如 '前 言李秋零'）"""
    for suf in TRANSLATORS:
        if s.endswith(suf):
            return s[: -len(suf)]
    return s

ALL_D01 = {norm(n['title']) for n in flat if n['level'] < 2}
COVER = {"判断力批判"}  # 册内著作封面大标题（其他两个已被 ALL_D01 覆盖）
BOOK_PREFIX = ("书名：", "作者：", "译者：", "出版社：", "出版日期：", "ISBN：", "价格：", "译注：")
# ncx 缺失"第一卷 私人法权/第二卷 公共法权"（part0141 被拆分且无条目）：
# 一般道德形而上学的划分 只收 part0140 小节，part0141 拆为独立章
EXTRA_AFTER = {"一般道德形而上学的划分": ("私人法权与公共法权", "text/part0141_split_000.html",
                                          ["第一卷 私人法权", "第一章 物品法权", "第二章 人身法权",
                                           "第三章 采用物的方式的人身法权", "第二卷 公共法权",
                                           "第一章 国家法权", "第二章国际法权", "第三章世界公民法权"])}
KANT_SECTIONS = {norm(s) for s in EXTRA_AFTER["一般道德形而上学的划分"][2]}

toc = []
files = {}
ch_index = 0
warns = []
prev_part_label = None

for i, node in enumerate(flat):
    title = clean_title(node['title'])
    nl = norm(title)
    if nl in SKIP_NORMS:
        continue
    if node['level'] >= 2:
        continue  # section 不切分
    if node['level'] == 0:
        toc.append({"type": "part", "title": node['title'], "level": 0, "index": ch_index})
        seq0 = seg_text(node['src'])
        prev_part_label = (nl, seq0[0] if seq0 else None)
        continue
    seq = seg_text(node['src'])
    if not seq:
        warns.append(f"!! 无锚点: {node['title']}")
        continue
    fi, bi = seq[0]
    nf, nb = next_split(i)
    extra = None
    if nl in EXTRA_AFTER:
        e_title, e_file, e_secs = EXTRA_AFTER[nl]
        pfi = htmls.index(e_file)
        end_fi, end_bi = (pfi, 0)   # 本节只收 part0140 小节
        extra = (pfi, 0, nf, nb, e_title, e_secs)
    else:
        end_fi, end_bi = nf, nb
    # part 锚点仅当与 chapter 同文件且中间无其他块才并入起点
    # （否则吞入 册封面大标题 等中间块；总目录页因不同文件自动排除）
    pl_nl = prev_part_label[0] if prev_part_label else None
    p_anchor = prev_part_label[1] if prev_part_label else None
    prev_part_label = None
    if p_anchor and p_anchor[0] == fi:
        mid = collect(p_anchor[0], p_anchor[1], fi, bi)  # [part锚点, chapter锚点) 区间
        if mid:
            p_anchor = None  # 中间有封面/书名块 → 不用 part 锚点
    start = p_anchor if p_anchor is not None else (fi, bi)
    blocks = collect(start[0], start[1], end_fi, end_bi)
    while True:
        bv = norm(blocks[0]["value"]) if blocks else None
        if not bv:
            break
        if nl and head_eq(blocks[0]["value"], nl):
            blocks = blocks[1:]
            continue
        if pl_nl and head_eq(blocks[0]["value"], pl_nl):
            blocks = blocks[1:]
            continue
        if bv in SKIP_NORMS:
            blocks = blocks[1:]
            continue
        if bv in ALL_D01 or bv in COVER:
            blocks = blocks[1:]  # 另一著作的封面大标题/分隔页
            continue
        if bv.startswith(BOOK_PREFIX):
            blocks = blocks[1:]  # 出版信息页（书名/作者/出版社/ISBN…）
            continue
        break
    dedup = []
    for blk in blocks:
        if dedup and norm(dedup[-1]["value"]) == norm(blk["value"]):
            continue
        dedup.append(blk)
    if not dedup:
        warns.append(f"!! 空章节跳过: {node['title']}")
        continue
    secs = []
    for s in node['children']:
        if norm(s['title']) in SKIP_NORMS or s['level'] != 2:
            continue
        secs.append({"type": "section", "title": clean_title(s['title']), "index": ch_index, "level": 2})
    toc.append({"type": "chapter", "title": title, "index": ch_index, "level": 1})
    toc.extend(secs)
    files[ch_index] = {"index": ch_index, "title": title, "content": dedup}
    ch_index += 1
    if extra:
        efi, ebi, eend_fi, eend_bi, e_title, e_secs = extra
        eblocks = collect(efi, ebi, eend_fi, eend_bi)
        while eblocks and norm(eblocks[0]["value"]) in (norm(e_title), norm("第一卷 私人法权")):
            eblocks = eblocks[1:]  # 卷标题块
        # 尾部：下一 chapter 标题块 + 其"科学院版编者导言"块（本区间吞入）
        nxt_norm = None
        for node2 in flat[i + 1:]:
            if node2['level'] >= 2:
                continue
            n2 = norm(clean_title(node2['title']))
            if n2 in SKIP_NORMS:
                continue
            nxt_norm = n2
            break
        while eblocks and (norm(eblocks[-1]["value"]) == nxt_norm
                           or norm(eblocks[-1]["value"]) == "科学院版编者导言"):
            eblocks = eblocks[:-1]
        ededup = []
        for blk in eblocks:
            if ededup and norm(ededup[-1]["value"]) == norm(blk["value"]):
                continue
            ededup.append(blk)
        if not ededup:
            warns.append(f"!! 空章节: {e_title}")
        else:
            for s in e_secs:  # 卷内章标题挂 section（不切分正文）
                toc.append({"type": "section", "title": s, "index": ch_index, "level": 2})
            toc.append({"type": "chapter", "title": e_title, "index": ch_index, "level": 1})
            files[ch_index] = {"index": ch_index, "title": e_title, "content": ededup}
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
    "bookId": old_meta.get("bookId") or "390398aff8d0",
    "title": old_meta.get("title") or "康德文集",
    "author": old_meta.get("author") or "康德",
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
