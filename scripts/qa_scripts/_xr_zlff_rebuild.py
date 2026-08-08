# -*- coding: utf-8 -*-
"""《真理与方法》解读（何卫平）b43aeb7ccc57 重建（一次性，PDF 文本层按页切分）
pdf: F:/philosophy/西方/汉斯-格奥尔格·伽达默尔/《真理与方法》解读.pdf（692 页，文本层 599k 字）
旧数据 toc 错乱：part 排在章后、part index 乱跳、"导言"重复（chapter+part 同名）。
真实结构（目录 p30-33 + 边界页逐页验证，PDF = 印 + 33，p34=印1 起）:
  [ch] 导言 p34-43（印1-10）
  [part] 第一部分 艺术经验里真理问题的展现（标题页 p44, p45 空）
    [ch] 第一章 审美领域的超越 p46-95（3 节）
    [ch] 第二章 艺术作品的存在论及其诠释学的意义 p140-166（2 节+本部分提示）
  [part] 第二部分 真理问题扩大到精神科学里的理解问题（标题页 p206, p207 空）
    [ch] 第一章 历史的准备 p208-236（3 节）
    [ch] 第二章 一种诠释学经验理论的基本特征 p264-301（3 节+本部分提示）
  [part] 第三部分 以语言为主线的诠释学本体论转向（无标题页，直接三节，节=章级）
    [ch] 第一节~第三节 p371-468（第三节下挂本部分提示）
  [ch] 附录一：诠释学简史 p478-609（3 节: 一/二/三）
  [ch] 附录二：哲学诠释学的基本特征 p610-692（10 节: 一~十）
  SKIP: p0 封面/p1-3 书名·CIP·签名/p4-29 写在前面(前言)/p30-33 目录/p45 空/p207 空
剥除: 页眉行（页码+书名 / 部分名+页码 / 导言+页码）、纯数字页码行、
      章/节标题块（norm 匹配）、部分标题页块（第X部分 2 行）、附录标题块（2-3 行拆分）
用法: python _xr_zlff_rebuild.py [--dry]
"""
import fitz, json, os, re, sys, shutil

PDF = 'F:/philosophy/西方/汉斯-格奥尔格·伽达默尔/《真理与方法》解读.pdf'
BID = "b43aeb7ccc57"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"

doc = fitz.open(PDF)
print(f"PDF: {doc.page_count} 页")

def norm(s):
    return re.sub(r"\s+", "", s or "")

HEADER_PAT = [
    re.compile(r'^\d+\s*[《〈][^》〉]*[》〉]解读$'),     # 72《真理与方法》解读 / 14 〈真理与方法〉解读
    re.compile(r'^第[一二三]部分[^0-9]*\d+$'),           # 第一部分…73 / 第三部分…363
    re.compile(r'^第[一二三]部分[^0-9。，、：；]{0,30}$'),  # 部分名页眉拆行无页码（"第一部分 艺术经验里真理问题的展现"）
    re.compile(r'^导言\s*\d+$'),                         # 导言9 / 导言 5
    re.compile(r'^附录[一二][:：][^0-9]{0,40}\d*$'),     # 附录页眉: "附录一：诠释学简史 447" / "附录二：…基本特征—"（拆行）
]
PAGE_PAT = re.compile(r'^\d{1,3}$')

# 章标题 OCR 错字修正（正文 norm → toc 标题）
TITLE_FIX = {
    "第二章艺术作品的存在论及其诈释学的意义": "第二章 艺术作品的存在论及其诠释学的意义",
}

def page_blocks(pi):
    t = doc[pi].get_text()
    out = []
    for line in t.splitlines():
        s = line.strip()
        if not s:
            continue
        if any(p.match(s) for p in HEADER_PAT) or PAGE_PAT.match(s):
            continue
        out.append({"type": "text", "value": s})
    return out

# ---- 章节表（title, part, 页区间 [start,end), 节[(title,start,end)], 额外剥除块正则） ----
SPANS = [
    ("导言", None, 34, 44, [], [r'^导言$']),
    ("第一部分 艺术经验里真理问题的展现", "PART", 44, 46, [],
     [r'^第一部分$', r'^艺术经验里真理问题的展现$']),
    ("第一章 审美领域的超越", "第一部分 艺术经验里真理问题的展现", 46, 140, [
        ("第一节 人文主义传统对于精神科学的意义", 47, 96),
        ("第二节 康德的批判所导致的美学主观化倾向", 96, 124),
        ("第三节 艺术真理问题的重新提出", 124, 140)], []),
    ("第二章 艺术作品的存在论及其诠释学的意义", "第一部分 艺术经验里真理问题的展现", 140, 206, [
        ("第一节 作为存在论阐释入门的游戏", 140, 167),
        ("第二节 美学和诠释学的结论", 167, 194),
        ("本部分提示", 194, 206)], []),
    ("第二部分 真理问题扩大到精神科学里的理解问题", "PART", 206, 208, [],
     [r'^第二部分$', r'^真理问题扩大到精神科学里的理解问题$']),
    ("第一章 历史的准备", "第二部分 真理问题扩大到精神科学里的理解问题", 208, 264, [
        ("第一节 浪漫主义诠释学及其在历史学中的应用质疑", 210, 237),
        ("第二节 狄尔泰陷入历史主义困境", 237, 250),
        ("第三节 通过现象学研究对认识论问题的克服", 250, 264)], []),
    ("第二章 一种诠释学经验理论的基本特征", "第二部分 真理问题扩大到精神科学里的理解问题", 264, 371, [
        ("第一节 理解的历史性上升为诠释学原则", 264, 302),
        ("第二节 诠释学基本问题的重新发现", 302, 328),
        ("第三节 对效果历史意识的分析", 328, 354),
        ("本部分提示", 354, 371)], []),
    ("第三部分 以语言为主线的诠释学本体论转向", "PART", None, None, [], []),
    ("第一节 语言作为诠释学经验之媒介", "第三部分 以语言为主线的诠释学本体论转向", 371, 396, [], []),
    ("第二节 “语言”概念在西方思想史上的发展", "第三部分 以语言为主线的诠释学本体论转向", 396, 429, [], []),
    ("第三节 语言作为诠释学本体论的视域", "第三部分 以语言为主线的诠释学本体论转向", 429, 469, [
        ("本部分提示", 469, 478)], []),
    ("附录一：诠释学简史", None, 478, 610, [
        ("一、古代诠释学", 478, 484),
        ("二、近代诠释学", 484, 533),
        ("三、现代诠释学", 533, 610)],
     [r'^附录一[:：]$', r'^诠释学简史$']),
    ("附录二：哲学诠释学的基本特征——伽达默尔《真理与方法》一书梗概", None, 610, 692, [
        ("一、诠释学循环", 611, 622),
        ("二、前理解", 622, 630),
        ("三、事情本身", 630, 650),
        ("四、完满性前把握", 650, 660),
        ("五、时间距离", 660, 664),
        ("六、效果历史意识", 664, 669),
        ("七、视域融合", 669, 673),
        ("八、应用", 673, 681),
        ("九、问答结构", 681, 685),
        ("十、诠释学对话", 685, 692)],
     [r'^附录二[:：]$', r'^哲学诠释学的基本特征$', r'^伽达默尔《真理与方法》一书梗概$']),
]

# ---- 附录节标题自动提取（正文带德语括号后缀，SPANS 简洁标题 norm 无法匹配原块） ----
APPENDIX_EXTRACT = {
    "附录一：诠释学简史": (478, 610),
    "附录二：哲学诠释学的基本特征——伽达默尔《真理与方法》一书梗概": (610, 692),
}

def extract_appendix_secs(sp, ep):
    out, seen = [], set()
    for pi in range(sp, ep):
        for b in page_blocks(pi):
            v = b["value"]
            if re.match(r'^[一二三四五六七八九十]+、', v) and len(norm(v)) <= 60:
                nv = norm(v)
                if nv not in seen:
                    seen.add(nv)
                    out.append(v)
    return out

appendix_secs = {t: extract_appendix_secs(*rng) for t, rng in APPENDIX_EXTRACT.items()}

sec_norm = {norm(t): t for _, _, _, _, secs, _ in SPANS for t, _, _ in secs}
for t, ext in appendix_secs.items():
    for s in ext:
        sec_norm[norm(s)] = s

toc = []
files = {}
warns = []
junk_count = 0
total_chars = 0
ch_index = 0
for title, part, sp, ep, secs, extra in SPANS:
    if part == "PART":
        toc.append({"type": "part", "title": title, "index": ch_index, "level": 0})
        continue
    if title in appendix_secs:
        ext = appendix_secs[title]
        if len(ext) != len(secs):
            warns.append(f"!! 附录节标题数不符 {title}: 提取 {len(ext)} vs SPANS {len(secs)}")
        secs = [(t, st, en) for t, (_, st, en) in zip(ext, secs)]
    blocks = []
    junk = 0
    tnorm = norm(title)
    extra_pats = [re.compile(p) for p in extra]
    stripped_t = False
    for pi in range(sp, ep):
        for b in page_blocks(pi):
            v = b["value"]
            if not stripped_t and (norm(v) == tnorm or TITLE_FIX.get(norm(v)) == title):
                junk += 1
                stripped_t = True
                continue
            if norm(v) in sec_norm:
                junk += 1
                continue
            if any(p.match(v) for p in extra_pats):
                junk += 1
                continue
            blocks.append(b)
    if not stripped_t and not extra_pats:
        warns.append(f"!! 未剥章标题: {title}")
    junk_count += junk
    if not blocks:
        warns.append(f"!! 空章节: {title}")
        continue
    toc.append({"type": "chapter", "title": title, "index": ch_index, "level": 1})
    for si, (st, ss, se) in enumerate(secs, 1):
        toc.append({"type": "section", "title": st, "index": ch_index, "sec": si, "level": 2})
    files[ch_index] = {"index": ch_index, "title": title, "content": blocks}
    ch_index += 1

print(f"章节总数: {len(files)} | part: {sum(1 for t in toc if t['type']=='part')} | "
      f"section: {sum(1 for t in toc if t['type']=='section')} | 剥除: {junk_count} | 警告: {len(warns)}")
for w in warns:
    print("⚠", w)
for idx in sorted(files):
    ch = files[idx]
    nc = sum(len(b['value']) for b in ch['content'])
    total_chars += nc
    print(f"  {idx:2d} {ch['title'][:40]:42s} {nc:7d} 字")
print(f"\n总: {len(files)} 章, {total_chars} 字符（旧 10 章）")
for tt in toc:
    ind = '  ' * tt.get('level', 1)
    print(f"{ind}[{tt['type']} {tt.get('sec','')}] {tt['title'][:44]}")
print("首:", files[0]['title'], "| 末:", files[len(files) - 1]['title'])

if '--dry' in sys.argv:
    for idx, ch in files.items():
        for b in ch['content']:
            v = b['value']
            if re.match(r'^第[一二三]部分[^0-9是]{0,24}$', v) \
               or re.match(r'^第[一二三四五六七八九十]+章[^0-9]{0,24}$', v) \
               or re.match(r'^第[一二三四五六七八九十]+节[^0-9]{0,24}$', v) \
               or re.match(r'^附录[一二][:：][^0-9]{0,24}\d*$', v) \
               or re.match(r'^[一二三四五六七八九十]+、[^0-9，。]{0,24}[）) ]?$', v):
                print(f"⚠ 残留标题 [{idx} {ch['title'][:10]}]: {v[:36]}")
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
    "title": old_meta.get("title") or "《真理与方法》解读",
    "author": old_meta.get("author") or "何卫平",
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
