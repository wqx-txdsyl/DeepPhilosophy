# -*- coding: utf-8 -*-
"""荣格心理学 重建（目录驱动, 2026-08-08 v1）
问题: chapterize 把 TOC 页混入章节 + 页眉误切 → 10 章损坏（字符串数组 toc, 注释误切标题）。
依据: 书内目录(p5-8) 印刷页码→PDF 偏移 +8（19+ 锚点验证: 意识与无意识013→p21 … 著述目录188→p196）。
结构: 12 章（前言/荣格序/绪论/第一~三章/荣格传略/人名索引/名词术语索引/著述目录/附录1/附录2）+ 54 节。
页眉实况: 奇数页=章名（第一章心理的结构与本质…）, 偶数页=书名"荣格心理学导读";
  章题页为 2 行拆分（"第一章"+“心理的结构与本质"）; 偶页页码/脚注号偶被并入正文行;
  著述目录按年份分组（1902/1908/…/1961, 独立行年份须保留）。
用法: python _xc_rg_rebuild.py
"""
import sys, os, json, re
sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.abspath(__file__))
PAGES = json.load(open(os.path.join(BASE, "_xc_tmp_pages.json"), encoding="utf-8"))
# __FAILED__ 页 = 空白/篇章间隔页, 视为空页（不产生文本块）
PAGES = {k: ("" if str(v).strip() == "__FAILED__" else v) for k, v in PAGES.items()}
N = len(PAGES)
BID = "d1a2be0b5837"
OUT = r"f:/program/Python/PhiAgent/backend/data/book_chapters/d1a2be0b5837"
DDIR = r"f:/program/Python/PhiAgent/backend/data/book_detail"

def norm(s):
    return re.sub(r"\s+", "", s or "")
def norm2(s):
    """只留 汉字/字母/数字 —— 清除一切 OCR 符号变体"""
    return re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", s or "")

def fuzzy_equal(a, b):
    """编辑距离 ≤1（允许单个 OCR 错字）; 短标题(len<4)不模糊"""
    if a == b:
        return True
    la, lb = len(a), len(b)
    if min(la, lb) < 4:
        return False
    if abs(la - lb) > 1:
        return False
    if la == lb:
        return sum(x != y for x, y in zip(a, b)) <= 1
    if la > lb:
        a, b = b, a
        la, lb = lb, la
    return any(a == b[:i] + b[i + 1:] for i in range(lb))

_PAGE_PAT = re.compile(r"^\d{1,3}$")          # 页号/脚注号（≤3 位; 4 位留给年份）
_YEAR_PAT = re.compile(r"^(19|20)\d{2}$")     # 著述目录年份标题, 保留
_EDGE_PAT = re.compile(r"^[AB][IVX\d]{1,5}$")
HDRS = {norm(s) for s in [
    "前言", "荣格序", "绪论",
    "第一章心理的结构与本质", "第二章心理过程和心理反应的规律", "第三章荣格学说的实际应用",
    "荣格传略", "人名索引", "名词术语索引", "荣格德语著述目录",
    "附录1其他著述译名对照", "附录2本书提及的荣格著述译名对照",
    "荣格心理学导读",
]}
_NOISE_PAT = re.compile(r"^[0-9a-zA-Z|+.:·．!?=*\-~/\\()<>\[\]\"'“”…\s]{1,16}$")
_PUNCT_ONLY = re.compile(r"^[、，。：；！？…—·\"'“”‘’【】■↓=*+\-./~|!?()<>\[\]{}①②③④⑤⑥⑦⑧⑨⑩]{1,4}$")

def is_noise(s):
    n = norm(s)
    if not n or _YEAR_PAT.match(s):
        return False
    if _PAGE_PAT.match(s) or _EDGE_PAT.match(s):
        return True
    return bool(_NOISE_PAT.match(n))

def clean_page(t, keep_lines, permissive=False):
    ls = t.split("\n")
    i = 0
    while i < len(ls):
        if i in keep_lines:
            break
        s = ls[i].strip()
        n = norm(s)
        if not s or is_noise(s) or n in HDRS:
            i += 1
            continue
        break
    j = len(ls)
    while j > i:
        s = ls[j - 1].strip()
        if is_noise(s):
            j -= 1
            continue
        break
    out = []
    for k, l in enumerate(ls[i:j], start=i):
        s = l.strip()
        n = norm(s)
        if not s:
            out.append("")
            continue
        if k in keep_lines:
            out.append(l)
            continue
        if is_noise(s) or n in HDRS or _PUNCT_ONLY.match(s):
            continue
        if permissive:
            out.append(l)
            continue
        if _NOISE_PAT.match(n):
            continue
        out.append(l)
    return "\n".join(out).strip()

def match_line(line, title, mode, kw):
    n, n2 = norm(line), norm2(line)
    if not n:
        return False
    tn, tn2 = norm(title), norm2(title)
    if mode == "exact":
        return n == tn or (tn2 and n2 == tn2)
    if mode == "var":
        if tn2 and n2 == tn2:
            return True
        if tn2 and fuzzy_equal(n2, tn2):
            return True
        return False
    if mode == "contains":
        return bool(tn) and tn in n
    if mode == "kw":
        return all(k in n for k in kw)
    return False

def find_title_block(lines, title):
    """章题块: 连续 1-3 行拼接(norm2) == 标题（"第一章"+"心理的结构与本质"）"""
    tn2 = norm2(title)
    for i in range(len(lines)):
        for j in range(i, min(i + 3, len(lines))):
            if norm2("".join(lines[i:j + 1])) == tn2:
                return i, j
    return -1, -1

def find_sec(sec_title, exp_pg, attempts):
    """节标题: 窗口 [exp-2, exp+3] 内逐行匹配; attempts=[(mode,kw),...] 依次尝试"""
    for pg in range(max(0, exp_pg - 2), min(N, exp_pg + 4)):
        lines = PAGES.get(str(pg), "").split("\n")
        for li, l in enumerate(lines):
            for mode, kw in attempts:
                if match_line(l, sec_title, mode, kw):
                    return pg, li
    return -1, -1

def join_pages(pg_list):
    return "\n\n".join(s for s in pg_list if s)

# ── 结构: (章标题, 首页, 末页, [(节标题, 预期页, attempts)]) ──
CH1_SECS = [
    ("意识与无意识", 21), ("意识功能", 26), ("心理倾向", 34), ("创作者的类型问题", 39),
    ("人格面具", 43), ("无意识的内容", 47), ("情结", 52), ("原型", 55),
]
CH2_SECS = [
    ("力比多的概念", 71), ("矛盾结构", 72), ("力比多的运动形式", 74),
    ("前行与退行", 76), ("心理值与心座", 77),
]
CH3_SECS = [
    ("荣格心理学的双重意义", 81), ("与精密学科的关系", 82), ("因果论与目的论", 87),
    ("辨证方法", 88), ("通向无意识的道路", 90), ("梦", 91), ("梦的解释", 93),
    ("梦的根源", 94), ("梦的类型", 95), ("梦的排列", 96), ("梦的内容之多义性", 98),
    ("梦的补偿作用", 99), ("梦作为“儿童王国”", 100), ("解析的步骤", 102), ("梦的结构", 103),
    ("条件论", 104), ("放大法", 105), ("还原解析法", 107), ("梦的动态趋势", 109),
    ("个体意义与集体意义", 111), ("解释层面", 112), ("投射", 114), ("象征", 115),
    ("象征与符号", 117), ("图解象征", 119), ("分析的基本原则", 121), ("神经症的意义", 123),
    ("展望性", 125), ("人格的发展", 127), ("个性化过程", 128), ("阴影", 130),
    ("阿尼姆斯与阿尼玛", 137), ("精神原则与物质原则的原型", 147), ("自性", 149),
    ("自性形成", 155), ("统一性象征", 158), ("曼茶罗象征", 159), ("个性化过程的类比", 164),
    ("分析心理学与宗教", 169), ("转变与成熟", 172), ("责任在个人", 174),
]
STRUCT = [
    ("前言", 9, 11, []),
    ("荣格序", 13, 14, []),
    ("绪论", 15, 17, []),
    ("第一章 心理的结构与本质", 19, 67, CH1_SECS),
    ("第二章 心理过程和心理反应的规律", 69, 78, CH2_SECS),
    ("第三章 荣格学说的实际应用", 79, 175, CH3_SECS),
    ("荣格传略", 176, 180, []),
    ("人名索引", 181, 182, []),
    ("名词术语索引", 183, 195, []),
    ("荣格德语著述目录", 196, 214, []),
    ("附录1 其他著述译名对照", 215, 215, []),
    ("附录2 本书提及的荣格著述译名对照", 216, 218, []),
]

# 著述目录/索引页为宽松清理模式（保留德文书目行）
PERMISSIVE = {pg for t, a, b, _s in STRUCT for pg in range(a, b + 1) if t in ("荣格德语著述目录",)}

# ── 1) 定位全部保留行 ──
keep = {}
warns = []

def mark(pg, li):
    if li >= 0:
        keep.setdefault(pg, set()).add(li)

for ch_title, pg_s, pg_e, secs in STRUCT:
    i, j = find_title_block(PAGES.get(str(pg_s), "").split("\n"), ch_title)
    if i < 0:
        warns.append(f"章[{ch_title}] 页{pg_s} 标题块未定位")
    for li in range(i, j + 1):
        mark(pg_s, li)
    for sec_title, exp_pg in secs:
        attempts = [("var", None)]
        if "图解" in sec_title:
            attempts.append(("kw", ["图解象征"]))
        pg, li = find_sec(sec_title, exp_pg, attempts)
        mark(pg, li)
        if pg < 0:
            warns.append(f"节[{sec_title}] 预期页{exp_pg} 未定位")

print("定位: 保留行页数", len(keep), "警告", len(warns))
for w in warns:
    print("⚠", w)

# ── 2) 清洗全部页 ──
pages = [clean_page(PAGES[str(k)], keep.get(k, set()), permissive=(k in PERMISSIVE)) for k in range(N)]

# ── 3) 组装章节 ──
def split_sec_lines(text, sec_specs):
    """节标题行 → 独立段 + 替换为标准标题; 重复行删除; 跨行标题拼接删除"""
    lines = text.split("\n")
    repl = {}
    for sec_title, exp_pg in sec_specs:
        tn2 = norm2(sec_title)
        first = True
        for li, l in enumerate(lines):
            ok = False
            for mode, kw in [("var", None)] + ([("kw", ["图解象征"])] if "图解" in sec_title else []):
                if match_line(l, sec_title, mode, kw):
                    ok = True
                    break
            if not ok:
                continue
            if first:
                repl[li] = (sec_title, True)
                first = False
            else:
                repl[li] = (sec_title, False)
            # 跨行标题: 命中行 + 下一行 拼接 == 标题
            if li + 1 < len(lines):
                cur, nxt = norm2(l), norm2(lines[li + 1])
                if nxt and tn2 and cur and len(cur) < len(tn2) and fuzzy_equal(cur + nxt, tn2):
                    repl[li + 1] = (sec_title, False)
    if not repl:
        return text, set()
    out = []
    for li, l in enumerate(lines):
        if li in repl:
            t, is_anchor = repl[li]
            if is_anchor:
                if out and out[-1] != "":
                    out.append("")
                out.append(t)
                out.append("")
        else:
            out.append(l)
    return "\n".join(out), {t for t, a in repl.values() if a}

def blocks_from_text(text, hint=None):
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paras:
        paras = [hint or ""]
    return [{"type": "text", "value": v} for v in paras]

# 索引/译名对照: 每行一个条目（OCR 条目间无空行 → 行级拆段）
LINE_PARAS = {"人名索引", "附录1 其他著述译名对照", "附录2 本书提及的荣格著述译名对照"}

toc = []
files = {}
ch_index = 0
sec_total = 0

for ch_title, pg_s, pg_e, secs in STRUCT:
    toc.append({"type": "chapter", "title": ch_title, "index": ch_index, "level": 1})
    segs = []
    pg_clean = pages[pg_s]
    i, j = find_title_block(pg_clean.split("\n"), ch_title)
    if i >= 0:
        rest = "\n".join(pg_clean.split("\n")[j + 1:]).strip()
        head = ch_title  # 标准标题替换 OCR 变体/2 行拆分
        if rest:
            head += "\n\n" + rest
        segs.append(head)
    else:
        warns.append(f"章[{ch_title}] 页{pg_s} 组装时标题块未定位")
        if pg_clean:
            segs.append(pg_clean)
    segs.extend(pages[pg_s + 1:pg_e + 1])
    text = join_pages([s for s in segs if s])
    text, found_secs = split_sec_lines(text, secs)
    if ch_title in LINE_PARAS:
        # 行级拆段: 索引条目/译名对照行, 每行独立成段
        blocks = [{"type": "text", "value": p.strip()} for p in text.split("\n") if p.strip()]
    else:
        blocks = blocks_from_text(text, ch_title)
    sec_anchors = {}
    for sec_title, exp_pg in secs:
        tn = norm(sec_title)
        for bi, b in enumerate(blocks):
            if norm(b["value"]) == tn:
                sec_anchors[sec_title] = bi
                break
        if sec_title not in sec_anchors:
            warns.append(f"节[{sec_title}] 锚点未建立")
    files[ch_index] = {"index": ch_index, "title": ch_title, "content": blocks}
    total_chars = sum(len(b["value"]) for b in blocks)
    first = blocks[0]["value"][:22].replace("\n", " ")
    print(f"  [{ch_title}] 页{pg_s}-{pg_e} 块{len(blocks)} {total_chars}字 首: {first}…")
    for sec_title, sec_at in sec_anchors.items():
        toc.append({"type": "section", "title": sec_title, "index": ch_index, "sec": sec_at, "level": 2})
        sec_total += 1
    ch_index += 1

for w in warns:
    print("⚠", w)

# ── 4) 抽查全部节锚点（前块尾/本块首/后块首）──
print("\n===== 节锚点抽查 =====")
for ci, ch in files.items():
    meta_toc = [t for t in toc if t["type"] == "section" and t["index"] == ci]
    for t in meta_toc:
        at = t["sec"]
        blocks = ch["content"]
        prev = blocks[at - 1]["value"][-20:] if at > 0 else "(无前块)"
        cur = blocks[at]["value"][:20]
        nxt = blocks[at + 1]["value"][:20] if at + 1 < len(blocks) else "(无后块)"
        print(f"[{ch['title']}] {t['title']} @{at}: 前…{prev!r} | 本{cur!r} | 后{nxt!r}")

# ── 5) 写盘 ──
if os.path.isdir(OUT):
    suf = "_old_bad"
    i2 = 2
    while os.path.isdir(OUT + suf):
        suf = f"_old_bad{i2}"
        i2 += 1
    os.rename(OUT, OUT + suf)
os.makedirs(OUT)
for idx, ch in files.items():
    json.dump(ch, open(os.path.join(OUT, f"{idx}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
meta = {
    "bookId": BID,
    "title": "荣格心理学",
    "author": "荣格",
    "toc": toc,
    "cover": None,
    "chapterCount": len(files),
    "chapterTitles": [ch["title"] for ch in files.values()],
}
json.dump(meta, open(os.path.join(OUT, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

dp = os.path.join(DDIR, f"{BID}.json")
if os.path.exists(dp):
    d = json.load(open(dp, encoding="utf-8"))
    d["toc"] = toc
    d["chapterCount"] = len(files)
    d["chapterTitles"] = meta["chapterTitles"]
    json.dump(d, open(dp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("book_detail 更新 ✓")

total_chars = sum(len(b["value"]) for ch in files.values() for b in ch["content"])
print(f"\nchapterCount={len(files)}, toc 条目={len(toc)} (章{len(files)} 节{sec_total}), 全文字数={total_chars}")
