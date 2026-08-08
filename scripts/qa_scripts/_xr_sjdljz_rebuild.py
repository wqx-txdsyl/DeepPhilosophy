# -*- coding: utf-8 -*-
"""《世界的逻辑构造》（卡尔纳普/陈启伟译）8ae083851bd8 重建（一次性，EPUB spine 事件流）
epub: F:/philosophy/西方/鲁道夫·卡尔纳普/世界的逻辑构造.epub（无 OCR，直接提取）
旧数据 28 章 toc 全乱：五个部分被压成 chapter、缺各"第一章"、非编号小节被提升为 chapter、第X节未入 toc。
真实结构（TOC.xhtml 完整目录 + 4 个 spine 文件 h1/h2/h3 标签验证）:
  [ch] Digital Lab简介 / 中译本序 / 第一版序 / 第二版序 / 第二版序所引书目（1966年）/ 第三版弁言（h1）
  [part] 第一部分 绪论 研究的任务和计划:  第一章 任务(1-5) / 第二章 研究计划(6-9)
  [part] 第二部分 预备性的讨论:          第一章 论科学命题的形式(10-16) / 第二章 对象种类及其关系概述(17-25)
  [part] 第三部分 构造系统的形式问题:    第一章 等级形式(26-45) / 第二章 系统形式(一 形式的研究+46-53 / 二 实质的研究+54-60)
                                        / 第三章 基础(一 基本要素+61-74 / 二 基本关系+75-83) / 第四章 对象形式(84-94)
                                        / 第五章 一个构造系统的表达形式(95-105)
  [part] 第四部分 一个构造系统的纲要:    第一章 低等级(106-122) / 第二章 中间等级(123-138) / 第三章 高等级(139-156)
  [part] 第五部分 根据构造理论对若干哲学问题的澄清: 第157节 构造理论是哲学研究的基础(无章，独立 chapter)
                                        / 第一章 关于本质的几个问题(158-165) / 第二章 心物问题(166-169)
                                        / 第三章 构造的或经验的实在问题(170-174) / 第四章 形而上学的实在问题(175-178)
                                        / 第五章 科学的任务和限度(179-183)
  [ch] 本书提要 / 人名书名索引
标签: h1=前置章/部分/提要/索引（按标题区分）, h2=章, h3=节（第X节 + 非编号小节"一 形式的研究"等 4 个，印刷 TOC 均列出）
剥除: h1/h2/h3 标签文本（章节边界）、h1/h2 标签后 p 重复标题行（EPUB 制作遗留，norm 命中标题集合）、
      "未知"残片（每 split 文件开头）、节标题尾注号（"第13节 关于限定摹状词[1]"）。
用法: python _xr_sjdljz_rebuild.py [--dry]
"""
import html, json, os, re, sys, shutil, zipfile

BID = "8ae083851bd8"
EPUB = "F:/philosophy/西方/鲁道夫·卡尔纳普/世界的逻辑构造.epub"
SPINE = ["OEBPS/Text/Section0001_split_000.xhtml", "OEBPS/Text/Section0001_split_001.xhtml",
         "OEBPS/Text/Section0001_split_002.xhtml", "OEBPS/Text/Section0001_split_003.xhtml"]
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

def norm(s):
    return re.sub(r"\s+", "", s or "")

# ---- TOC.xhtml 节标题（1-183）----
z = zipfile.ZipFile(EPUB)
toc_html = z.read("OEBPS/Text/TOC.xhtml").decode("utf-8", errors="replace")
toc_text = html.unescape(re.sub(r"<[^>]+>", "", toc_html))
# "第X章/部分"算边界；节标题内部出现"第X部分"必带"（本书"前缀，排除前字符"书"。
# （TOC 剥离标签后章标题与上节标题同行无分隔，不能按行首/空白判定）
BOUND = (r"(?=第\d+节|(?<!书)第[一二三四五六七八九十]+(?:章|部分)"
         r"|一 形式的研究|二 实质的研究|一 基本要素|二 基本关系"
         r"|本书提要|人名书名索引|$)")
SEC_183 = {}
for m in re.finditer(r"第(\d+)节\s*(.*?)" + BOUND, toc_text):
    SEC_183[int(m.group(1))] = m.group(2).strip()
assert len(SEC_183) == 183, f"TOC 节数异常: {len(SEC_183)}"

# ---- 章节表（title, part, secs=[节号或非编号标题]）----
CHS = [
    ("Digital Lab简介", None, []),
    ("中译本序", None, []),
    ("第一版序", None, []),
    ("第二版序", None, []),
    ("第二版序所引书目（1966年）", None, []),
    ("第三版弁言", None, []),
    ("第一章 任务", "第一部分 绪论 研究的任务和计划", list(range(1, 6))),
    ("第二章 研究计划", "第一部分 绪论 研究的任务和计划", list(range(6, 10))),
    ("第一章 论科学命题的形式", "第二部分 预备性的讨论", list(range(10, 17))),
    ("第二章 对象种类及其关系概述", "第二部分 预备性的讨论", list(range(17, 26))),
    ("第一章 等级形式", "第三部分 构造系统的形式问题", list(range(26, 46))),
    ("第二章 系统形式", "第三部分 构造系统的形式问题", ["一 形式的研究"] + list(range(46, 54)) + ["二 实质的研究"] + list(range(54, 61))),
    ("第三章 基础", "第三部分 构造系统的形式问题", ["一 基本要素"] + list(range(61, 75)) + ["二 基本关系"] + list(range(75, 84))),
    ("第四章 对象形式", "第三部分 构造系统的形式问题", list(range(84, 95))),
    ("第五章 一个构造系统的表达形式", "第三部分 构造系统的形式问题", list(range(95, 106))),
    ("第一章 低等级：自我心理对象", "第四部分 一个构造系统的纲要", list(range(106, 123))),
    ("第二章 中间等级：物理对象", "第四部分 一个构造系统的纲要", list(range(123, 139))),
    ("第三章 高等级：他人心理对象和精神对象", "第四部分 一个构造系统的纲要", list(range(139, 157))),
    ("第157节 构造理论是哲学研究的基础", "第五部分 根据构造理论对若干哲学问题的澄清", []),
    ("第一章 关于本质的几个问题", "第五部分 根据构造理论对若干哲学问题的澄清", list(range(158, 166))),
    ("第二章 心物问题", "第五部分 根据构造理论对若干哲学问题的澄清", list(range(166, 170))),
    ("第三章 构造的或经验的实在问题", "第五部分 根据构造理论对若干哲学问题的澄清", list(range(170, 175))),
    ("第四章 形而上学的实在问题", "第五部分 根据构造理论对若干哲学问题的澄清", list(range(175, 179))),
    ("第五章 科学的任务和限度", "第五部分 根据构造理论对若干哲学问题的澄清", list(range(179, 184))),
    ("本书提要", None, []),
    ("人名书名索引", None, []),
]
# 期望节标题（norm 完整形式「第X节 标题」→ 完整原文；非编号小节直接记）
EXPECT = {}
for ct, pt, secs in CHS:
    for s in secs:
        if isinstance(s, int):
            full = f"第{s}节 {SEC_183[s]}"
            EXPECT[norm(full)] = full
        else:
            EXPECT[norm(s)] = s

# ---- 解析 spine → 事件流 (tag, text) ----
TAG_RE = re.compile(r"<(h[123])[^>]*>(.*?)</\1>", re.S)
def strip_tags(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s))

events = []
for fn in SPINE:
    t = z.read(fn).decode("utf-8", errors="replace")
    pos = 0
    for m in TAG_RE.finditer(t):
        pre = strip_tags(t[pos:m.start()])
        if pre.strip():
            events.append(("text", pre))
        events.append((m.group(1), strip_tags(m.group(2)).strip()))
        pos = m.end()
    tail = strip_tags(t[pos:])
    if tail.strip():
        events.append(("text", tail))

# 标题集合（剥重复行用；part 标题单独成集——h1 事件流中出现但归属由 open_ch 经 pt 字段自动处理）
TITLE_NORM = {norm(ct) for ct, pt, secs in CHS}
for s in EXPECT:
    TITLE_NORM.add(norm(EXPECT[s]))
PART_NORM = {norm(pt) for ct, pt, secs in CHS if pt}

# ---- 切分 ----
toc = []
files = {}
ch_index = 0
pending_part = None
cur_secs = []      # 当前章已收集节标题
cur_blocks = []
cur_title = None
cur_sec_count = 0
warns = []
junk_count = 0
cur_ch = 0
sec_collected = []  # 当前章节标题（按出现序）

def flush_ch():
    global cur_blocks, ch_index
    if cur_blocks or sec_collected:
        files[ch_index] = {"index": ch_index, "title": cur_title, "content": cur_blocks}
        toc.append({"type": "chapter", "title": cur_title, "index": ch_index, "level": 1})
        for si, st in enumerate(sec_collected, 1):
            toc.append({"type": "section", "title": st, "index": ch_index, "sec": si, "level": 2})
        ch_index += 1

def open_ch(ci, title):
    global cur_blocks, cur_sec_count, cur_title, pending_part
    flush_ch()
    ct, pt, secs = CHS[ci]
    cur_title = ct
    cur_blocks = []
    cur_sec_count = 0
    sec_collected.clear()
    if pt and pt != pending_part:
        toc.append({"type": "part", "title": pt, "index": ch_index, "level": 0})
        pending_part = pt

open_ch(0, CHS[0][0])
h3_as_ch = norm("第157节 构造理论是哲学研究的基础")
for tag, text in events:
    if tag in ("h1", "h2"):
        nv = norm(text)
        if nv in PART_NORM:
            continue  # part 标题，不切章
        if nv in TITLE_NORM:
            # 找对应章
            ci = next(i for i, (ct, pt, secs) in enumerate(CHS) if norm(ct) == nv)
            open_ch(ci, text)
        else:
            warns.append(f"⚠ 未知 h1/h2 标题: {text[:40]}")
        continue
    if tag == "h3":
        t2 = re.sub(r"\[\d+\]$", "", text).strip()  # 剥尾注号
        nv = norm(t2)
        if nv in EXPECT:
            sec_collected.append(EXPECT[nv])
        elif nv == h3_as_ch:
            # 第157节 → 独立章（第五部分下无章标题）
            ci = next(i for i, (ct, pt, secs) in enumerate(CHS) if norm(ct) == nv)
            open_ch(ci, t2)
        else:
            warns.append(f"⚠ 未知 h3 标题: {t2[:40]}")
        continue
    # text 块
    for raw in text.split("\n"):
        s = raw.strip()
        if not s:
            continue
        nv = norm(s)
        if nv == "未知":
            junk_count += 1
            continue
        if nv in TITLE_NORM:
            junk_count += 1  # h1/h2 后的 p 重复标题行
            continue
        cur_blocks.append({"type": "text", "value": s})
flush_ch()  # 收尾

# ---- 校验 ----
sec_n = 0
for ci, (ct, pt, secs) in enumerate(CHS):
    got = [t["title"] for t in toc if t["type"] == "section" and t["index"] == ci]
    exp = [f"第{s}节 {SEC_183[s]}" if isinstance(s, int) else s for s in secs]
    if got != exp:
        for g, e in zip(got, exp):
            if g != e:
                warns.append(f"⚠ [{ci} {ct[:12]}] 节序: 期望「{e[:24]}」实得「{g[:24]}」")
        if len(got) != len(exp):
            warns.append(f"⚠ [{ci} {ct[:12]}] 节数 {len(got)} ≠ 期望 {len(exp)}")
    sec_n += len(secs)

total_chars = 0
for idx in sorted(files):
    nc = sum(len(b["value"]) for b in files[idx]["content"])
    total_chars += nc
    print(f"  {idx:2d} {files[idx]['title'][:42]:44s} {nc:7d} 字")
print(f"总: {len(files)} 章 + {sum(1 for t in toc if t['type']=='part')} part, {sec_n} 节, {total_chars} 字符（旧 28 章）")
old_total = 0
if os.path.isdir(SRC):
    for fn in os.listdir(SRC):
        if fn.endswith('.json') and fn != 'meta.json':
            ch = json.load(open(os.path.join(SRC, fn), encoding='utf-8'))
            old_total += sum(len(b.get('value', '')) for b in ch.get('content', []))
print(f"旧数据总字数: {old_total}")
for tt in toc:
    ind = '  ' * tt.get('level', 1)
    print(f"{ind}[{tt['type']} {tt.get('sec','')}] {tt['title'][:44]}")
print("首:", files[0]['title'], "| 末:", files[len(files) - 1]['title'])
for w in warns:
    print("⚠", w)

if "--dry" in sys.argv:
    n_res = 0
    for idx, ch in files.items():
        for b in ch["content"]:
            v = b["value"]
            nv = norm(v)
            if nv in TITLE_NORM or nv == "未知":
                print(f"⚠ 残留标题 [{idx} {ch['title'][:10]}]: {v[:36]}")
                n_res += 1
    print(f"残留: {n_res} | 警告: {len(warns)}")
    sys.exit(0)

# ---- 写入 ----
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
    "title": old_meta.get("title") or "世界的逻辑构造",
    "author": old_meta.get("author") or "鲁道夫·卡尔纳普",
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
print("✓ 同步 DP chapters")

for p in (DETAIL_SRC, DETAIL_DST):
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))
        d["toc"] = toc
        d["chapterCount"] = len(files)
        d["chapterTitles"] = [ch["title"] for ch in files.values()]
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
        print(f"✓ book_detail 更新: {p}")

if os.path.exists(BOOKS_JSON):
    bj = json.load(open(BOOKS_JSON, encoding="utf-8"))
    bl = bj if isinstance(bj, list) else bj.get("books", [])
    for b in bl:
        if b.get("id") == BID:
            b["chapterCount"] = len(files)
    with open(BOOKS_JSON, "w", encoding="utf-8") as f:
        json.dump(bl if isinstance(bj, list) else {**bj, "books": bl}, f, ensure_ascii=False, indent=None)
    print("✓ books.json chapterCount 更新")
