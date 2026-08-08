# -*- coding: utf-8 -*-
"""书签驱动文本层重建（通用版, 2026-08-08）
用法:
  python _bm_rebuild.py <pdf> <out_dir> <title> <author>
原理:
  - 全书文本层按页提取 + 页眉/页码清洗
  - PDF 书签(可能层级错乱)按「标题正则 + 上下文游标」重建三级结构:
      part:    导言/序/第X部分/附录X
      chapter: 第X章/卷/篇; part 下无章时直接出现的第X节提升为章; 顶级附录
      section: 第X节/本部分提示 等(挂在章下)
    SKIP: 封面/版权/目录/封底/写在...前 等杂项
  - 页内标题行定位切分: 节从标题行起, 下一节起始页标题行前归本节
  - 输出 {out}/{i}.json + meta.json（三级 toc）
"""
import sys, os, re, json, shutil
from collections import Counter
import fitz

sys.stdout.reconfigure(encoding="utf-8")

PDF, OUT, TITLE, AUTHOR = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]

SKIP_EXACT = {"封面", "版权", "目录", "封底", "书名页", "前言页", "封面页"}
SKIP_PREFIX = ("写在", "出版说明", "译者序", "代序", "序言页")
PART_PAT = re.compile(r"^(导言|自?序[言文]?|前言|引[言论]|结[论语]|跋|后记|附[录记])$|^第[一二三四五六七八九十百]+部分")
CH_PAT = re.compile(r"^第[一二三四五六七八九十百]+[章卷篇]|^附录[一二三四五六七八九十]*")
SEC_PAT = re.compile(r"^第[一二三四五六七八九十百]+节|^本部分提示|^附记|^注释")
SKIP_PAT = re.compile(r"^[a-zA-Zαβγδεζ][）)．.]|^注\d+")

def norm(s):
    return re.sub(r"\s+", "", s or "")

def skip(title):
    t = norm(title)
    return t in SKIP_EXACT or any(t.startswith(norm(p)) for p in SKIP_PREFIX) or SKIP_PAT.match(t)

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
if headers:
    print("页眉:", headers)
_PAGE_PAT = re.compile(r"^\d{1,6}$")
# 页码+书名 页眉（如 "338《真理与方法》解读"）
_HDR_PAT = re.compile(r"^\d{1,6}\s*[《「]?[^，。；！？\n]{0,18}[》」]?\s*\d{0,6}$")
# part 名+页码 页眉（如 "第三部分以语言为主线的诠释学本体论转向363"）
_PART_HDR = re.compile(r"^第[一二三四五六七八九十百]+部分\S{0,16}\s*\d{1,6}$")

def clean_page(t):
    ls = t.split("\n")
    i = 0
    while i < len(ls):
        s = ls[i].strip()
        if s in headers or (len(s) < 30 and (_PAGE_PAT.match(s) or _HDR_PAT.match(s) or _PART_HDR.match(s))):
            i += 1
            continue
        break
    j = len(ls)
    while j > i:
        s = ls[j - 1].strip()
        if _PAGE_PAT.match(s) or (len(s) < 30 and _HDR_PAT.match(s)):
            j -= 1
            continue
        break
    out = [l for l in ls[i:j] if not _PAGE_PAT.match(l.strip())]
    return "\n".join(out).strip()

pages = [clean_page(t) for t in pages]

# ── 书签 → 三级结构（游标法, 不信书签 level） ──
parts = []          # [{title|None, pg, chapters:[{title, pg, sections:[{title,pg}]}]}]
cur_part = None
cur_ch = None
for lv, title, pg in bm:
    t = norm(title)
    if skip(title):
        continue
    if PART_PAT.match(t):
        cur_part = {"title": title, "pg": pg, "chapters": []}
        parts.append(cur_part)
        cur_ch = None
    elif CH_PAT.match(t):
        cur_ch = {"title": title, "pg": pg, "sections": []}
        if cur_part is None:
            cur_part = {"title": None, "pg": pg, "chapters": []}
            parts.append(cur_part)
        cur_part["chapters"].append(cur_ch)
    elif SEC_PAT.match(t):
        if cur_ch is None or lv == 1:
            # part 下无章, 或书签 level=1 的连续"第X节"（如《真理与方法》第三部分
            # 第一节/第二节/第三节 同级平铺）→ 节提升为章
            cur_ch = {"title": title, "pg": pg, "sections": []}
            if cur_part is None:
                cur_part = {"title": None, "pg": pg, "chapters": []}
                parts.append(cur_part)
            cur_part["chapters"].append(cur_ch)
        else:
            cur_ch["sections"].append({"title": title, "pg": pg})
    # 其他书签（a) α) 等细级）→ 忽略

print("part=%d" % len(parts))
for p in parts:
    print("  %-4s %s (页%d) 章数=%d" % (p["title"] or "(顶级)", p["title"] or "", p["pg"], len(p["chapters"])))

# ── 文本提取 ──
def split_at_title(pg_text, title):
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
    if not pg_list:
        return ""
    full = pg_list[0]
    for t in pg_list[1:]:
        if full and full[-1] in "。！？；：”』」）】…—-":
            full += "\n\n" + t
        else:
            full += t
    return full

def blocks_from_text(text, hint=None):
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paras:
        paras = [hint or ""]
    return [{"type": "text", "value": v} for v in paras]

toc = []
files = {}
ch_index = 0
warns = []
for part in parts:
    part_start_ch = ch_index
    part_pg_s = part["pg"]
    for k, chd in enumerate(part["chapters"]):
        ch_title, ch_pg = chd["title"], chd["pg"]
        # chapter 页界: 本章起始页 → 下一章/下一 part/书末
        if k + 1 < len(part["chapters"]):
            ch_end = part["chapters"][k + 1]["pg"]
        else:
            nxt = next((p["pg"] for p in parts if p["pg"] > part_pg_s), total + 1)
            ch_end = nxt
        toc.append({"type": "chapter", "title": ch_title, "index": ch_index, "level": 1})
        content = []
        sec_entries = []
        # 章自身块: 章标题行起 → 第一 section 标题行前（无 section 时整页, 下方处理）
        if chd["sections"] and ch_pg < chd["sections"][0]["pg"]:
            fs_pg = chd["sections"][0]["pg"]
            i0 = split_at_title(pages[ch_pg - 1], ch_title)
            head = pages[ch_pg - 1] if i0 < 0 else "\n".join(pages[ch_pg - 1].split("\n")[i0:]).strip()
            mid = pages[ch_pg:fs_pg - 1]
            i1 = split_at_title(pages[fs_pg - 1], chd["sections"][0]["title"])
            tail = pages[fs_pg - 1] if i1 < 0 else "\n".join(pages[fs_pg - 1].split("\n")[:i1]).strip()
            content.extend(blocks_from_text(join_pages([head] + mid + [tail]), ch_title))
            print("  [章引言] %s 页%d-%d 首块: %s…" % (
                ch_title[:20], ch_pg, fs_pg - 1, content[0]["value"][:26].replace("\n", " ")))
        for sk, s in enumerate(chd["sections"]):
            s_title, s_pg = s["title"], s["pg"]
            start0 = s_pg - 1
            if sk + 1 < len(chd["sections"]):
                nxt_title, nxt0 = chd["sections"][sk + 1]["title"], chd["sections"][sk + 1]["pg"] - 1
            else:
                nxt_title, nxt0 = None, ch_end - 1
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
            first = content[sec_entries[-1][1]]["value"][:36].replace("\n", " ")
            ok = norm(first).startswith(norm(s_title))
            print("  节[%s] 页%d-%d %s" % (s_title[:22], s_pg, nxt0 + 1, "✓" if ok else "⚠ 未对齐"))
        # 无 section 的 chapter: 整页拼接
        if not content:
            text = join_pages([pages[i] for i in range(ch_pg - 1, ch_end - 1)])
            content = blocks_from_text(text, ch_title)
            print("  [无节章] %s 页%d-%d 首块: %s…" % (ch_title, ch_pg, ch_end - 1,
                  content[0]["value"][:28].replace("\n", " ")))
        files[ch_index] = {"index": ch_index, "title": ch_title, "content": content}
        for s_title, sec_at in sec_entries:
            toc.append({"type": "section", "title": s_title, "index": ch_index, "sec": sec_at, "level": 2})
        ch_index += 1
    if part_start_ch == ch_index:
        # part 无 chapter（如"导言"）→ 生成占位 chapter（内容=part 页界全文）
        nxt = next((p["pg"] for p in parts if p["pg"] > part["pg"]), total + 1)
        text = join_pages([pages[i] for i in range(part["pg"] - 1, nxt - 1)])
        content = blocks_from_text(text, part["title"] or "")
        toc.append({"type": "chapter", "title": part["title"] or "", "index": ch_index, "level": 1})
        files[ch_index] = {"index": ch_index, "title": part["title"] or "", "content": content}
        print("  [part 无章] %s 页%d-%d 首块: %s…" % (
            part["title"] or "", part["pg"], nxt - 1, content[0]["value"][:28].replace("\n", " ")))
        ch_index += 1
    # part 条目
    if part_start_ch < ch_index:
        toc.append({"type": "part", "title": part["title"] or "", "level": 0, "index": part_start_ch})

for w in warns:
    print("⚠", w)

# ── 写盘 ──
if os.path.isdir(OUT):
    shutil.rmtree(OUT)
os.makedirs(OUT)
for idx, ch in files.items():
    json.dump(ch, open(os.path.join(OUT, f"{idx}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
meta = {
    "bookId": os.path.basename(OUT),
    "title": TITLE,
    "author": AUTHOR,
    "toc": toc,
    "cover": None,
    "chapterCount": len(files),
    "chapterTitles": [ch["title"] for ch in files.values()],
}
json.dump(meta, open(os.path.join(OUT, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(f"\n写入 {OUT}: chapterCount={len(files)}, toc 条目={len(toc)}")
