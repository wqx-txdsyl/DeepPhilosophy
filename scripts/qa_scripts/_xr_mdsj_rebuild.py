# -*- coding: utf-8 -*-
"""《孟德斯鸠分权论研究》（刘训练）a04933b82f3c 重建（一次性，PDF 文本层重提取）
pdf: F:/philosophy/西方/孟德斯鸠/孟德斯鸠分权论研究.pdf（202 页，文本层可用）
旧数据 9 章 toc 全乱：章节摘要句当标题（"第一章 "孟德斯鸠的正义论…"试图揭示一个容…截断）、
文件序错乱（3 第三章在 4 第一章前）、1/2/3/4 实为导言"主要结构与框架"部分（PDF P28-49）、
5+6+7 连续段（PDF 50-173）实含 第一二三四章、8 含第四章+结语+封底。
真实结构（PDF 物理页，章标题在页眉，正文中 P79/P89 等有节标题）:
  [ch] 导言                        P4-47   一 谜一样的孟德斯鸠 P4 / 二 国内外研究综述 P7 / 三 主要结构与框架 P28
  [ch] 第一章 孟德斯鸠的正义论及其高级法背景  P48-87   一《波斯人信札》中的正义论 P48(边界 67: "主权理论还有另外一个难点")
                                          / 二 消失的主权 P67 / 三 杰斐逊、林肯与高级法 P79
  [ch] 第二章 历史视角下的分权理论       P88-142  六节: P89/100/108/113/118/125
  [ch] 第三章 国际背景下的分权理论       P143-173 四节: P144/152/163/167
  [ch] 第四章 从联盟权到联邦制          P174-195 三节: P174/179/189
  [ch] 结语                         P196-202
旧数据缺导言"一 谜一样的孟德斯鸠"（P4-7，0 从 P8 起）——重提取补回。
block = PDF 页 get_text("blocks") 段落，剥页眉（页首章名/书名/导言/结语行 + OCR 噪声）。
用法: python _xr_mdsj_rebuild.py [--dry]
"""
import json, os, re, sys, shutil, fitz

BID = "a04933b82f3c"
PDF = "F:/philosophy/西方/孟德斯鸠/孟德斯鸠分权论研究.pdf"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

def norm(s):
    return re.sub(r"\s+", "", s or "")

# ---- 章节结构（PDF 物理页，含页内首尾）----
# (title, [ (sec_title, start_p, end_p), ... ])  end_p 含
STRUCT = [
    ("导言", [
        ("一 谜一样的孟德斯鸠", 4, 6),
        ("二 国内外研究综述", 7, 27),
        ("三 主要结构与框架", 28, 47),
    ]),
    ("第一章 孟德斯鸠的正义论及其高级法背景", [
        ("一 《波斯人信札》中的正义论", 48, 66),
        ("二 消失的主权", 67, 78),
        ("三 杰斐逊、林肯与高级法", 79, 87),
    ]),
    ("第二章 历史视角下的分权理论", [
        ("一 分权的史前史：封建制起源之争", 88, 99),
        ("二 罗马的衰亡与蛮族的兴起", 100, 107),
        ("三 野蛮的自由与文明的奴役", 108, 112),
        ("四 哥特式宪政的地理基础", 113, 117),
        ("五 哥特式宪政的历史演变", 118, 124),
        ("六 哥特式的英国政体", 125, 142),
    ]),
    ("第三章 国际背景下的分权理论", [
        ("一 波里比阿与英格兰分权政体", 143, 151),
        ("二 万民法的变革及其对英国宪政的影响", 152, 162),
        ("三 国际贸易对英国宪政的影响", 163, 166),
        ("四 均势与分权", 167, 173),
    ]),
    ("第四章 从联盟权到联邦制", [
        ("一 孟德斯鸠的原始语境：联盟权", 174, 178),
        ("二 联邦党人的再阐释：联邦制", 179, 188),
        ("三 孟德斯鸠与联邦党人理论的差异", 189, 195),
    ]),
    ("结语", [("", 196, 199)]),   # 空节标题 = 无 section；200-201 版权页/封底跳过
]

# ---- 页眉剥除（页首块含章名页眉/书名页眉/导言/结语 + OCR 噪声）----
CHAP_NAMES = ["孟德斯鸠的正义论及其高级法背景", "历史视角下的分权理论",
              "国际背景下的分权理论", "从联盟权到联邦制"]
KEEP_SHORT = {c for c in "一二三四五六七八九十"}  # 页首块中保留的裸数字行（节题"一"等）

def clean_block(txt):
    """剥块内页眉与噪声，返回正文或 None（整块为页眉/扉页残骸）。"""
    for c in CHAP_NAMES:  # 块级章名页眉（跨行："第一章\n章名\n<噪声> 正文"）
        txt = re.sub(rf"^第[一二三四五六七八九十]+章\s*\n?\s*{re.escape(c)}\s*\n?\s*[^一-鿿]*", "", txt, flags=re.S)
    lines = txt.strip().split("\n")
    out = []
    for line in lines:
        s = line.strip()
        if not s:
            continue
        m = re.search(r"孟德斯鸠分权论研究", s)  # 偶数页书名页眉：词后无正文（词后仅噪声/空）→ 整行剥
        if m and not re.search(r"[一-鿿]", s[m.end():]):
            s = ""
        s = re.sub(r"^言\s*骂[^一-鿿]*(?:[一-鿿][^一-鿿]*){0,3}", "", s)  # 索引6"导言"页眉 OCR 变形
        s = re.sub(r"^导\s*言\s*[^一-鿿]*", "", s)
        s = re.sub(r"^结\s*语\s*", "", s)
        nv0 = norm(s)
        if nv0 and len(nv0) <= 2 and nv0 not in KEEP_SHORT \
                and not re.match(r"^[一二三四五六七八九十]+[、.．]", nv0):
            continue  # 残骸短行（扉页"导""口"、脚注夹噪"嘈"、页码残"月第"）；节题裸数字与"一、"保留
        s = re.sub(r"^[^一-鿿0-9a-zA-Z]+", "", s)  # 残余行首 OCR 噪声（数字/字母保留：脚注"1期。"页码等）
        if not re.search(r"[一-鿿]", norm(s)):  # 无中文的行（页码"1"/纯噪声"11•·--·"）丢弃
            continue
        if s.strip():
            out.append(s)
    body = "\n".join(out)
    return body.strip() or None

doc = fitz.open(PDF)
assert doc.page_count == 202, doc.page_count

# ---- 逐页提取（block = 段落）----
pages = {}  # p → blocks 列表
for p in range(4, 202):  # 索引 4-201（202 页=0-indexed）
    blocks = []
    for bi, b in enumerate(doc[p].get_text("blocks")):
        if not b or len(b) < 5:
            continue
        txt = b[4].strip() if isinstance(b, (tuple, list)) else str(b).strip()
        if not txt:
            continue
        c = clean_block(txt)
        if c:
            blocks.append({"type": "text", "value": c})
    pages[p] = blocks

doc.close()

# ---- 组装 ----
toc = []
files = {}
idx = 0
for ci, (ctitle, secs) in enumerate(STRUCT):
    blocks = []
    for s_title, s0, s1 in secs:
        for p in range(s0, s1 + 1):
            blocks.extend(pages[p])
    files[idx] = {"index": idx, "title": ctitle, "content": blocks}
    toc.append({"type": "chapter", "title": ctitle, "index": idx, "level": 1})
    si = 0
    for s_title, s0, s1 in secs:
        if not s_title:
            continue
        si += 1
        toc.append({"type": "section", "title": s_title, "index": idx, "sec": si, "level": 2})
    idx += 1

# ---- 校验 ----
n_sec = sum(1 for t in toc if t["type"] == "section")
assert len(files) == 6, len(files)
assert n_sec == 19, n_sec
for i, t in enumerate(toc):
    if t["type"] == "section" and (i == 0 or toc[i - 1]["type"] != "section" or toc[i - 1]["index"] != t["index"]):
        assert toc[i - 1]["type"] == "chapter" and toc[i - 1]["index"] == t["index"], f"section 错位: {t}"

total_chars = 0
for i in sorted(files):
    nc = sum(len(b.get("value", "")) for b in files[i]["content"])
    total_chars += nc
    print(f"  {i} {files[i]['title'][:38]:40s} {nc:7d} 字")
print(f"总: {len(files)} 章 + {n_sec} section, {total_chars} 字符（旧 9 章平级 cc 9→6）")
old_total = 0
if os.path.isdir(SRC):
    for fn in os.listdir(SRC):
        if fn.endswith('.json') and fn != 'meta.json':
            ch = json.load(open(os.path.join(SRC, fn), encoding='utf-8'))
            old_total += sum(len(b.get('value', '')) for b in ch.get('content', []))
print(f"旧数据总字数: {old_total}（新含 P4-7 导言一）")
for t in toc:
    ind = '  ' * t.get('level', 1)
    print(f"{ind}[{t['type']} {t.get('sec','')}] {t['title'][:40]}")
print("首:", files[0]["title"], "| 末:", files[5]["title"])

if "--dry" in sys.argv:
    n_res = 0
    for i, ch in files.items():
        for b in ch["content"]:
            v = b.get("value", "")
            nv = norm(v)
            if (nv in {"未知", "目录"} or "孟德斯鸠分权论研究" in nv[:12]
                    or (re.match(r"^第[一二三四五六七八九十]+章", nv) and len(nv) <= 12)):
                print(f"⚠ 疑似残留 [{i} {ch['title'][:10]}]: {v[:34]}")
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
    "title": old_meta.get("title") or "孟德斯鸠分权论研究",
    "author": old_meta.get("author") or "刘训练",
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
