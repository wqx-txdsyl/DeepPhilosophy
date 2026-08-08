# -*- coding: utf-8 -*-
"""《反对方法》（费耶阿本德/周昌忠译）744757b853eb 重建（一次性，ckpt ocr 页级文本）
pdf: F:/philosophy/西方/保罗·费耶阿本德/反对方法.pdf（290 页，无文本层，OCR 已完成）
本书从 ckpt 的 ocr 键直接读页级文本重建（281 页成功，失败 [281-289] 书末待全量后补，本脚本打印缺口警告）。
旧数据 10 章 toc 全乱：脚注残片当章名（"第2章最后一个注。""第4卷，格丁根，1800年，第60页意评。）"）。
真实结构（分析索引 p16-20 摘要与正文章首引文逐字一致 + 每章首页首行章号，PDF = 印 + 20）:
  [ch] 导言 p10-15（罗马页码，p10"导言"标题 + 布莱希特题词）
  [ch] 分析索引 p16-20（"作为对主要论点的概述"，各章摘要+指引线）
  [ch] 第1章~第18章 p21-280（章首页 = 章号行 + 章首引文 = 分析索引摘要；正文无章标题，全书章为编号制）
  正文中穿插 5 篇附录（"详见本章附录1"式章内附录）:
    附录1 p105-107（第9章内）、附录2 p108-109（第9章内）、附录3 p203-208（第16章内）、
    附录4 p209-210（第16章内）、附录5 p273-274（第17章内）
  SKIP: p0-2 封面/CIP、p3-7 译者的话、p8 献词、p9 前言
剥除: 页码行（页尾 ^·N 或丢点变体 ^N / 罗马数字残片 I/V/Y）、
      章号行（每章首页首部 1-18 独立数字行）、分析索引指引线（^*.*数字* 变体）、
      标题行（导言/分析索引/作为对主要论点的概述/目次：/导盲.../附录X）、
      残片行（单标点行、单字母数字行）。
用法: python _xr_fandui_rebuild.py [--dry]
"""
import json, os, re, sys, shutil

BID = "744757b853eb"
CKPT = 'f:/program/Python/PhiAgent/backend/data/dp_pdf_import_ckpt.json'
OCR_KEY = '西方_保罗_费耶阿本德_反对方法.pdf'
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"

def norm(s):
    return re.sub(r"\s+", "", s or "")

# ---- 页码（页尾行）----
PAGE_DIGIT = re.compile(r'^[·•.．:：+。]{0,2}\d{1,4}[·•.．:：。?？]?$')  # "·1" / "26" / "115" / ".·128" / "+137" / "89?" 页码 OCR 变体
PAGE_ROMAN = re.compile(r'^[IVXlY·•]{1,4}$')          # 导言罗马页码残片（"I"/"Y"=V错字）

# ---- 分析索引指引线 ----
GUIDE = re.compile(r'^[.*·\s]{2,}\d{1,4}$|^\d{1,4}\s*[.*·]{2,}$')   # "*****.**.12" / "...........33"
GUIDE_NUM = re.compile(r'^(?:[1-9]|1[0-9])[.．·]{1,4}$')            # "13......." 章号指引线残片
GUIDE_APX = re.compile(r'^附录[1-5][.．·]{1,4}$')                    # "附录1...." / "附录2.."

# ---- 残片行 ----
PUNC_ONLY = re.compile(r'^[：:；;。．,，、]{1,4}$')      # p116 首行"：" / 单顿号行
SHORT_ALN = re.compile(r'^[A-Za-z0-9]{1,2}$')          # "1"/"D" OCR 残片（本书脚注用圈号，独立阿拉伯行 = 残片）

# 标题行（norm 精确剥除）
TITLE_NORM = {
    "导言", "分析索引", "作为对主要论点的概述",
    "目次：", "导盲...", "附录1", "附录2", "附录3", "附录4", "附录5",
}

# ---- 章节表（title, 页区间 [sp,ep), 排除页区间列表[exclude]）----
CHS = [
    ("导言", 10, 16, []),
    ("分析索引", 16, 21, []),
    ("第1章", 21, 27, []),
    ("第2章", 27, 32, []),
    ("第3章", 32, 44, []),
    ("第4章", 44, 51, []),
    ("第5章", 51, 65, []),
    ("第6章", 65, 77, []),
    ("第7章", 77, 89, []),
    ("第8章", 89, 95, []),
    ("第9章", 95, 116, [(105, 110)]),      # 挖出附录1/2
    ("附录1", 105, 108, []),
    ("附录2", 108, 110, []),
    ("第10章", 116, 133, []),
    ("第11章", 133, 136, []),
    ("第12章", 136, 151, []),
    ("第13章", 151, 153, []),
    ("第14章", 153, 158, []),
    ("第15章", 158, 168, []),
    ("第16章", 168, 211, [(203, 210)]),    # 挖出附录3/4
    ("附录3", 203, 209, []),
    ("附录4", 209, 211, []),
    ("第17章", 211, 275, [(273, 275)]),    # 挖出附录5
    ("附录5", 273, 275, []),
    ("第18章", 275, 281, []),
]

# 章首页章号行（sp → 章号字符）；ch1 p21 无章号、ch7 p77 无章号
CH_NUM = {27: "2", 32: "3", 44: "4", 51: "5", 65: "6", 89: "8", 95: "9",
          116: "10", 133: "11", 136: "12", 151: "13", 153: "14", 158: "15",
          168: "16", 211: "17", 275: "18"}

ck = json.load(open(CKPT, encoding='utf-8'))
pages = {int(x): t for x, t in ck['ocr'][OCR_KEY].items()}
n_fail = sum(1 for t in pages.values() if t == '__FAILED__')
print(f"ckpt 页数: {len(pages)} | 失败页: {n_fail}")

def page_lines(pi):
    return [l.strip() for l in pages.get(pi, '').split('\n') if l.strip()]

toc = []
files = {}
warns = []
junk_count = 0
total_chars = 0
ch_index = 0
for title, sp, ep, exc in CHS:
    blocks = []
    junk = 0
    missing = []
    chnum = CH_NUM.get(sp)
    for pi in range(sp, ep):
        if any(a <= pi < b for a, b in exc):
            continue  # 被挖出的附录区间
        t = pages.get(pi)
        if t == '__FAILED__' or t is None:
            missing.append(pi)
            continue
        ls = page_lines(pi)
        for li, s in enumerate(ls):
            is_last = (li == len(ls) - 1)
            if chnum and pi == sp and li < 3 and s == chnum:
                junk += 1
                continue
            if PAGE_DIGIT.match(s) or PAGE_ROMAN.match(s):
                # 页码行全局剥除（OCR 块序乱，页码块不总在页尾）
                junk += 1
                continue
            if title == "分析索引":
                if GUIDE.match(s) or GUIDE_NUM.match(s) or GUIDE_APX.match(s):
                    junk += 1
                    continue
            if norm(s) in TITLE_NORM:
                junk += 1
                continue
            if PUNC_ONLY.match(s) or SHORT_ALN.match(s):
                junk += 1
                continue
            blocks.append({"type": "text", "value": s})
    if missing:
        warns.append(f"⚠ 缺失页 {title}: {missing}")
    junk_count += junk
    if not blocks:
        warns.append(f"!! 空章节: {title}")
        continue
    toc.append({"type": "chapter", "title": title, "index": ch_index, "level": 1})
    files[ch_index] = {"index": ch_index, "title": title, "content": blocks}
    ch_index += 1

print(f"章节总数: {len(files)} | 剥除: {junk_count} | 警告: {len(warns)}")
for w in warns:
    print(w)
for idx in sorted(files):
    ch = files[idx]
    nc = sum(len(b['value']) for b in ch['content'])
    total_chars += nc
    print(f"  {idx:2d} {ch['title'][:40]:42s} {nc:7d} 字")
print(f"\n总: {len(files)} 章, {total_chars} 字符（旧 10 章）")
old_total = 0
if os.path.isdir(SRC):
    for fn in os.listdir(SRC):
        if fn.endswith('.json') and fn != 'meta.json':
            ch = json.load(open(os.path.join(SRC, fn), encoding='utf-8'))
            old_total += sum(len(b.get('value', '')) for b in ch.get('content', []))
print(f"旧数据总字数: {old_total}")
for tt in toc:
    print(f"  [{tt['type']}] {tt['title']}")
print("首:", files[0]['title'], "| 末:", files[len(files) - 1]['title'])

if '--dry' in sys.argv:
    n_res = 0
    for idx, ch in files.items():
        for b in ch['content']:
            v = b['value']
            if norm(v) in TITLE_NORM:
                print(f"⚠ 残留标题 [{idx} {ch['title'][:10]}]: {v[:36]}")
                n_res += 1
                continue
            if GUIDE.match(v) or GUIDE_NUM.match(v) or GUIDE_APX.match(v) \
               or PUNC_ONLY.match(v) or SHORT_ALN.match(v) \
               or (len(v) <= 5 and (PAGE_DIGIT.match(v) or PAGE_ROMAN.match(v))):
                print(f"⚠ 残留垃圾行 [{idx} {ch['title'][:10]}]: {v[:36]}")
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
    "title": old_meta.get("title") or "反对方法",
    "author": old_meta.get("author") or "保罗·费耶阿本德",
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
