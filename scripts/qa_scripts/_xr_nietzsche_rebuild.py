# -*- coding: utf-8 -*-
"""尼采哲学经典（套装共5册）523a7333343f 重建（一次性，纯文件级切分）
epub: 尼采哲学经典（套装共5册）.epub  简体正文  ncx 1827 条但锚点全部错乱
       （d1/d2 锚点指向瞧！人书的标题页/译注页/版本页，不可用于切分）
结构: 每本书有完整排版区（版权页+目录+正文），正文每章 = 标题页文件 + 正文文件
      瞧！这个人 004-043（19章）｜快乐的知识 046-065（9章）｜查拉 068-081（9章）
      上帝之死 084-101（9章）｜悲剧的诞生 104-115（4章）＝ 50 章
映射: 书=part（5）；章=chapter（文件级区间）；节=section（ncx d2 有文字标题才挂）
      d2 纯序号（一/二/三 或 1/2/3）→ 不挂；图注页（巴塞尔图/签名/档案馆）保留在章首
用法: python _xr_nietzsche_rebuild.py [--dry]
"""
import zipfile, re, json, os, sys, html as html_mod, shutil

EP = 'F:/philosophy/西方/弗里德里希·尼采/尼采哲学经典（套装共5册）.epub'
SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters/523a7333343f"
DST = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/523a7333343f"

# (标题, 起始文件编号, 结束文件编号) —— 左闭右开，按文件顺序
CH = [
    # ── 瞧！这个人（19章）──────────────────────────
    ("尼采的天鹅之歌", 6, 9),        # 006 图页 + 007 标题页 + 008 正文
    ("前言", 9, 10),
    ("为什么我这么有智慧", 10, 12),
    ("为什么我如此聪明", 12, 14),
    ("为什么我会写出如此优越的书", 14, 16),
    ("《悲剧的诞生》", 16, 18),
    ("《不合时宜的思想》", 18, 20),
    ("《人性的，太人性的》及其两续篇", 20, 22),
    ("《曙光》：道德思想是偏见", 22, 24),
    ("《快乐的知识》：快乐的科学", 24, 26),
    ("《查拉图斯特拉如是说》：为所有人、不为某个人而写的书", 26, 28),
    ("《善恶的彼岸》：未来哲学的序曲", 28, 30),
    ("《道德的系谱》：一个论战", 30, 32),
    ("《偶像的黄昏》", 32, 34),
    ("《瓦格纳事件》：一个音乐家的问题", 34, 36),
    ("为什么我是命运", 36, 38),
    ("一个自我批评的企图", 38, 40),
    ("译后语", 40, 42),
    ("尼采年谱", 42, 44),
    # ── 快乐的知识（9章）──────────────────────────
    ("译序", 48, 50),                # 048 图页 + 049 译序
    ("嘲谑、阴谋与报复", 50, 52),
    ("卷一", 52, 54),
    ("卷二", 54, 56),
    ("卷三", 56, 58),
    ("卷四", 58, 60),
    ("卷五", 60, 62),
    ("附录：“自由之鸟”王子之歌", 62, 64),
    ("尼采年谱", 64, 66),
    # ── 查拉图斯特拉如是说（9章）──────────────────
    ("尼采生平", 70, 72),            # 070 图注（魏玛的尼采档案馆）+ 071 正文
    ("关于《查拉图斯特拉如是说》", 72, 73),
    ("查拉图斯特拉是如何产生的", 73, 74),
    ("查拉图斯特拉　序白", 74, 75),
    ("卷一", 75, 76),
    ("卷二", 76, 77),
    ("卷三", 77, 78),
    ("卷四", 78, 80),
    ("尼采年谱", 80, 82),
    # ── 上帝之死（9章）────────────────────────────
    ("英译编者前言", 86, 88),        # 086 图页 + 087 前言
    ("作者前言", 88, 89),
    ("尼采的生平和《上帝之死》", 89, 91),
    ("从陀思妥耶夫斯基、尼采到卡夫卡", 91, 93),
    ("尼采的一生", 93, 95),
    ("对基督教道德观念的批判", 95, 97),
    ("附录：尼采与虚无主义", 97, 99),
    ("译后语", 99, 100),
    ("尼采年谱", 100, 102),
    # ── 悲剧的诞生（4章）──────────────────────────
    ("天才尼采的悲剧", 106, 109),    # 106 图页 + 107 标题页 + 108 正文
    ("批评的回顾", 109, 111),
    ("悲剧诞生于音乐精神", 111, 114),  # 111 标题页 + 112 + 113（分片续）
    ("尼采年谱", 114, 116),
]
PART_BOUND = {19, 28, 37, 46}  # 每书起始章索引（瞧0/快乐19/查拉28/上帝37/悲剧46）
PART_TITLES = ["瞧！这个人", "快乐的知识", "查拉图斯特拉如是说", "上帝之死", "悲剧的诞生"]
TAIL_SKIP = {"重排大字修订版", "1998年10月"}  # 008 文件尾部版本页说明块+日期

z = zipfile.ZipFile(EP)

def norm(s):
    return re.sub(r"\s+", "", s or "")

# ── ncx：只取 ROOT[1] 的 50 个 d1 标题 + d2 标题（section 用）──
ncx_name = [n for n in z.namelist() if n.endswith('.ncx')][0]
t = z.read(ncx_name).decode('utf-8')
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
    return html_mod.unescape(lb.group(1)) if lb else ''

roots = build_tree()
d1_list = roots[1]['children']  # 50 个 d1（与 CH 顺序一致）
assert len(d1_list) == len(CH), f"ncx d1={len(d1_list)} vs CH={len(CH)}"

# ── 正文块提取 ──
_HTML_TAG = re.compile(r'<[^>]+>')
_BR = re.compile(r'<br\s*/?>', re.I)

def el_text(seg):
    seg = _BR.sub('\n', seg)
    seg = _HTML_TAG.sub('', seg)
    seg = html_mod.unescape(seg)
    seg = re.sub(r'[ \t\xa0]+', ' ', seg)
    return seg.strip()

_INVIS = '　​‌‍﻿ \t\xa0'

def extract_blocks(fname):
    h = z.read(fname).decode('utf-8')
    blocks = []
    for m in re.finditer(r'<(p|table|h[1-6])([^>]*)>(.*?)</\1>', h, re.S):
        tag, inner = m.group(1), m.group(3)
        if tag == 'p':
            text = el_text(inner)
            if text and text.strip(_INVIS):
                blocks.append({"type": "text", "value": text})
        elif tag == 'table':
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', inner, re.S)
            for r in rows:
                cells = re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', r, re.S)
                row_text = '  '.join(el_text(c) for c in cells)
                if row_text and row_text.strip(_INVIS):
                    blocks.append({"type": "text", "value": row_text})
        elif tag in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
            text = el_text(inner)
            if text and text.strip(_INVIS):
                blocks.append({"type": "text", "value": text})
    return blocks

htmls = sorted((n for n in z.namelist() if n.endswith(('.html', '.xhtml'))),
               key=lambda n: [int(x) if x.isdigit() else x for x in re.split(r'(\d+)', n)])
# 文件编号 → 索引（index_split_NNN 的编号 = 索引，前面无填充干扰）
fi_of = {}
for idx, f in enumerate(htmls):
    m = re.match(r'index_split_(\d+)\.html', f)
    if m:
        fi_of[int(m.group(1))] = idx
blocks_by_file = {f: extract_blocks(f) for f in htmls}
print(f"ncx 条目: {len(opens)} | html 文件: {len(htmls)}")

def head_eq(b0, title):
    n0, nt = norm(b0), norm(title)
    return n0 == nt or (n0.startswith(nt) and len(n0) - len(nt) <= 4)

PURE_D2 = re.compile(r'^[一二三四五六七八九十百\d]+$')  # 纯序号节标题不挂

toc = []
files = {}
warns = []
ch_index = 0

for i, (title, fa, fb) in enumerate(CH):
    fi_a, fi_b = fi_of[fa], fi_of[fb]
    blocks = []
    for kf in range(fi_a, fi_b):
        for blk in blocks_by_file[htmls[kf]]:
            blocks.append(blk)
    # 章首标题块删除（标题页文件 或 合体章首块）
    while blocks and head_eq(blocks[0]["value"], title):
        blocks = blocks[1:]
    # 尾部版本页清理
    while blocks and norm(blocks[-1]["value"]) in {norm(k) for k in TAIL_SKIP}:
        blocks = blocks[:-1]
    dedup = []
    for blk in blocks:
        if dedup and norm(dedup[-1]["value"]) == norm(blk["value"]):
            continue
        dedup.append(blk)
    if not dedup:
        warns.append(f"!! 空章节: {title}")
    # part 边界（第一本书 i=0 也输出）
    if i == 0 or i in PART_BOUND:
        pid = 0 if i == 0 else sorted(PART_BOUND).index(i) + 1
        toc.append({"type": "part", "title": PART_TITLES[pid], "level": 0, "index": ch_index})
    # section（ncx d2 有文字标题才挂）
    secs = []
    for c in d1_list[i]['children']:
        l2 = norm(node_info(c))
        if not l2 or PURE_D2.match(l2):
            continue
        secs.append({"type": "section", "title": node_info(c), "index": ch_index, "level": 2})
    toc.append({"type": "chapter", "title": title, "index": ch_index, "level": 1})
    toc.extend(secs)
    files[ch_index] = {"index": ch_index, "title": title, "content": dedup}
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
    "bookId": old_meta.get("bookId") or "523a7333343f",
    "title": old_meta.get("title") or "尼采哲学经典（套装共5册）",
    "author": old_meta.get("author") or "弗里德里希·尼采",
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
