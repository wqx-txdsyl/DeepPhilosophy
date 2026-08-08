# -*- coding: utf-8 -*-
"""MEGA：陶伯特版《德意志意识形态·费尔巴哈》1085686cbd33 重建（一次性，PDF 文本层按页切分）
pdf: F:/philosophy/西方/卡尔·马克思/MEGA：陶伯特版《德意志意识形态·费尔巴哈》.pdf（411 页，文本层 469k 字）
旧数据 4 章 = dp_pdf_import 强模式标题误匹配（"第一部 第一章"是正文中段、"第1节…"两条、
"出版说明"是编辑说明）→ 正文截断、层级全丢。
真实结构（PDF 物理页，勘察自目录 p16-18 + 各边界页验证）:
  ch0 代译序 p5-12 / ch1 发刊词 p13-15
  part0 德意志意识形态(正文):
    绪言(先行版) p21-32 / 编辑符号说明 p33-34 / 手稿和刊印稿 p35-36 / 答布鲁诺·鲍威尔 p37-38 /
    费尔巴哈和历史。草稿和笔记 p39-100（4 section: 草稿1-29页 p39-60/30-35页 p61-65/36-72页 p66-98/幻己·笔记 p99-100）/
    费尔巴哈 p101-102 / I.费尔巴哈 A. p103-104 / I.费尔巴哈 1. p105-106 / 导言 p107-108 /
    残篇1 p109-110 / 残篇2 p111-112 / 莱比锡宗教会议 p113-114 / II.圣布鲁诺 p115-128 /
    布鲁诺·鲍威尔及其辩护士 p129-132
  part1 副卷：异文与编辑说明:
    1/5-1 答布鲁诺 p137-139 / 1/5-3 费尔巴哈和历史 p140-164 / 1/5-4 费尔巴哈 p165-175 /
    1/5-5 I.费尔巴哈 A. p176-177 / 1/5-10 莱比锡宗教会议 p178-179 / 1/5-11 II.圣布鲁诺 p180-182
  part2 附录:
    附录一 德文原文 p183-326 / 附录二 MEGA2试行版(1972) p327-409
  SKIP: p0 封面/p1 内容提要/p2 书名页/p3 版权页/p4 丛书总序/p16-18 目录/p19-20 正文书名页/
        p133 副卷书名页/p134 空/p135-136 副卷编辑符号说明(与正文部分重复)/p410 丛书广告
  每页=1 块；剥纯数字行（页码/眉码 ^[0-9〇]{1,4}$）
用法: python _xr_mega_rebuild.py [--dry]
"""
import fitz, json, os, sys, re, shutil

PDF = 'F:/philosophy/西方/卡尔·马克思/MEGA：陶伯特版《德意志意识形态·费尔巴哈》.pdf'
BID = "1085686cbd33"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"

doc = fitz.open(PDF)
print(f"PDF: {doc.page_count} 页")

# ---- 页文本提取（每页=1 块；剥纯数字页码/眉码行） ----
def page_blocks(pi):
    t = doc[pi].get_text()
    out = []
    for line in t.splitlines():
        s = line.strip()
        if not s:
            continue
        if re.fullmatch(r'[0-9〇]{1,4}', s):
            continue
        out.append({"type": "text", "value": s})
    return out

page_texts = {}
for pi in range(doc.page_count):
    page_texts[pi] = page_blocks(pi)

# ---- 章节表（PDF 物理页区间） ----
SPANS = [
    # (title, part_title, start_p, end_p, sections)
    ("代译序", None, 5, 13, []),
    ("发刊词", None, 13, 16, []),
    ("绪言（先行版）", "德意志意识形态(正文)", 21, 33, []),
    ("编辑符号说明", "德意志意识形态(正文)", 33, 35, []),
    ("德意志意识形态。手稿和刊印稿", "德意志意识形态(正文)", 35, 37, []),
    ("答布鲁诺·鲍威尔", "德意志意识形态(正文)", 37, 39, []),
    ("费尔巴哈和历史。草稿和笔记", "德意志意识形态(正文)", 39, 101, [
        ("草稿第1—29页", 39, 61), ("草稿第30—35页", 61, 66),
        ("草稿第36—72页", 66, 99), ("幻己（笔记）", 99, 101)]),
    ("费尔巴哈", "德意志意识形态(正文)", 101, 103, []),
    ("I.费尔巴哈 A. 一般意识形态，特别是德意志的", "德意志意识形态(正文)", 103, 105, []),
    ("I.费尔巴哈 1. 一般意识形态，特别是德国哲学", "德意志意识形态(正文)", 105, 107, []),
    ("I.费尔巴哈 导言", "德意志意识形态(正文)", 107, 109, []),
    ("I.费尔巴哈 残篇1", "德意志意识形态(正文)", 109, 111, []),
    ("I.费尔巴哈 残篇2", "德意志意识形态(正文)", 111, 113, []),
    ("莱比锡宗教会议", "德意志意识形态(正文)", 113, 115, []),
    ("II.圣布鲁诺", "德意志意识形态(正文)", 115, 129, []),
    ("布鲁诺·鲍威尔及其辩护士", "德意志意识形态(正文)", 129, 133, []),
    ("1/5-1 答布鲁诺·鲍威尔", "副卷：异文与编辑说明", 137, 140, []),
    ("1/5-3 费尔巴哈和历史。草稿和笔记", "副卷：异文与编辑说明", 140, 165, []),
    ("1/5-4 费尔巴哈", "副卷：异文与编辑说明", 165, 176, []),
    ("1/5-5 I.费尔巴哈 A. 一般意识形态，特别是德意志的", "副卷：异文与编辑说明", 176, 178, []),
    ("1/5-10 莱比锡宗教会议", "副卷：异文与编辑说明", 178, 180, []),
    ("1/5-11 II.圣布鲁诺", "副卷：异文与编辑说明", 180, 183, []),
    ("附录一 德意志意识形态(正文)德文原文", "附录", 183, 327, []),
    ("附录二 《马克思恩格斯全集》(MEGA2)试行版(1972)", "附录", 327, 410, []),
]

SKIP_PAGES = list(range(0, 5)) + list(range(16, 21)) + [133, 134, 135, 136, 410]

toc = []
files = {}
warns = []
ch_index = 0
pending_part = None
total_chars = 0

for title, part_title, sp, ep, sections in SPANS:
    if part_title and part_title != pending_part:
        toc.append({"type": "part", "title": part_title, "index": ch_index, "level": 0})
        pending_part = part_title
    blocks = []
    for pi in range(sp, ep):
        blocks.extend(page_texts[pi])
    if not blocks:
        warns.append(f"!! 空章节: {title}")
        continue
    toc.append({"type": "chapter", "title": title, "index": ch_index, "level": 1})
    sec_i = 1
    for st, ss, se in sections:
        sblocks = []
        for pi in range(ss, se):
            sblocks.extend(page_texts[pi])
        if sblocks:
            toc.append({"type": "section", "title": st, "index": ch_index, "sec": sec_i, "level": 2})
            sec_i += 1
    files[ch_index] = {"index": ch_index, "title": title, "content": blocks}
    ch_index += 1

print(f"\n章节总数: {len(files)} | toc: {len(toc)} | 警告: {len(warns)}")
for w in warns:
    print("⚠", w)
for idx in sorted(files):
    ch = files[idx]
    nc = sum(len(b['value']) for b in ch['content'])
    total_chars += nc
    print(f"  {idx:2d} {ch['title'][:44]:46s} {nc:7d} 字")
print(f"\n总: {len(files)} 章, {total_chars} 字符")
# 旧数据对账
old_total = 0
old_dir = SRC
if os.path.isdir(old_dir):
    for fn in os.listdir(old_dir):
        if fn.endswith('.json') and fn != 'meta.json':
            ch = json.load(open(os.path.join(old_dir, fn), encoding='utf-8'))
            old_total += sum(len(b.get('value', '')) for b in ch.get('content', []))
print(f"旧数据总字数: {old_total}")
for tt in toc:
    ind = '  ' * tt.get('level', 1)
    print(f"{ind}[{tt['type']} {tt.get('sec','')}] {tt['title'][:44]}")
print("标题首:", files[0]['title'], "| 末:", files[len(files) - 1]['title'])

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
    "bookId": old_meta.get("bookId") or BID,
    "title": old_meta.get("title") or "MEGA：陶伯特版《德意志意识形态·费尔巴哈》",
    "author": old_meta.get("author") or "卡尔·马克思、弗里德里希·恩格斯、约瑟夫·魏德迈",
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
