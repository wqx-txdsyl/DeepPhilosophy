# -*- coding: utf-8 -*-
"""《上帝之城》（奥古斯丁/王晓朝译）bcc83fdfca5e 重建（一次性，PDF 文本层按页切分）
pdf: F:/philosophy/西方/奥古斯丁/上帝之城.pdf（1262 页，文本层 890k 字，扫描版内置 OCR 层错字多）
旧数据 23 章 toc 全 OCR 残片（"第19节 章""第616节 一"）→ 强模式误匹配。
真实结构（目录 p3-4 + [本卷提要] 22 个卷标题页逐页验证）:
  [ch] 中译本序 p5-30（5 节: 一~五）
  [part] 第一部分（第一卷~第十卷）
  [ch] 第一卷~第十卷 p31-412
  [part] 第二部分（第十一卷~第二十二卷）
  [ch] 第十一卷~第二十二卷 p414-1254
  [ch] 译名对照表 p1255-1261
  卷标题页 = 页码 + 卷名 + [本卷提要]；卷内章标题 = "章X"独立行 + 下一行标题（或同行）。
  第一卷卷首另有无编号短标题"前言写作本书的基本设想"。
  SKIP: p0-4 封面/版权/文库序/目录
剥除: 页码行（^[0-9l]{1,4}$）、卷页眉（第X卷）、书名页眉 OCR 变体（上帝之城/上帝Z版/…/上带走戚）、
      中译本序页眉变体（中/申/甲译本廖?）、译名对照表页眉、垃圾行（单字符/脚注号）、
      卷标题页 [本卷提要] 前行、章标题块（"章X"±标题行）、卷首独立短标题（前言）、序小节标题。
用法: python _xr_shangdi_rebuild.py [--dry]
"""
import fitz, json, os, re, sys, shutil

PDF = 'F:/philosophy/西方/奥古斯丁/上帝之城.pdf'
BID = "bcc83fdfca5e"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"

doc = fitz.open(PDF)
print(f"PDF: {doc.page_count} 页")

def norm(s):
    return re.sub(r"\s+", "", s or "")

# ---- 剥除模式 ----
PAGE_PAT = re.compile(r'^[0-9l]{1,4}$')                        # 页码（l = 1 的 OCR 错字）
VOL_HEAD = re.compile(r'^第[一二三四五六七八九十百]+卷$')      # 正文页卷页眉
BOOK_HEAD = re.compile(r'^(上帝[之zZ][城顾版脑娥饿戚贼切]|上带走戚)$')  # 书名页眉 OCR 变体
PRE_HEAD = re.compile(r'^[中申甲]译本廖?$')                    # 中译本序页眉变体
YI_HEAD = re.compile(r'^译名对照[表袤]$')                      # 译名对照表页眉
GARB = re.compile(r'^[A-Za-z0-9l①-⑩]{1,3}$|^[、‘’“”•·—–-]{1,3}$|^[A-Za-z]事$|^(卷|第)$'
                  r'|^[A-Za-z]{0,2}[一-龥]{1,2}$'  # 页底 OCR 乱序单字/两字残片（"K旨""院""时"）
                  r'|^[\d\s,，.．]{2,}$')  # 名目索引页码行（"164 ,266"）
CH_PAT = re.compile(r'^[\'"“”‘’vV、·也可飞t]?\s*章([0-9lIvx]{1,3})(?:\s+(.*))?$')  # 章标题（v/、/也/飞/可/t 为 OCR 前缀变体）

def is_garbage(s):
    if PAGE_PAT.match(s) or VOL_HEAD.match(s) or PRE_HEAD.match(s) or YI_HEAD.match(s):
        return True
    if GARB.match(s):
        return True
    nv = re.sub(r'[zZ]', '之', norm(s))
    if BOOK_HEAD.match(nv):
        return True
    return False

def page_lines(pi):
    return [l.strip() for l in doc[pi].get_text().splitlines() if l.strip()]

# ---- 卷标题页（[本卷提要]）----
VOL_PAGES = [31, 79, 122, 169, 213, 263, 292, 336, 383, 414, 473, 522, 567, 608,
             662, 720, 788, 842, 925, 980, 1056, 1117]
VOL_NAMES = ["第一卷", "第二卷", "第三卷", "第四卷", "第五卷", "第六卷", "第七卷",
             "第八卷", "第九卷", "第十卷", "第十一卷", "第十二卷", "第十三卷", "第十四卷",
             "第十五卷", "第十六卷", "第十七卷", "第十八卷", "第十九卷", "第二十卷",
             "第二十一卷", "第二十二卷"]
PART1, PART2 = "第一部分", "第二部分"
VOL_END = 1192  # 22卷结束（名目索引起点，目录印1162 → PDF 1192）
IDX_END = 1246  # 名目索引结束（译名对照表起点，目录印1216 → PDF 1246）

def tizhai_idx(sp):
    """卷标题页 [本卷提要] 行索引（OCR 变体: {本卷提要]、[本卷提要}）"""
    ls = page_lines(sp)
    for i, s in enumerate(ls):
        if '本卷提要' in s:
            return i
    return -1

def page_paras(pi):
    """按空行分段的行组（[本卷提要] 段与后续标题/正文以空行分隔）"""
    paras, cur = [], []
    for l in doc[pi].get_text().splitlines():
        if l.strip():
            cur.append(l.strip())
        elif cur:
            paras.append(cur)
            cur = []
    if cur:
        paras.append(cur)
    return paras

# 卷首无编号短标题（人工核对页面原文行）: 第一卷"前言"、第三卷"章1"标题（章标记被 pymupdf 拆到页尾）
VOL_LEAD = {
    31: ["前言写作本书的基本设想"],
    122: ["这些疾苦只令恶人害怕，即使在诸神得到崇拜的时候这个世",
          "界也在不断地遭受灾难"],
}

def lead_title(sp):
    """卷标题页卷首无编号短标题（页面原文行合并为标题；行级精确剥除）"""
    return "".join(VOL_LEAD.get(sp, []))

# 章标记残片页（人工核对）: "章X"独立行被 OCR 拆到标题之后（p1125 真章6 标题在前、"章6"在后）
# 值 = (页面原文行列表, 合并标题)
CH_LEAD = {
    (1125, "6"): (["罗马人把罗莫滔造就为神，因为他们热爱他，而教会热爱墓",
                   "酱，因为款会相信他是神"],
                  "罗马人把罗莫滔造就为神，因为他们热爱他，而教会热爱墓酱，因为款会相信他是神"),
}

def ch_title_next(ls, i):
    """章X 独立行后接标题行：返回 (标题或 None, 剥除行数)。
    next 非垃圾行无条件当标题（奥古斯丁章标题 = 带逗号长句）；
    跨行标题拼接续行（≤20 字且无句末标点，如"肉身会遭…侵犯，但/灵魂是不受侵犯的"）；
    页尾无行 → 占位。"""
    j = i + 1
    while j < len(ls) and (is_garbage(ls[j]) or CH_PAT.match(ls[j])):
        j += 1
    if j >= len(ls):
        return None, 0
    title = ls[j]
    n = 1
    j += 1
    while j < len(ls):
        s2 = ls[j]
        if len(s2) <= 20 and not re.search(r'[。！？]$', s2) \
           and not is_garbage(s2) and not CH_PAT.match(s2):
            title += s2
            n += 1
            j += 1
        else:
            break
    title = re.sub(r'[①②③④⑤⑥⑦⑧⑨⑩]+$', '', title)  # 标题尾脚注号
    title = title.replace('|', '')  # OCR 竖线残片（"无区到地|随到"）
    return title, n

def vol_sections(sp, ep):
    """卷内 section 标题提取：(title, 页, 行号)，含卷首短标题 + 章X 标题
    残片过滤: 卷尾被拆行的章标记 / rest 为纯标点·数字·"以下"（"章33 。"等）/
    卷内重复章号（脚注引用行"泛见章2，3"错配的独立"章X"行）"""
    secs = []
    lt = lead_title(sp)
    if lt:
        secs.append((lt, sp, 0))
    seen_nums = set()
    for p in range(sp, ep):
        ls = page_lines(p)
        for i, s in enumerate(ls):
            m = CH_PAT.match(s)
            if not m:
                continue
            # 卷标题页末尾被拆行的章标记（p122"章1"），已由卷首标题处理
            if p == sp and sp in VOL_LEAD and i == len(ls) - 1:
                continue
            num, rest = m.group(1), m.group(2)
            # OCR 残片: "章33 。"/"章9 0"/"章236 以下。"（真实标题为长句，非标点/数字碎片）
            if rest and (re.match(r'^[。．\s]+$', rest) or re.match(r'^\d', rest)
                         or rest.startswith('以下')):
                continue
            if (p, num) in CH_LEAD:
                seen_nums.add(num)
                secs.append((CH_LEAD[(p, num)][1], p, i))
                continue
            if num in seen_nums:
                # 句号 = 0 错字（全库仅 4 处，人工核实）: "可章1。"=章10(p229)/
                # "章1。"=章10(p631)/"章2。"=章20(p365、p1158)
                if not rest and num.isdigit() and int(num) <= 9 \
                        and ls[i].rstrip().endswith('。'):
                    num = num + '0'
                else:
                    continue  # 卷内重复章号（含脚注引用"章1 ，节74"）→ 残片
            if rest:
                seen_nums.add(num)
                secs.append((s, p, i))
            else:
                seen_nums.add(num)
                t2, _ = ch_title_next(ls, i)
                if t2:
                    secs.append((t2, p, i))
                else:
                    secs.append((f"章{num}", p, i))
    out, seen = [], set()
    for t, p, i in secs:
        if (t, p) not in seen:
            seen.add((t, p))
            out.append((t, p, i))
    return out

def vol_blocks(sp, ep):
    """卷内容块提取（剥页眉/页码/垃圾/标题页[本卷提要]前行/卷首短标题/章标题块）
    标题页与正文页统一循环：提要段本身保留为内容，提要前 + 卷首标题 + 章标题块剥除"""
    blocks = []
    junk = 0
    lead_lines = VOL_LEAD.get(sp, [])
    for p in range(sp, ep):
        ls = page_lines(p)
        t = tizhai_idx(sp) if p == sp else -1
        # CH_LEAD 标题原文行预剥（章标记残片页，标题行在"章X"标记行之前）
        for k2, s2 in enumerate(ls):
            for tls, _ in CH_LEAD.values():
                if s2 in tls:
                    junk += 1
                    ls[k2] = ""
        i = 0
        while i < len(ls):
            s = ls[i]
            if not s:
                i += 1
                continue
            if p == sp and t >= 0 and i < t:
                junk += 1
                i += 1
                continue
            if s in lead_lines:
                junk += 1
                i += 1
                continue
            if is_garbage(s):
                i += 1
                continue
            m = CH_PAT.match(s)
            if m:
                junk += 1
                i += 1
                if not m.group(2):
                    _, n = ch_title_next(ls, i - 1)
                    for _ in range(n):
                        if i < len(ls):
                            junk += 1
                            i += 1
                continue
            blocks.append({"type": "text", "value": s.replace('|', '')})
            i += 1
    return blocks, junk

# ---- 章节表 ----
CHS = [  # (title, part, sp, ep, secs)  secs = [(title, sp, ep)] 页边界
    ("中译本序", None, 5, 31, [
        ("一、古罗马帝国的兴盛与衰败", 5, 12),
        ("二、奥古斯丁生平概要", 12, 17),
        ("三、奥古斯丁的著作与版本", 17, 20),
        ("四、《上帝之城》的写作动因与逻辑结构", 20, 26),
        ("五、研究动态与思想价值", 26, 31)]),
]
for i, vp in enumerate(VOL_PAGES):
    pt = PART1 if i < 10 else PART2
    ep = VOL_PAGES[i + 1] if i + 1 < len(VOL_PAGES) else VOL_END
    CHS.append((VOL_NAMES[i], pt, vp, ep, None))
CHS.append(("名目索引", None, 1192, IDX_END, None))
CHS.append(("译名对照表", None, 1246, 1262, None))

sec_norm = {}
for t, pt, sp, ep, secs in CHS:
    if secs:
        for st, ss, se in secs:
            sec_norm[norm(st)] = st

toc = []
files = {}
warns = []
junk_count = 0
total_chars = 0
ch_index = 0
pending_part = None
for title, pt, sp, ep, secs in CHS:
    if pt and pt != pending_part:
        toc.append({"type": "part", "title": pt, "index": ch_index, "level": 0})
        pending_part = pt
    if secs is not None:
        blocks = []
        junk = 0
        for p in range(sp, ep):
            for s in page_lines(p):
                if is_garbage(s) or norm(s) in sec_norm:
                    junk += 1
                    continue
                blocks.append({"type": "text", "value": s.replace('|', '')})
        junk_count += junk
    else:
        blocks, junk = vol_blocks(sp, ep)
        junk_count += junk
        vs = vol_sections(sp, ep)
        secs = []
        for k, (t, p, i) in enumerate(vs):
            se = vs[k + 1][1] if k + 1 < len(vs) else ep
            secs.append((t, p, se))
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
print(f"\n总: {len(files)} 章, {total_chars} 字符（旧 890799）")
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

if '--dry' in sys.argv:
    n_res = 0
    for idx, ch in files.items():
        for b in ch['content']:
            v = b['value']
            if CH_PAT.match(v) or (re.match(r'^[一二三四五六七八九十]+、', v) and len(norm(v)) <= 25):
                print(f"⚠ 残留标题 [{idx} {ch['title'][:10]}]: {v[:36]}")
                n_res += 1
    print(f"残留: {n_res}")
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
    "title": old_meta.get("title") or "上帝之城",
    "author": old_meta.get("author") or "奥古斯丁",
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
