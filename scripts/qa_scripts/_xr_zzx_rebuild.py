# -*- coding: utf-8 -*-
"""#126 政治学（亚里士多德，吴寿彭译，商务"汉译世界学术名著丛书"本）53b09f03e24e 重建
病因（CHKLIST ✗B 卷下无章）:
  旧数据 8 文件 = 8 卷平铺，toc 每卷 part"第N卷" + chapter"第N卷"重复，卷下无章。
OCR 源（dp_pdf_import_ckpt.json，527/527 页 100%）结构:
  P0-1 书名页 / P2-17 吴恩裕《论亚里士多德的〈政治学〉》序言 / P18 书前目录 /
  P19-496 正文八卷（卷标行"卷（X）N" + 章一~章X）/ P497+ 书末附录"本书章节摘要"（不入正文）。
重建:
  [ch] 论亚里士多德的《政治学》（序言 P2-17，每页一块）
  [part l0] 第一卷~第八卷 ×8（卷标行触发）
    [ch] 第一章~第X章 ×103（章标题行"章X"，卷内中文数字编号；
         标题行剥离，粘连正文首句入章内容；注释行"章X。"保留正文）
  页内行: 过滤页眉"政治学"/页码(纯1-3位数字)/卷标行; 每页正文行拼接为一块。
  cc 8 → 104（1 序言 + 103 章）。
用法: python _xr_zzx_rebuild.py [--dry]
"""
import json, os, re, sys, shutil

BID = "53b09f03e24e"
CK = "f:/program/Python/PhiAgent/backend/data/dp_pdf_import_ckpt.json"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"
CHKLIST = "f:/program/Python/PhiAgent/backend/tools/CHKLIST.md"

def norm(s):
    return re.sub(r"\s+", "", s or "")

ck = json.load(open(CK, encoding="utf-8"))
v = ck["ocr"]["西方_亚里士多德_政治学.pdf"]

CH_TEXT = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "七", 8: "八",
           9: "九", 10: "十", 11: "十一", 12: "十二", 13: "十三", 14: "十四",
           15: "十五", 16: "十六", 17: "十七", 18: "十八"}

def is_page_num(l):
    return re.fullmatch(r"\d{1,3}", l) is not None

def is_header(l):
    return l == "政治学"

def is_vol_line(l):
    return re.match(r"^卷[（(][^)）]*[)）][一二三四五六七八九十]*$", l) is not None

def page_lines(p):
    return [l.strip() for l in v[str(p)].split("\n") if l.strip()]

# ---- 卷/章结构表（探针已验证: 8 卷 103 章连续）----
vols = []      # (页, 卷号)
chaps = []     # (页, 卷号, 章序号, 粘连正文)
CH_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8,
          "九": 9, "十": 10, "十一": 11, "十二": 12, "十三": 13, "十四": 14,
          "十五": 15, "十六": 16, "十七": 17, "十八": 18}
for p in sorted(v, key=int):
    pn = int(p)
    if pn < 19 or pn > 496:
        continue
    for l in page_lines(p):
        if is_vol_line(l):
            vols.append((pn, len(vols) + 1))
            continue
        m = re.match(r"^(章[一二三四五六七八九十]+-?[一二三四五六七八九十]?)\s*", l)
        if m:
            z = m.group(1)
            rest = l[len(z):]
            # 注释行: 后接阿拉伯数字/标点/括号（纯"①"=标题行注标噪音, 保留为标题）
            if rest and (rest[0] in "0123456789" or rest[0] in "。，、；：）〕」】"):
                continue
            zz = "章十一" if z == "章十-" else z
            num = CH_NUM.get(zz[1:])
            if num is None:
                continue
            chaps.append((pn, len(vols) - 1, num, rest))   # 卷号 0-based
assert len(vols) == 8, len(vols)
# 卷内章序去重 + 连续验证
chans = {}   # 卷号 -> [章序号]
seen = set()
for c in chaps:
    if c[1] not in chans:
        chans[c[1]] = []
    if c[2] in chans[c[1]]:
        continue   # 重复章号 = 注释/引用
    chans[c[1]].append(c[2])
for vi in range(8):
    seq = chans[vi]
    assert seq == list(range(1, len(seq) + 1)), (vi, seq)
VOL_CH = [len(chans[i]) for i in range(8)]
assert VOL_CH == [13, 12, 18, 16, 12, 8, 17, 7], VOL_CH

# ---- 组装 ----
toc = []
files = {}
idx = 0

def push_ch(title, blocks):
    global idx
    files[idx] = {"index": idx, "title": title, "content": blocks}
    toc.append({"type": "chapter", "title": title, "index": idx, "level": 1})
    idx += 1

# 序言章（P2-17，每页一块；P2 剥离章标题行，保留作者行）
pre_blocks = []
for p in range(2, 18):
    body = []
    for l in page_lines(p):
        if is_page_num(l) or is_header(l):
            continue
        if p == 2 and norm(l) == "论亚里土多德的《政治学》":
            continue
        body.append(l)
    if body:
        pre_blocks.append({"type": "text", "value": "".join(body)})
push_ch("论亚里士多德的《政治学》", pre_blocks)

# 八卷（流式逐行: 章标题行 = 页内位置切章; 卷标行所在页 = part 切卷）
CH_RE = re.compile(r"^(章[一二三四五六七八九十]+-?[一二三四五六七八九十]?)\s*")

def is_ch_comment(l):
    m = CH_RE.match(l)
    if not m:
        return False
    r = l[len(m.group(0)):]
    return bool(r) and (r[0] in "0123456789" or r[0] in "。，、；：）〕」】")

vol_page = {v[0]: i for i, v in enumerate(vols)}   # 页 -> 卷号(0-based)
cur_chap = None
cur_blocks = []
chap_seen = {i: set() for i in range(8)}

def flush_ch():
    global cur_chap, cur_blocks
    if cur_chap is not None:
        push_ch(f"第{CH_TEXT[cur_chap[2]]}章", cur_blocks)
        cur_chap = None
        cur_blocks = []

cur_vi = 0
for p in range(19, 497):
    if p in vol_page:
        cur_vi = vol_page[p]
        flush_ch()
        toc.append({"type": "part", "title": f"第{CH_TEXT[cur_vi+1]}卷", "index": idx, "level": 0})
    body = []
    new_chap = None
    for l in page_lines(p):
        if is_page_num(l) or is_header(l) or is_vol_line(l):
            continue
        if is_ch_comment(l):
            body.append(l)
            continue
        m = CH_RE.match(l)
        if m:
            z = m.group(1)
            zz = "章十一" if z == "章十-" else z
            num = CH_NUM.get(zz[1:])
            if num is None:
                body.append(l)
                continue
            vi = cur_vi
            if num in chap_seen[vi]:
                body.append(l)   # 卷内重复章号 = 注释/引用
                continue
            chap_seen[vi].add(num)
            rest = l[len(z):]
            new_chap = (p, vi, num, rest)
            continue
        body.append(l)
    if new_chap:
        flush_ch()
        cur_chap = new_chap
        if new_chap[3]:
            body.insert(0, new_chap[3])   # 粘连正文首句
    if body:
        cur_blocks.append({"type": "text", "value": "".join(body)})
flush_ch()

assert idx == 104, idx   # 1 序言 + 103 章
assert sum(1 for t in toc if t["type"] == "part") == 8

# ---- 校验 ----
total_chars = 0
for i in sorted(files):
    nc = sum(len(b.get("value", "")) for b in files[i]["content"])
    total_chars += nc
    print(f"  {i:3d} {files[i]['title'][:42]:44s} {nc:7d} 字")
print(f"总: {len(files)} 章 + 8 part, {total_chars} 字符（OCR 行合计 328921, 旧数据 344912）")
for t in toc:
    ind = "  " * t.get("level", 1)
    print(f"{ind}[{t['type']}] {t['title'][:40]}")

if "--dry" in sys.argv:
    n_res = 0
    for i, ch in files.items():
        for k, b in enumerate(ch["content"]):
            if "value" not in b or not b["value"]:
                continue
            nv = norm(b["value"])
            # 章标题残留（独立"章X"行不应再出现；注释"章X。"允许）
            for line in b["value"].split("\n"):
                m = re.match(r"^(章[一二三四五六七八九十]+-?[一二三四五六七八九十]?)(.*)$", line)
                if m and len(m.group(1)) <= 4 and not m.group(2):
                    print(f"⚠ 章题残留 [{i} {ch['title'][:12]}]: {line[:30]!r}")
                    n_res += 1
    print(f"残留: {n_res}")
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
for i, ch in files.items():
    json.dump(ch, open(os.path.join(SRC, f"{i}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
meta = {
    "bookId": old_meta.get("bookId") or BID,
    "title": old_meta.get("title") or "政治学",
    "author": old_meta.get("author") or "亚里士多德",
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
    hit = False
    for b in bl:
        if b.get("id") == BID:
            b["chapterCount"] = len(files)
            hit = True
    if hit:
        with open(BOOKS_JSON, "w", encoding="utf-8") as f:
            json.dump(bl if isinstance(bj, list) else {**bj, "books": bl}, f, ensure_ascii=False, indent=None)
        print("✓ books.json chapterCount 更新")
    else:
        print("⚠ books.json 未找到该书")
