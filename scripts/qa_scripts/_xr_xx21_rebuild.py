# -*- coding: utf-8 -*-
"""西方哲学二十一讲 9aea99ccb525 重建（一次性，ncx 顶层=part+chapter，文件边界切分）
epub: 西方哲学二十一讲.epub（西方/弗兰克·梯利/）
ncx 顶层 30 条：版权信息/导读/序言/第一部分 希腊哲学史/第一~五讲/
               第二部分 中古哲学/第六~十一讲/第三部分 近世哲学/近世哲学的精神/第十二~二十一讲
旧数据问题：2 part 且第二 part 标题错（"近代哲学"≠ncx"中古哲学"+"近世哲学"两 part 合并）、
            "第 一 讲"空格标题块残留、part 标题页文本（"第 一 部 分"）进正文、版权信息入章。
结构:
  SKIP: 版权信息条目 + part 标题页文件（≤12字自动过滤）+ Table of Contents 页
  part × 3（第一部分/第二部分/第三部分, level 0, index=首章 index, 无正文）
  chapter × 24（导读/序言 + 第一~二十一讲 + 近世哲学的精神, level 1）
  切分: 文件边界（第十七讲=part0024_split_000/001/002 三文件合并）
  剥标题: strip_title 串联累加（norm 去空格,"第 一 讲"+"自然哲学"=label）+ "康德"/"黑格尔"装饰块
  节标题块（"第一章"/"第一节…"）保留为正文
用法: python _xr_xx21_rebuild.py [--dry]
"""
import zipfile, re, json, os, sys, html as html_mod, shutil

EP = 'F:/philosophy/西方/弗兰克·梯利/西方哲学二十一讲.epub'
SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters/9aea99ccb525"
DST = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/9aea99ccb525"

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
flat = [node_info(r) for r in roots]
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
blocks_by_file = {}
for f in htmls:
    blocks_by_file[f] = extract_blocks(f)
print(f"html 文件: {len(htmls)}")

def tail_skip(fname):
    bl = blocks_by_file[fname]
    t2 = ''.join(b[1] for b in bl)
    if len(t2) <= 12:
        return True                          # 空壳/part 标题页（"第一部分"/"希腊哲学史"）
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
    """串联累加剥章首标题块（norm 去空格：'第 一 讲'+'自然哲学'=label）"""
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
    # 剥"康德"/"黑格尔"装饰大字块（split 页首块，全书精确匹配）
    return [b for b in blocks[i:] if b['value'].strip() not in ('康德', '黑格尔')]

PART_RE = re.compile(r'^(第一|第二|第三)部分')
SKIP = {'版权信息'}

toc = []
files = {}
warns = []
ch_index = 0
pending_parts = []  # (label, node_i) 等待回填 index

def resolve_parts():
    while pending_parts:
        toc.append({"type": "part", "title": pending_parts.pop(0), "index": ch_index, "level": 0})

for i, node in enumerate(flat):
    src = node['src']
    f, _, _ = src.partition('#')
    if PREFIX and f.startswith(PREFIX):
        pass
    elif PREFIX:
        f = PREFIX + f
    if norm(node['label']) == norm('版权信息'):
        print(f"skip: {node['label']}")
        continue
    if PART_RE.match(node['label'].strip()):
        pending_parts.append(node['label'])
        print(f"part 待定: {node['label']}")
        continue
    if f not in htmls:
        warns.append(f"!! 无文件: {node['label']} → {src}")
        continue
    fi = htmls.index(f)
    nf, nb = next_split(i)
    blocks = collect(fi, 0, nf, nb)
    blocks = strip_title(blocks, node['label'])
    if not blocks:
        warns.append(f"!! 空章节跳过: {node['label']}")
        continue
    resolve_parts()
    toc.append({"type": "chapter", "title": node['label'], "index": ch_index, "level": 1})
    files[ch_index] = {"index": ch_index, "title": node['label'], "content": blocks}
    ch_index += 1
if pending_parts:
    warns.append(f"!! part 无后继章: {pending_parts}")

print(f"\n章节总数: {len(files)} | toc 条目: {len(toc)} | 警告: {len(warns)}")
for w in warns:
    print("⚠", w)
total_chars = 0
for idx, ch in files.items():
    nc = sum(len(b['value']) for b in ch['content'])
    total_chars += nc
    print(f"  {idx:2d} {ch['title'][:30]:32s} {nc:7d} 字")
print(f"\n总: {len(files)} 章, {total_chars} 字符（旧 350114）")
for tt in toc:
    ind = ' ' * 2 * tt.get('level', 1)
    print(f"{ind}[{tt['type']} {tt.get('sec','')}] {tt['title'][:40]}")
print("标题首:", files[0]['title'], "| 末:", files[len(files) - 1]['title'])
for tgt in ('第一讲 自然哲学', '第六讲 基督教神学的兴起', '近世哲学的精神', '第十二讲 英国经院论', '第十七讲 康德的批判哲学', '第十八讲 德国的唯心论'):
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
    "bookId": old_meta.get("bookId") or "9aea99ccb525",
    "title": old_meta.get("title") or "西方哲学二十一讲",
    "author": old_meta.get("author") or "弗兰克·梯利",
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
