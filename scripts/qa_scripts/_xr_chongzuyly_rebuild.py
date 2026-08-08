# -*- coding: utf-8 -*-
"""充足理由律的四重根 d8bcc10d42ff 重建（一次性，纯文件+块级锚点，ncx 残缺乱序不可用）
epub: 充足理由律的四重根.epub（西方/阿图尔·叔本华/）
ncx 残缺：第4/5/6章标题整个缺失、缺 14 个节条目、第34节起嵌套错乱、内容句当标题（"2．谓词…"）、
         "第8章总述和结论604"目录残影、"2．谓词…"双条目同文件。**不用 ncx**。
正文文件（index_split_000-045，001 不存在，046 目录页 ncx 未引用）块级全提取：
  章标题块 8 个（第1~8章；第4/5章分（上）（下）卷页标题，剥后缀合并）
  节标题块 52 个（第1~52节全部在正文，ncx 漏 14 个）
结构:
  chapter × 10: 内容简介(000,剥"行行"营销块)/第二版序言(002)/第1章 引论/第2章 概述/
                第3章 新证明要点/第4章 第一类客体/第5章 第二类客体/第6章 第三类客体/
                第7章 第四类客体/第8章 总述和结论
  section × 52（第1~52节, 按原文归章: 1章1-4/2章5-14/3章15/4章16-25/5章26-33/6章34-39/7章40-45/8章46-52）
  边界 = 块级锚点（第5节块/第3章标题块/第4章(上)标题块/第5章(上)标题块/第34节块/第7章标题块/第8章标题块）
  剥除: ____装饰(≥10下划线)/《第X章…》孤独书斋装饰页/第X章…（上|下）卷页标题/
        章标题块(norm全等)/节标题块(norm全等,≥4字)/营销广告("本书由")
用法: python _xr_chongzuyly_rebuild.py [--dry]
"""
import zipfile, re, json, os, sys, html as html_mod, shutil

EP = 'F:/philosophy/西方/阿图尔·叔本华/充足理由律的四重根.epub'
SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters/d8bcc10d42ff"
DST = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/d8bcc10d42ff"

z = zipfile.ZipFile(EP)

def norm(s):
    return re.sub(r"\s+", "", s or "")

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

# 文件序 = 书脊序（ncx 残缺不用；046 目录页排除）
htmls = sorted((n for n in z.namelist() if n.endswith('.html') and 'index_split' in n and not n.endswith('_046.html')),
               key=lambda n: int(re.search(r'(\d+)', n).group(1)))
blocks_by_file = {}
for f in htmls:
    blocks_by_file[f] = extract_blocks(f)
print(f"html 文件: {len(htmls)}")

# ---- 展平全局块列表（file 标识） ----
global_blocks = []   # (fi, bi, value)
for fi, f in enumerate(htmls):
    for bi, b in enumerate(blocks_by_file[f]):
        global_blocks.append([fi, bi, b[1]])

# ---- 提取节标题块（^第X节, norm ≤45） ----
sec_cands = []
for fi, bi, v in global_blocks:
    m = re.match(r'^第\d+节', v)
    if m and len(norm(v)) <= 45:
        sec_cands.append((int(re.search(r'第(\d+)节', v).group(1)), v))
sec_cands.sort()
sec_titles = {}
for num, v in sec_cands:
    sec_titles.setdefault(num, v)   # 同节号取首个（应唯一）
sec_nums = sorted(sec_titles)
print(f"节标题块: {len(sec_titles)} 个（{sec_nums[0]}-{sec_nums[-1]}）")
missing = [n for n in range(1, 53) if n not in sec_titles]
if missing:
    print(f"  ⚠ 缺节号: {missing}")
for n in sec_nums:
    print(f"  {n:3d} {sec_titles[n][:44]}")
sec_norm = {norm(sec_titles[n]): n for n in sec_titles}
sec_norm = {k: v for k, v in sec_norm.items() if len(k) >= 4}

# ---- 提取章标题块（^第X章, 去（上）（下）） ----
ch_cands = []
for fi, bi, v in global_blocks:
    if re.match(r'^第\d+章[\u3000\s]', v) or re.match(r'^第\d+章$', v):
        ch_cands.append((int(re.search(r'第(\d+)章', v).group(1)), v))
ch_cands.sort()
ch_titles = {}
for num, v in ch_cands:
    key = re.sub(r'（上）|（下）', '', v)
    ch_titles.setdefault(num, key)   # 同章号合并（上）（下）
print(f"\n章标题块: {len(ch_titles)} 个")
for n in sorted(ch_titles):
    print(f"  第{n}章 → {ch_titles[n][:52]}")
ch_norm = {norm(ch_titles[n]): n for n in ch_titles}

# ---- 剥除过滤器 ----
def is_junk(v):
    nv = norm(v)
    if nv and set(nv) <= set('_') and len(nv) >= 10:
        return True                        # ____ 装饰行
    if re.match(r'^《第\d+章', v) or re.match(r'^《[^》]+》$', v):
        return True                        # 书名号装饰页（《第X章…》孤独书斋 / 《第二版序言》）
    if re.match(r'^第\d+章[\u3000\s].*[上下]）$', v):
        return True                        # 卷页标题 第X章…（上/下）（全角（）非分组符, 用字符类）
    if nv in ch_norm:
        return True                        # 章标题块
    if nv in sec_norm:
        return True                        # 节标题块
    if nv in ('内容简介', '第二版序言'):
        return True                        # 序言/简介标题块（章标题已入 toc）
    if v.startswith('本书由'):
        return True                        # 营销广告（000）
    return False

# ---- 块级锚点（边界定位） ----
def find_block(pred):
    for i, (fi, bi, v) in enumerate(global_blocks):
        if pred(v):
            return i
    return None

anchors = {
    'sec5':  find_block(lambda v: norm(v) == norm(sec_titles[5])),
    'ch3':   find_block(lambda v: norm(v) == norm(ch_titles[3])),
    'ch4':   find_block(lambda v: re.sub(r'（上）|（下）', '', v) == ch_titles[4]),
    'ch5':   find_block(lambda v: re.sub(r'（上）|（下）', '', v) == ch_titles[5]),
    'sec34': find_block(lambda v: norm(v) == norm(sec_titles[34])),
    'ch7':   find_block(lambda v: norm(v) == norm(ch_titles[7])),
    'ch8':   find_block(lambda v: norm(v) == norm(ch_titles[8])),
}
for k, v in anchors.items():
    print(f"  锚点 {k}: 块 {v}（{'未找到!!' if v is None else global_blocks[v][2][:24]}）")

# ---- 章节区间（显式 (start, end)；ch0/ch1 同终点特殊文件章，ch2 第1章从 003 起） ----
# ch0=000 内容简介, ch1=002 第二版序言（special=[fi] 只收该文件）
# ch2 第1章 = 003 起（rest: 排除 000/002）
# 边界锚点: sec5=块34, ch3=块128, ch4=块138, ch5=块285, sec34=块332, ch7=块408, ch8=块441
G3 = sum(len(blocks_by_file[f]) for f in htmls[:2])   # 003 首块全局位置
SPANS = [
    ("内容简介",                       0, 0,            anchors['sec5'], [0]),
    ("第二版序言",                     1, 0,            anchors['sec5'], [1]),
    (ch_titles[1],                    2, G3,            anchors['sec5'], 'rest'),
    (ch_titles[2],                    3, anchors['sec5'], anchors['ch3'],  None),
    (ch_titles[3],                    4, anchors['ch3'],  anchors['ch4'],  None),
    (ch_titles[4],                    5, anchors['ch4'],  anchors['ch5'],  None),
    (ch_titles[5],                    6, anchors['ch5'],  anchors['sec34'], None),
    (ch_titles[6],                    7, anchors['sec34'], anchors['ch7'], None),
    (ch_titles[7],                    8, anchors['ch7'],  anchors['ch8'],  None),
    (ch_titles[8],                    9, anchors['ch8'],  len(global_blocks), None),
]

SEC_RANGES = {  # 章内节号区间
    '内容简介': [], '第二版序言': [],
    2: list(range(1, 5)), 3: list(range(5, 15)), 4: [15],
    5: list(range(16, 26)), 6: list(range(26, 34)), 7: list(range(34, 40)),
    8: list(range(40, 46)), 9: list(range(46, 53)),
}

toc = []
files = {}
warns = []
ch_index = 0
junk_count = 0
total_chars = 0
for i, (title, idx, start_gi, end_gi, special) in enumerate(SPANS):
    blocks = []
    junk = 0
    for gi in range(start_gi, end_gi):
        fi, bi, v = global_blocks[gi]
        if special is not None:
            if special == 'rest':
                if fi < 2:   # 000/002 由 ch0/ch1 收集
                    continue
            elif fi not in special:
                continue
        if is_junk(v):
            junk += 1
            continue
        blocks.append({"type": "text", "value": v})
    junk_count += junk
    if not blocks:
        warns.append(f"!! 空章节: {title}")
        continue
    toc.append({"type": "chapter", "title": title, "index": ch_index, "level": 1})
    for sec_num in SEC_RANGES.get(idx, []):
        toc.append({"type": "section", "title": sec_titles[sec_num],
                    "index": ch_index, "sec": sec_num - (min(SEC_RANGES[idx]) - 1) if SEC_RANGES[idx] else 0,
                    "level": 2})
    files[ch_index] = {"index": ch_index, "title": title, "content": blocks}
    ch_index += 1

print(f"\n章节总数: {len(files)} | toc: {len(toc)} | 剥除块: {junk_count} | 警告: {len(warns)}")
for w in warns:
    print("⚠", w)
for idx in sorted(files):
    ch = files[idx]
    nc = sum(len(b['value']) for b in ch['content'])
    total_chars += nc
    print(f"  {idx:2d} {ch['title'][:40]:42s} {nc:7d} 字")
print(f"\n总: {len(files)} 章, {total_chars} 字符（旧 42 章）")
for tt in toc:
    ind = '  ' * tt.get('level', 1)
    print(f"{ind}[{tt['type']} {tt.get('sec','')}] {tt['title'][:48]}")
print("标题首:", files[0]['title'], "| 末:", files[len(files) - 1]['title'])
for tgt in ('内容简介', '第二版序言', '第1章 引论', '第4章 论主体的第一类客体，以及在这类客体中起支配作用的充足根据律的形式', '第5章 论主体的第二类客体以及充足根据律在其中起支配作用的形式', '第6章 论主体的第三类客体以及充足根据律在这类客体中起支配作用的形式', '第7章 论主体的第四类客体以及充足根据律在其中起支配作用的形式', '第8章 总述和结论'):
    for idx, ch in files.items():
        if ch['title'] == tgt:
            print(f"首块[{tgt[:16]}]:", ch['content'][0]['value'][:40])
            break

if '--dry' in sys.argv:
    for idx, ch in files.items():
        for b in ch['content']:
            v = b['value']
            if ('孤独书斋' in v or re.match(r'^第\d+章', v) or re.search(r'[上下]）$', v)
                    or (len(v) >= 5 and set(v) <= set('_ \t'))):
                print(f"⚠ 残留 [{idx} {ch['title'][:14]}]: {v[:52]}")
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
    "bookId": old_meta.get("bookId") or "d8bcc10d42ff",
    "title": old_meta.get("title") or "充足理由律的四重根",
    "author": old_meta.get("author") or "阿图尔·叔本华",
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
