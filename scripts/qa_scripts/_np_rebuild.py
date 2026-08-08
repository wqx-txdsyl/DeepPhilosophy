# -*- coding: utf-8 -*-
"""尼采与哲学 文本层重建（书签驱动两级分级）
背景: 该 PDF 实际有完整文本层 + 84 条书签, 但 has_text_layer 只采样第 30 页误判为 OCR
→ 旧入库数据是 OCR 版(5 章无 section, 节标题与正文粘连)。
重建: 书签 level1(5 part + 结论) → chapter; level2(75) → section; 正文按页提取拼接。
"""
import sys, os, re, json, shutil, hashlib
from collections import Counter
import fitz

sys.stdout.reconfigure(encoding="utf-8")

PDF = r"F:/philosophy/西方/吉尔·德勒兹/尼采与哲学.pdf"
BID = "e7c27b39a87c"
BASE = r"f:/program/Python/PhiAgent/backend"
OUT = os.path.join(BASE, "data/book_chapters", BID)
DDIR = os.path.join(BASE, "data/book_detail")
SKIP_PARTS = {"总序一", "总序二", "目录"}

doc = fitz.open(PDF)
total = doc.page_count
pages = [doc[i].get_text() for i in range(total)]
bm = doc.get_toc()
doc.close()

# ── 页眉/页码清洗 ──
firsts = Counter()
for t in pages:
    ls = [l.strip() for l in t.split("\n") if l.strip()]
    if ls:
        firsts[ls[0]] += 1
headers = {l for l, c in firsts.items() if c > total * 0.1 and len(l) < 20}
print("页眉(>10%页首行):", headers)
_PAGE_PAT = re.compile(r"^\d{1,6}$")

def clean_page(t):
    ls = t.split("\n")
    i = 0
    while i < len(ls) and ls[i].strip() in headers:
        i += 1
    out = []
    for l in ls[i:]:
        if _PAGE_PAT.match(l.strip()):
            continue
        out.append(l)
    return "\n".join(out).strip()

pages = [clean_page(t) for t in pages]

# ── 书签分级 ──
parts = [b for b in bm if b[0] == 1 and b[1] not in SKIP_PARTS]
secs = [b for b in bm if b[0] == 2]
# part 边界
bounds = parts + [("END", total + 1, total + 1)]
chapters = []  # (title, start_pg1, end_pg1_excl)
for i, (lv, title, pg) in enumerate(parts):
    nxt = bounds[i + 1][2]
    chapters.append((re.sub(r"\s+", "", title), pg, nxt))

# ── 节内容切分（页内标题行定位: 标题行起切, 下一节起始页标题行前归本节） ──
def norm(s):
    return re.sub(r"\s+", "", s or "")

def split_at_title(pg_text, title):
    """页文本中定位标题行 → 行索引; 找不到 -1"""
    tn = norm(title)
    lines = pg_text.split("\n")
    for i, line in enumerate(lines):
        if norm(line) == tn:
            return i
    if len(tn) >= 5:
        for i, line in enumerate(lines):
            if norm(line).startswith(tn[:5]):
                return i
    return -1

def join_pages(pg_list):
    """pg_list: 0-based 页索引列表 → 文本（页末无标点直接拼, 否则段落分隔）"""
    if not pg_list:
        return ""
    full = pg_list[0]
    for t in pg_list[1:]:
        if full and full[-1] in "。！？；：”』」）】…—-":
            full += "\n\n" + t
        else:
            full += t
    return full

def blocks_from_text(text, title_hint=None):
    """按空行分段 → content 块"""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paras:
        paras = [title_hint or ""]
    return [{"type": "text", "value": v} for v in paras]

toc = []
files = {}  # chapter index → {index, title, content}
ch_index = 0
warns = []
for (ch_title, pg_s, pg_e) in chapters:
    ch_secs = [s for s in secs if pg_s <= s[2] < pg_e]
    toc.append({"type": "chapter", "title": ch_title, "index": ch_index, "level": 1})
    content = []
    sec_entries = []
    for k, s in enumerate(ch_secs):
        s_title, s_pg = s[1], s[2]
        start0 = s_pg - 1
        if k + 1 < len(ch_secs):
            nxt_title, nxt0 = ch_secs[k + 1][1], ch_secs[k + 1][2] - 1
        else:
            nxt_title, nxt0 = None, pg_e - 1
        i0 = split_at_title(pages[start0], s_title)
        if i0 < 0:
            warns.append(f"节[{s_title}] 起始页 {s_pg} 未找到标题行")
            head = pages[start0]
        else:
            head = "\n".join(pages[start0].split("\n")[i0:]).strip()
        if nxt0 > start0:
            mid = pages[start0 + 1:nxt0]
            if nxt_title:
                i1 = split_at_title(pages[nxt0], nxt_title)
                if i1 < 0:
                    warns.append(f"节[{s_title}] 结束页 {nxt0+1} 未找到下一节标题行[{nxt_title}]")
                    tail = pages[nxt0]
                else:
                    tail = "\n".join(pages[nxt0].split("\n")[:i1]).strip()
            else:
                tail = pages[nxt0]
            text = join_pages([head] + mid + [tail])
        else:
            text = head
        blocks = blocks_from_text(text)
        sec_entries.append((s_title, len(content)))
        content.extend(blocks)
        first = content[sec_entries[-1][1]]["value"][:40].replace("\n", " ")
        expect = norm(s_title)
        got = norm(first)[: len(expect) * 2]
        ok = got.startswith(expect)
        print("  节[%s] 页%d-%d 首块: %s… %s" % (
            s_title[:22], s_pg, nxt0 + 1, first[:32], "✓" if ok else "⚠ 标题行缺失/错位"))
    # 结论章等无 section 的 chapter: 整页拼接
    if not content:
        text = join_pages([pages[i] for i in range(pg_s - 1, pg_e - 1)])
        content = blocks_from_text(text, ch_title)
        print("  [无节章] %s 页%d-%d 首块: %s…" % (ch_title, pg_s, pg_e - 1,
              content[0]["value"][:32].replace("\n", " ")))
    files[ch_index] = {"index": ch_index, "title": ch_title, "content": content}
    for s_title, sec_at in sec_entries:
        toc.append({"type": "section", "title": s_title, "index": ch_index, "sec": sec_at, "level": 2})
    ch_index += 1

for w in warns:
    print("⚠", w)

# ── 写盘（PhiAgent 端） ──
if os.path.isdir(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT)
for idx, ch in files.items():
    json.dump(ch, open(os.path.join(OUT, f"{idx}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
meta = {
    "bookId": BID,
    "title": "尼采与哲学",
    "author": "吉尔·德勒兹",
    "toc": toc,
    "cover": None,
    "chapterCount": len(files),
    "chapterTitles": [ch["title"] for ch in files.values()],
}
json.dump(meta, open(os.path.join(OUT, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(f"\n写入 {OUT}: chapterCount={len(files)}, toc 条目={len(toc)}")

# ── 更新 book_detail ──
dp = os.path.join(DDIR, f"{BID}.json")
if os.path.exists(dp):
    d = json.load(open(dp, encoding="utf-8"))
    d["toc"] = toc
    d["chapterCount"] = len(files)
    d["chapterTitles"] = meta["chapterTitles"]
    d["extract"] = "text_layer"
    json.dump(d, open(dp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("book_detail 更新:", dp)
