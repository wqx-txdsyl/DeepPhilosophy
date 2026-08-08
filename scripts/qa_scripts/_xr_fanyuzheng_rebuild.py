# -*- coding: utf-8 -*-
"""反与正·婚礼集·夏 9bd452eb8422 重建（一次性，三书=part，篇目=chapter）
epub: 反与正·婚礼集·夏.epub  ncx 仅 5 条（目录/版权/三书各一文件）
结构: part0002=反与正(7篇) part0003=婚礼集(6篇) part0004=夏(8篇)，篇目=文件内标题块扫描
      （part0005-0008 为《反抗者》残留文件，spine 未引用，忽略）
映射: 每书=part；书内篇目标题（作者序/嘲　弄/若有若无之间/伤心之旅/热爱生活/反与正，
      出版者的说明/提帕萨的婚礼/贾米拉的风/阿尔及尔的夏天/沙　漠，
      人身牛头怪/地狱中的普罗米修斯/没有历史的城市小引/流放海伦/谜　语/重返蒂帕札/大海就在眼前）=chapter
      注　释 标题块并入末篇（注释正文保留）；头部书名页/译者/献词丢弃
用法: python _xr_fanyuzheng_rebuild.py [--dry]
"""
import zipfile, re, json, os, sys, html as html_mod, shutil

EP = 'F:/philosophy/西方/阿尔贝·加缪/反与正·婚礼集·夏.epub'
SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters/9bd452eb8422"
DST = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/9bd452eb8422"

PARTS = [
    ("反与正", "OEBPS/Text/part0002.xhtml",
     ["作者序", "嘲　弄", "若有若无之间", "伤心之旅", "热爱生活", "反与正"]),
    ("婚礼集", "OEBPS/Text/part0003.xhtml",
     ["出版者的说明", "提帕萨的婚礼", "贾米拉的风", "阿尔及尔的夏天", "沙　漠"]),
    ("夏", "OEBPS/Text/part0004.xhtml",
     ["人身牛头怪", "地狱中的普罗米修斯", "没有历史的城市小引", "流放海伦", "谜　语", "重返蒂帕札", "大海就在眼前"]),
]
HEAD_DROP = {"丁世中译", "王殿忠译", "献给让·格勒尼埃"}  # norm 后（头部前置页）

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

def is_title(blk, titles):
    """匹配篇目标题 → 返回标题（无脚注圈码），否则 None"""
    n = norm(blk["value"])
    for t in titles:
        nt = norm(t)
        if n == nt or (n.startswith(nt) and len(n) <= 8):  # 脚注圈码如 人身牛头怪②
            return t
    return None

# ────────── 组装 ──────────
toc = []
files = {}
ch_index = 0
warns = []

for part_title, fname, titles in PARTS:
    blocks = extract_blocks(fname)
    # 头部：书名页（书名/译者/献词）
    if blocks and norm(blocks[0]["value"]) == norm(part_title):
        blocks = blocks[1:]
    while blocks and norm(blocks[0]["value"]) in HEAD_DROP:
        blocks = blocks[1:]
    toc.append({"type": "part", "title": part_title, "level": 0, "index": ch_index})
    # 按篇目标题切分
    cur = None      # {title, blocks}
    pending = []    # 首个标题前的题词/引文块 → 并入第一篇
    for blk in blocks:
        t = is_title(blk, titles)
        if t:
            if cur is not None:
                files[ch_index] = {"index": ch_index, "title": cur["title"], "content": cur["blocks"]}
                toc.append({"type": "chapter", "title": cur["title"], "index": ch_index, "level": 1})
                ch_index += 1
            cur = {"title": t, "blocks": pending + []}
            pending = []
            continue
        if norm(blk["value"]) == "注释":
            continue  # 注释标题块并入末篇（注释正文保留）
        if cur is None:
            pending.append(blk)  # 题词（——司汤达/荷尔德林引文）待并入第一篇
        else:
            cur["blocks"].append(blk)
    if cur is not None:
        files[ch_index] = {"index": ch_index, "title": cur["title"], "content": cur["blocks"]}
        toc.append({"type": "chapter", "title": cur["title"], "index": ch_index, "level": 1})
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
    print(f"  [{idx}] {ch['title'][:24]} {nb}块 {nc}字 | {first}…")
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
    "bookId": old_meta.get("bookId") or "9bd452eb8422",
    "title": old_meta.get("title") or "反与正·婚礼集·夏",
    "author": old_meta.get("author") or "阿尔贝·加缪",
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
