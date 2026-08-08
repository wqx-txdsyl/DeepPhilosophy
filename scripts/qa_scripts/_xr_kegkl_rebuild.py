# -*- coding: utf-8 -*-
"""《最伟大的思想家 - 克尔恺廓尔》（安德森/瞿旭彤译）add6c213fde8 重建（一次性，PDF 文本层按页切分）
pdf: F:/philosophy/西方/索伦·克尔凯郭尔/最伟大的思想家 - 克尔恺廓尔.pdf（107 页，文本层 6.8w 字）
旧数据 6 章 toc 全 OCR 残片（"第183节 哩年…""第3节 理就"）→ 强模式误匹配。
真实结构（目录 p3-4 逐页核对，PDF = 印 + 4，印1 = PDF5）:
  [ch] 1 克尔恺廓尔的生平 p5-29（印1-25，无节）
  [ch] 2 克尔恺廓尔的哲学 p30-92（印26-88）
    [sec] 2.1 导论 p30-32
    [sec] 2.2 克尔恺廓尔反对什么 p33-38（三级小标题: 黑格尔/成为信徒的必要条件的观点/现时代/任何时代的潮流/讨论题，保留正文）
    [sec] 2.3 克尔恺廓尔哲学的主题 p39-92（三级小标题: 个体主义/真理即主观性/非此即彼/生存的三层面/信仰/心灵的清洁/激情/赢得自我/讨论题，保留正文）
  [ch] 3 克尔恺廓尔哲学的重要性 p93-103（印89-99）
    [sec] 讨论题 p102-103
  [ch] 参考书目 p104-105（印100-101）
  SKIP: p0-2 封面/书名/CIP、p3-4 目录、p106 丛书宣传页
剥除: 页码行（^[0-9]{1,3}$）、页眉两系（偶数页"×思想×译丛"变体 / 奇数页"《克尔/莞尔×廓尔》"书名 OCR 变体）、
      章标题块（"1 克尔'皑廓尔的生平"/"2 克尔'f岂廓尔的哲学"/"3 克尔'皑廓尔哲学/的重要性"/"参考书目"）、
      节标题块（2.1 导论/2.2 克尔×反对什么/2.3 克尔×主题/讨论题[仅章3]）。
用法: python _xr_kegkl_rebuild.py [--dry]
"""
import fitz, json, os, re, sys, shutil

PDF = 'F:/philosophy/西方/索伦·克尔凯郭尔/最伟大的思想家 - 克尔恺廓尔.pdf'
BID = "add6c213fde8"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"

doc = fitz.open(PDF)
print(f"PDF: {doc.page_count} 页")

def norm(s):
    return re.sub(r"\s+", "", s or "")

# ---- 剥除模式 ----
PAGE_PAT = re.compile(r'^\d{1,3}$')                                  # 页码
YI_HEAD = re.compile(r'^[·•\s]{0,2}[^·•]{2,16}(译丛|思想)[^·•]{0,4}[·•－\s]{0,2}$')  # 偶数页页眉（×思想×译丛 变体）
BK_HEAD = re.compile(r'^[·•E’“〈f\s]{0,2}[《〈（｛]?[^·•，。；：！？]{2,12}[》〉）｝]?[·•－’]{0,2}$')  # 奇数页书名页眉
def is_header(s):
    if YI_HEAD.match(s) and len(norm(s)) <= 20:
        return True
    if BK_HEAD.match(s) and len(s) <= 16 and re.search(r'(尔|皑|廓|廊|鹏|鹰|属)', s):
        return True
    return False

# 章标题块（OCR 变体: 皑=恺、'f岂/吉=哲）
CH_PATS = [
    re.compile(r"^克尔['’\w]{0,4}廓尔的生平$"),      # 1 生平
    re.compile(r"^克尔['’\w]{0,4}廓尔的哲学$"),      # 2 哲学
    re.compile(r"^克尔['’\w]{0,4}廓尔哲学$"),        # 3 重要性（跨行第 1 行）
    re.compile(r"^的重要性$"),                       # 3 跨行第 2 行
    re.compile(r"^参考书目$"),
]
# 节标题块（2.1/2.2/2.3 正则适配 OCR；"讨论题"仅章3 页内剥）
SEC_PATS = [
    re.compile(r'^2\s*[.．]\s*1\s*导论$'),
    re.compile(r'^2\s*[.．]\s*2\s*克尔[\S]{0,4}廓尔反对什么$'),
    re.compile(r'^2\s*[.．]\s*3\s*克尔[\S]{0,4}廓尔[\S]{0,5}学的主题$'),
]

def page_lines(pi):
    return [l.strip() for l in doc[pi].get_text().splitlines() if l.strip()]

# ---- 章节表（title, part, 页区间 [sp,ep), 节[(title, sp, ep)]） ----
CHS = [
    ("1 克尔恺廓尔的生平", None, 5, 30, []),
    ("2 克尔恺廓尔的哲学", None, 30, 93, [
        ("2.1 导论", 30, 33),
        ("2.2 克尔恺廓尔反对什么", 33, 39),
        ("2.3 克尔恺廓尔哲学的主题", 39, 93)]),
    ("3 克尔恺廓尔哲学的重要性", None, 93, 104, [
        ("讨论题", 102, 104)]),
    ("参考书目", None, 104, 106, []),
]

sec_norm = {}
for _, _, _, _, secs in CHS:
    for st, ss, se in secs:
        sec_norm[norm(st)] = st

toc = []
files = {}
warns = []
junk_count = 0
total_chars = 0
ch_index = 0
for title, pt, sp, ep, secs in CHS:
    blocks = []
    junk = 0
    for pi in range(sp, ep):
        for s in page_lines(pi):
            if PAGE_PAT.match(s):
                junk += 1
                continue
            if is_header(s):
                junk += 1
                continue
            if any(p.match(s) for p in CH_PATS):
                junk += 1
                continue
            if any(p.match(s) for p in SEC_PATS):
                junk += 1
                continue
            if norm(s) in sec_norm:
                junk += 1
                continue
            blocks.append({"type": "text", "value": s})
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
print(f"\n总: {len(files)} 章, {total_chars} 字符（旧 6 章 65953）")
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
            if is_header(v) or any(p.match(v) for p in CH_PATS + SEC_PATS) \
               or (re.match(r'^\d{1,3}$', v)):
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
    "title": old_meta.get("title") or "克尔恺廓尔",
    "author": old_meta.get("author") or "苏珊·李·安德森",
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
