# -*- coding: utf-8 -*-
"""知行合一王阳明大全集(5册) d3f79625368c 重建（一次性，按 html 文件切分，5 册 part + 每文件一章）
epub: 知行合一王阳明大全集(套装共5册）.epub  ncx 5 条（每册一个起点：知行合一王阳明.1-.4 + 传习录）
旧数据 5 章 = 每册一整章未拆（0.json 2832 段）；且册5"传习录"仅 512 字——
ncx 指向的 text00088 是空文件，传习录正文（前言/序/上传习录中/下/附录/年谱/参考文献/注释）
全部丢失，从未入库。
结构:
  part(0) × 5: 知行合一王阳明1/2/3/4 + 传习录（按文件序号范围触发）
  chapter × N: 每个非跳过 html 文件一章，标题 = 文件首块（归一化空白）
  跳过: 空文件 / 版权页(^图书在版编目) / 书名页(单块^知行合一王阳明\d或^传习录$)
        / 广告页(^激发个人成长|^认准读客熊猫) / 目录页(^目录$)
  特例: text00099 注释块(^\[\d+\]) → 标题 "注释"
用法: python _xr_zhixingheyi_rebuild.py [--dry]
"""
import zipfile, re, json, os, sys, html as html_mod, shutil

EP = 'F:/philosophy/东方/度阴山/知行合一王阳明大全集(套装共5册）.epub'
SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters/d3f79625368c"
DST = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/d3f79625368c"
# 每册的文件序号范围 [start, end]（含）
RANGES = [("知行合一王阳明1", 2, 11),
          ("知行合一王阳明2", 13, 23),
          ("知行合一王阳明3", 27, 64),
          ("知行合一王阳明4", 69, 86),
          ("传习录", 91, 99)]

z = zipfile.ZipFile(EP)
htmls = sorted((n for n in z.namelist() if n.endswith(('.html', '.xhtml'))),
               key=lambda n: [int(x) if x.isdigit() else x for x in re.split(r'(\d+)', n)])

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
    return blocks

blocks_by_file = {}
for f in htmls:
    blocks_by_file[f] = extract_blocks(f)
print(f"html 文件: {len(htmls)}")

# 文件序号（text000XX.html → XX）
def fnum(fname):
    m = re.search(r'text(\d+)\.html', fname)
    return int(m.group(1)) if m else -1

ADV = {'激发个人成长', '认准读客熊猫'}

def skip_reason(fname):
    """返回跳过原因或 None"""
    bl = blocks_by_file[fname]
    if not bl:
        return '空文件'
    first = bl[0][1]
    if first.startswith('图书在版编目'):
        return '版权页'
    if len(bl) == 1 and (re.fullmatch(r'知行合一王阳明\d', first) or first == '传习录'):
        return '书名页'
    if first in ADV:
        return '广告页'
    if first == '目录':
        return '目录页'
    return None

toc = []
files = {}
ch_index = 0
warns = []
vol_i = 0
active_part = None  # 当前已触发的 part 名

for f in htmls:
    n = fnum(f)
    if n < 0:
        continue
    # part 触发：进入新一册范围（仅触发一次）
    while vol_i < len(RANGES) and n > RANGES[vol_i][2]:
        vol_i += 1
    if vol_i < len(RANGES) and n >= RANGES[vol_i][1]:
        if active_part != RANGES[vol_i][0]:
            active_part = RANGES[vol_i][0]
            toc.append({"type": "part", "title": RANGES[vol_i][0], "level": 0, "index": ch_index})
    # 跳过判断
    reason = skip_reason(f)
    if reason:
        if reason != '空文件':
            warns.append(f"跳过 {f}: {reason}")
        continue
    # 章
    bl = blocks_by_file[f]
    blocks = [{"type": "text", "value": b[1]} for b in bl]
    first = bl[0][1]
    if re.match(r'^\[\d+\]', first):
        title = '注释'
    else:
        title = re.sub(r'\s+', ' ', first)
    toc.append({"type": "chapter", "title": title, "index": ch_index, "level": 1})
    files[ch_index] = {"index": ch_index, "title": title, "content": blocks}
    ch_index += 1

print(f"\n章节总数: {len(files)} | toc 条目: {len(toc)}")
for w in warns:
    print("⚠", w)
total_chars = 0
for idx, ch in files.items():
    nc = sum(len(b['value']) for b in ch['content'])
    total_chars += nc
print(f"\n总: {len(files)} 章, {total_chars} 字符（旧 857,212，其中传习录册仅 512 字）")
# 按 part 累计字数
vols = [(tt['title'], tt['index']) for tt in toc if tt['type'] == 'part']
for vi, (vname, vstart) in enumerate(vols):
    vend = vols[vi + 1][1] if vi + 1 < len(vols) else len(files)
    vsum = sum(sum(len(b['value']) for b in files[i]['content']) for i in range(vstart, vend) if i in files)
    print(f"  {vname}: [{vstart},{vend}) {vsum}字")
for tt in toc:
    if tt['type'] == 'part':
        print(("  " * tt['level']) + f"[{tt['level']}] {tt['title']}")
print("标题前3:", [files[i]['title'][:26] for i in range(3)])
print("标题末3:", [files[i]['title'][:26] for i in range(len(files) - 3, len(files))])

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
    "bookId": old_meta.get("bookId") or "d3f79625368c",
    "title": old_meta.get("title") or "知行合一王阳明大全集(5册)",
    "author": old_meta.get("author") or "度阴山",
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
