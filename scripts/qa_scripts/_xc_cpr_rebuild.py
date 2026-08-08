# -*- coding: utf-8 -*-
"""纯粹理性批判 重建（目录驱动, 2026-08-08 v3）
问题: chapterize 把页眉路径（"第二部分·第一编·第-卷·第一章"）误切为章标题 → 178 章平铺+7 空章+9 重复。
依据: 书内目录（48-56 页）+ 印刷页码→PDF 偏移恒 +56（7 锚点验证）+ 正文标题行逐级定位（全部验证）。
结构: 2 part + 17 chapter + 21 section（导言 7 节/感性论 3 节/逻辑 1/分析论 2/辩证论 4/训练 2/法规 3）。
页眉实况（扫全书）: 全路径"第二部分·第一编·第二卷·第二章·第三节" / 浅路径"第一章·第一节" /
  部分+节名"第一部分·第二节时间" / 部分+章名"第二部分·导言先验逻辑的理念" / 带附原文页码"…·［附第一版原文]329" /
  OCR 变体"第--章，第二节" "第-·节" "第.二编"。节标题行 OCR 变体: "第-节"（一→-）/"口.Ⅱ" /"证.Ⅶ" 等。
用法: python _xc_cpr_rebuild.py
"""
import sys, os, json, re
sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.abspath(__file__))
PAGES = json.load(open(os.path.join(BASE, "_xc_tmp_pages.json"), encoding="utf-8"))
BID = "8c0c6955c793"
OUT = r"f:/program/Python/PhiAgent/backend/data/book_chapters/8c0c6955c793"
DDIR = r"f:/program/Python/PhiAgent/backend/data/book_detail"

def norm(s):
    return re.sub(r"\s+", "", s or "")
def norm2(s):
    """只留 汉字/字母/数字/罗马数字 —— 清除一切 OCR 符号变体（-－—·．.、等）"""
    return re.sub(r"[^\u4e00-\u9fffA-Za-z0-9ⅠⅡⅢⅣⅤⅥⅦ]", "", s or "")

def fuzzy_equal(a, b):
    """编辑距离 ≤1（允许单个 OCR 错/漏/多字符）; 短标题不模糊"""
    if a == b:
        return True
    la, lb = len(a), len(b)
    if min(la, lb) < 8:
        return False
    if abs(la - lb) > 1:
        return False
    if la == lb:
        return sum(x != y for x, y in zip(a, b)) <= 1
    if la > lb:
        a, b = b, a
        la, lb = lb, la
    return any(a == b[:i] + b[i + 1:] for i in range(lb))

_PAGE_PAT = re.compile(r"^\d{1,4}$")
_EDGE_PAT = re.compile(r"^[AB][IVX\d]{1,5}$")
# 页眉路径: 第X[部分编卷章节]·… 或 第X章·第Y节; 量词间可含 - . · (OCR变体); 尾部可带 附原文+页码
_HDR_PATH = re.compile(
    r"^第[一二三四五六七八九十百\-\.·]{0,6}[部分编卷章节]"
    r"[·，,]((第[一二三四五六七八九十百\-\.·]{0,6}[部分编卷章节])|[一-龥]{1,14})"
    r"([·，,]((第[一二三四五六七八九十百\-\.·]{0,6}[部分编卷章节])|[一-龥]{1,14})){0,5}"
    r"([·［\[【(！!]?(附?[：:]?第?[一二三四五六七八九十百\-\.]{0,6}版原文)?[\]】」]?\d{0,4})?$"
)
# 纯名页眉（running head = 章名/序名, 无路径前缀）
HDRS = {norm(s) for s in [
    "导言", "目录", "中译本序", "第一版序", "第二版序", "第一—版序", "第二二版序",
    "一、先验要素论", "二先验方法论", "二、先验方法论", "德汉术语索引", "汉德术语对照表",
    "第一部分先验感性论", "第二部分先验逻辑", "第一编先验分析论", "第二编先验辩证论",
    "第一章纯粹理性的训练", "第二章纯粹理性的法规", "第三章纯粹理性的建筑术", "第四章纯粹理性的历史",
    "致宫廷国务大臣冯·策特里茨男爵大人阁下", "题辞", "献辞",
]}
_NOISE_PAT = re.compile(r"^[0-9a-zA-Z|+.:·．!?=*\-~/\\()<>\[\]\"'“”…\s]{1,16}$")
_PUNCT_ONLY = re.compile(r"^[、，。：；！？…—·\"'“”‘’【】■↓=*+\-./~|!?()<>\[\]{}①②③④⑤⑥⑦⑧⑨⑩]{1,4}$")

def is_noise(s):
    n = norm(s)
    if not n or _PAGE_PAT.match(s) or _EDGE_PAT.match(s):
        return True
    return bool(_NOISE_PAT.match(n))

def clean_page(t, keep_lines):
    ls = t.split("\n")
    i = 0
    while i < len(ls):
        if i in keep_lines:
            break
        s = ls[i].strip()
        n = norm(s)
        if not s or is_noise(s) or n in HDRS or _HDR_PATH.match(s):
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
        if is_noise(s) or n in HDRS or _HDR_PATH.match(s) or _PUNCT_ONLY.match(s):
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
        if tn2 and len(tn2) >= 8 and n2.startswith(tn2[:8]):
            return True
        if tn2 and len(n2) >= 8 and tn2.startswith(n2[:8]):
            return True
        if tn2 and fuzzy_equal(n2, tn2):
            return True
        return False
    if mode == "contains":
        return bool(tn) and tn in n
    if mode == "kw":
        return all(k in n for k in kw)
    return False

def find_line(lines, title, mode, kw=None):
    for i, line in enumerate(lines):
        if match_line(line, title, mode, kw):
            return i
    return -1

def join_pages(pg_list):
    """每页独立段（页间无条件空行）—— 页末常为脚注行(非标点)导致旧逻辑不拆段"""
    return "\n\n".join(s for s in pg_list if s)

# ── 结构: (part, [(ch, pg_s, pg_e, [(sec_title, pg, mode, kw)], has_title, end_cut)]) ──
DAOYAN_SECS = [
    ("Ⅰ.纯粹知识和经验性知识的区别", 57, "kw", ["纯粹知识", "经验性知识"]),
    ("Ⅱ.我们具有某些先天知识，甚至普通知性也从来不缺少它们", 59, "kw", ["我们具有某些", "普通知性"]),
    ("Ⅲ.哲学需要一门科学来规定一切先天知识的可能性、原则和范围", 61, "kw", ["哲学需要一门科学"]),
    ("Ⅳ.分析判断与综合判断的区别", 64, "kw", ["分析判断", "综合判断的区别"]),
    ("Ⅴ.在理性的一切理论科学中都包含有先天综合判断作为原则", 67, "kw", ["理论科学中都包含有", "先天综合判断作为原则"]),
    ("Ⅵ.纯粹理性的总课题", 71, "kw", ["纯粹理性的总课题"]),
    ("Ⅶ.在纯粹理性批判名下的一门特殊科学的理念和划分", 75, "kw", ["在纯粹理性批判名下", "理念和划分"]),
]
STRUCT = [
    (None, [
        ("中译本序", 4, 14, [], True, None),
        ("题辞", 15, 15, [], True, None),
        ("献辞", 16, 17, [], True, None),
        ("第一版序", 18, 26, [], True, None),
        ("第二版序", 27, 47, [], True, None),
        ("导言", 57, 78, DAOYAN_SECS, True, None),
    ]),
    ("一、先验要素论", [
        ("第一部分先验感性论", 81, 106, [
            ("第一节空间", 83, "contains", None),
            ("第二节时间", 90, "exact", None),
            ("先验感性论的结论", 106, "exact", None),
        ], True, None),
        ("第二部分先验逻辑", 107, 115, [
            ("导言先验逻辑的理念", 107, "exact", None),
        ], True, None),
        ("第一编先验分析论", 116, 313, [
            ("第一卷概念分析论", 117, "exact", None),
            ("第二卷原理分析论", 190, "exact", None),
        ], True, None),
        ("第二编先验辩证论", 314, 603, [
            ("导言", 314, "exact", None),
            ("第一卷纯粹理性的概念", 324, "exact", None),
            ("第二卷纯粹理性的辩证推论", 342, "exact", None),
            ("先验辩证论附录", 561, "exact", None),
        ], True, None),
    ]),
    ("二、先验方法论", [
        ("导言", 605, 606, [], False, "第一章纯粹理性的训练"),
        ("第一章纯粹理性的训练", 606, 661, [
            ("第一节纯粹理性在独断运用中的训练", 608, "var", None),
            ("第二节对纯粹理性在其论争上的运用的训练", 625, "var", None),
        ], True, None),
        ("第二章纯粹理性的法规", 662, 683, [
            ("第一节我们理性的纯粹运用之最后目的", 663, "var", None),
            ("第二节至善理想作为纯粹理性最终目的的规定的根据", 667, "var", None),
            ("第三节意见、知识和信念", 677, "var", None),
        ], True, None),
        ("第三章纯粹理性的建筑术", 684, 697, [], True, None),
        ("第四章纯粹理性的历史", 698, 701, [], True, None),
    ]),
    (None, [
        ("德汉术语索引", 702, 742, [], True, None),
        ("汉德术语对照表", 743, 755, [], True, None),
    ]),
]

# ── 1) 定位全部标题行（clean 前原文）→ keep_lines ──
keep = {}
warns = []

def mark(pg, li):
    if li >= 0:
        keep.setdefault(pg, set()).add(li)
    return li

for part_title, chs in STRUCT:
    for ch_title, pg_s, pg_e, secs, has_title, end_cut in chs:
        if has_title:
            i = find_line(PAGES.get(str(pg_s), "").split("\n"), ch_title, "var")
            if i < 0:
                i = find_line(PAGES.get(str(pg_s), "").split("\n"), ch_title, "contains")
            mark(pg_s, i)
            if i < 0:
                warns.append(f"章[{ch_title}] 页{pg_s} 未定位")
        if end_cut and end_cut != ch_title:
            i = find_line(PAGES.get(str(pg_e), "").split("\n"), end_cut, "var")
            mark(pg_e, i)
            if i < 0:
                warns.append(f"截断点[{end_cut}] 页{pg_e} 未定位")
        for sec_title, sec_pg, mode, kw in secs:
            i = find_line(PAGES.get(str(sec_pg), "").split("\n"), sec_title, mode, kw)
            mark(sec_pg, i)
            if i < 0:
                warns.append(f"节[{sec_title}] 页{sec_pg} 未定位")
print("定位: 保留行页数", len(keep), "警告", len(warns))
for w in warns:
    print("⚠", w)

# ── 2) 清洗全部页 ──
pages = [clean_page(PAGES[str(k)], keep.get(k, set())) for k in range(756)]

# ── 3) 组装章节 ──
def split_sec_lines(text, sec_specs):
    """节标题行 → 独立段 + 替换为标准标题; 后续重复行（页眉重复）删除; 跨行标题拼接删除"""
    lines = text.split("\n")
    repl = {}
    for sec_title, _pg, mode, kw in sec_specs:
        tn2 = norm2(sec_title)
        first = True
        for li, l in enumerate(lines):
            if match_line(l, sec_title, mode, kw):
                if first:
                    repl[li] = (sec_title, True)
                    first = False
                else:
                    repl[li] = (sec_title, False)
                # 跨行标题: 命中行 + 下一行 拼接 == 标题（625 行18+19 情况）
                if first is False and li + 1 < len(lines):
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

toc = []
files = {}
ch_index = 0

for part_title, chs in STRUCT:
    part_start_ch = ch_index
    if part_title:
        toc.append({"type": "part", "title": part_title, "level": 0, "index": part_start_ch})
    for k, (ch_title, pg_s, pg_e, secs, has_title, end_cut) in enumerate(chs):
        toc.append({"type": "chapter", "title": ch_title, "index": ch_index, "level": 1})
        segs = []
        if has_title:
            pg_clean = pages[pg_s]
            i0 = find_line(pg_clean.split("\n"), ch_title, "var")
            if i0 < 0:
                i0 = find_line(pg_clean.split("\n"), ch_title, "contains")
            if i0 >= 0:
                rest = "\n".join(pg_clean.split("\n")[i0 + 1:]).strip()
                head = ch_title  # 标准标题替换 OCR 变体
                if rest:
                    head += "\n\n" + rest
                segs.append(head)
            else:
                warns.append(f"章[{ch_title}] 页{pg_s} 组装时未定位")
                if pg_clean:
                    segs.append(pg_clean)
        else:
            if pages[pg_s]:
                segs.append(pages[pg_s])
        mid_s = pg_s + 1
        last_pg = pg_e
        # end_cut: 末页在标题行处截断（导言 606 行 2-9 并入, 行 10+ 归下一章）
        if end_cut and end_cut != ch_title:
            ls = pages[pg_e].split("\n")
            ci = find_line(ls, end_cut, "var")
            if ci >= 0:
                if ci == 0:
                    last_pg = pg_e - 1
                else:
                    segs.append("\n".join(ls[:ci]).strip())
                    last_pg = pg_e - 1
            else:
                warns.append(f"截断点[{end_cut}] 页{pg_e} 组装时未定位")
                last_pg = pg_e
        if mid_s <= last_pg:
            segs.extend(pages[mid_s:last_pg + 1])
        text = join_pages([s for s in segs if s])
        text, found_secs = split_sec_lines(text, secs)
        blocks = blocks_from_text(text, ch_title)
        # 节锚点: 最终 blocks 中 value == 标准标题
        sec_anchors = {}
        for sec_title, _pg, mode, kw in secs:
            tn = norm(sec_title)
            for bi, b in enumerate(blocks):
                if norm(b["value"]) == tn:
                    sec_anchors[sec_title] = bi
                    break
            if sec_title not in sec_anchors:
                warns.append(f"节[{sec_title}] 锚点未建立")
        files[ch_index] = {"index": ch_index, "title": ch_title, "content": blocks}
        total_chars = sum(len(b["value"]) for b in blocks)
        first = blocks[0]["value"][:24].replace("\n", " ")
        print(f"  [{part_title if part_title else '顶'}] {ch_title} 页{pg_s}-{pg_e} 块{len(blocks)} {total_chars}字 首: {first}…")
        for sec_title, sec_at in sec_anchors.items():
            toc.append({"type": "section", "title": sec_title, "index": ch_index, "sec": sec_at, "level": 2})
        ch_index += 1

for w in warns:
    print("⚠", w)

# ── 4) 写盘 ──
if os.path.isdir(OUT):
    suf = "_old_bad"
    i = 2
    while os.path.isdir(OUT + suf):
        suf = f"_old_bad{i}"
        i += 1
    os.rename(OUT, OUT + suf)
os.makedirs(OUT)
for idx, ch in files.items():
    json.dump(ch, open(os.path.join(OUT, f"{idx}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
meta = {
    "bookId": BID,
    "title": "纯粹理性批判",
    "author": "康德",
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
print(f"\nchapterCount={len(files)}, toc 条目={len(toc)}, 全文字数={total_chars}")
