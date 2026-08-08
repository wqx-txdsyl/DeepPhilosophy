# -*- coding: utf-8 -*-
"""西塞罗全集·修辞学卷 重建（OCR 页文本 → 著作/卷两级结构）
背景: chapterize 把正文引用句（"第2卷第1章。"等）误切成章标题, 旧版 20 章中 14 章标题是正文半句。
依据: 书内目录（印刷页码→PDF页偏移34, 全部锚点验证）+ 页眉转换 + 卷标题行页内定位。
结构: 4 part（论公共演讲的理论/论开题/论演说家/译名对照与索引）+ 23 chapter + 导言 5 section。
用法: python _xc_rebuild.py
"""
import sys, os, json, re
sys.stdout.reconfigure(encoding="utf-8")

PAGES = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "_xc_tmp_pages.json"), encoding="utf-8"))
BID = "a494d6365a42"
OUT = r"f:/program/Python/PhiAgent/backend/data/book_chapters/a494d6365a42"
DDIR = r"f:/program/Python/PhiAgent/backend/data/book_detail"

def norm(s):
    return re.sub(r"\s+", "", s or "")

NAME_HDRS = {norm(s) for s in [
    "中译者导言", "论公共演讲的理论", "论开题", "论最好的演说家", "论题", "论演说家",
    "论命运", "斯多亚学派的反论", "论演讲术的分类", "布鲁图", "演说家", "西汉译名对照",
    "修辞学术语译名对照", "修辞学术语索引", "事项索引", "人名索引", "地名索引",
    "西塞罗全集·修辞学卷", "修辞学卷", "西塞罗全集", "正文",
]}
# 页码（含 .3 / ·162 / 4. / 71: 等变体）
_PAGE_PAT = re.compile(r"^[.·．]?\s*\d{1,4}[.·．:：]?$")
# 乱码/装饰行（扫描页边缘噪点: 无汉字短行, 如 "L" "!--" "+++?.4." "4!" "71:" "1 | 24"）
_NOISE_PAT = re.compile(r"^[0-9a-zA-Z|+.:·．!?=*\-~/\\()<>\[\]\"'“”…\s]{1,16}$")
# 孤立标点行（OCR 标点分离: "、" "：： "！." "■" "↓" "=：" 等页内噪点）
_PUNCT_ONLY = re.compile(r"^[、，。：；！？…—·\"'“”‘’【】■↓=*+\-./~|!?()<>\[\]{}]{1,4}$")

def is_hdr(s):
    n = norm(s)
    if n in NAME_HDRS:
        return True
    n2 = re.sub(r"[-·.．\s]+", "", n)  # "论演-说家" / "论·题" 残页眉
    if n2 and n2 in NAME_HDRS:
        return True
    return len(n) <= 2 and bool(re.fullmatch(r"[一-鿿]+", n))  # "论"/"题" 单字残页眉

def is_noise(s):
    n = norm(s)
    if not n:
        return True
    if _PAGE_PAT.match(s):
        return True
    if _NOISE_PAT.match(n):
        return True
    return False

def clean_page(t):
    ls = t.split("\n")
    i = 0
    while i < len(ls):
        s = ls[i].strip()
        if not s or is_hdr(s) or is_noise(s):
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
    for l in ls[i:j]:
        s = l.strip()
        if not s:
            out.append("")
            continue
        if is_noise(s) or is_hdr(s) or _PUNCT_ONLY.match(s):  # 页内页码/页眉/孤立标点
            continue
        out.append(l)
    return "\n".join(out).strip()

pages = [clean_page(PAGES[str(k)]) for k in range(956)]

# ── 章节结构: (part_title_or_None, [(chapter_title, pg_s, cut_line, pg_e)])
# cut_line: 起始页内从第几行开始（卷标题行位置）; 上一章截断到该页 cut_line 前
PARTS = [
    (None, [
        ("中译者导言", 3, None, 32),
    ]),
    ("论公共演讲的理论", [
        ("第一卷", 36, 1, 53),      # 36页行1"第一卷"（行0"正文"为总标题页, 弃）
        ("第二卷", 54, 6, 84),      # 54页行6"第二卷"
        ("第三卷", 85, 11, 108),    # 85页行11"第三卷"
        ("第四卷", 109, 10, 172),   # 109页行10"第四卷"
    ]),
    ("论开题", [
        ("第一卷", 173, None, 232),  # 173-174 内容提要
        ("第二卷", 233, 21, 301),    # 233页行21"第二卷"
    ]),
    (None, [
        ("论最好的演说家", 302, None, 311),
        ("论题", 312, None, 343),
    ]),
    ("论演说家", [
        ("第一卷", 344, None, 421),  # 344-345 提要+人物介绍; 346页行11"第一卷"
        ("第二卷", 422, 2, 532),     # 422页行2"第二卷"
        ("第三卷", 533, 24, 604),    # 533页行24"第三卷"
    ]),
    (None, [
        ("论命运", 605, None, 628),
        ("斯多亚学派的反论", 629, None, 649),
        ("论演讲术的分类", 650, None, 690),
        ("布鲁图", 691, None, 804),
        ("演说家", 805, None, 887),
    ]),
    ("译名对照与索引", [
        ("西汉译名对照", 888, None, 903),
        ("修辞学术语译名对照", 904, None, 910),
        ("修辞学术语索引", 911, None, 933),
        ("事项索引", 934, None, 935),
        ("人名索引", 936, None, 950),
        ("地名索引", 951, None, 955),
    ]),
]
# 导言 5 节（页内标题行定位 → section）
DAOYAN_SECS = ["一、拉丁文化概述", "二、西塞罗生平概要", "三、西塞罗对修辞学的贡献",
               "四、西塞罗的哲学成就", "五、关于全集中译本的若干说明"]
# 索引区章节（词条行无标点结尾, 页间强制分段, 防整章粘连成 1-2 大块）
INDEX_CHS = {"西汉译名对照", "修辞学术语译名对照", "修辞学术语索引", "事项索引", "人名索引", "地名索引"}

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

def join_pages(pg_list, force_sep=False):
    if not pg_list:
        return ""
    full = pg_list[0]
    for t in pg_list[1:]:
        if force_sep or (full and full[-1] in "。！？；：”』」）】…—-"):
            full += "\n\n" + t
        else:
            full += t
    return full

def blocks_from_text(text, hint=None):
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paras:
        paras = [hint or ""]
    return [{"type": "text", "value": v} for v in paras]

# ── 组装各章 ──
toc = []
files = {}
ch_index = 0
warns = []
for part_title, chs in PARTS:
    part_start_ch = ch_index
    # part 条目放组首（C12: 组内 chapter 在 part 之后）
    if part_title:
        toc.append({"type": "part", "title": part_title, "level": 0, "index": part_start_ch})
    for k, (ch_title, pg_s, cut, pg_e) in enumerate(chs):
        # 上一章在此页截断: 找本页标题行
        if cut is not None:
            i0 = split_at_title(pages[pg_s], ch_title)
            if i0 != cut:
                warns.append(f"章[{ch_title}] 预期标题行{cut} 实际{i0} (页{pg_s})")
                cut = i0 if i0 >= 0 else cut
        toc.append({"type": "chapter", "title": ch_title, "index": ch_index, "level": 1})
        segs = []
        if cut is not None:
            hlines = [l for l in pages[pg_s].split("\n")[cut:] if l.strip()]
            if hlines and norm(hlines[0]) == norm(ch_title):
                # 标题行独立成段（防标题拼进正文首段）
                head = hlines[0].strip() + ("\n\n" + "\n".join(hlines[1:]).strip() if len(hlines) > 1 else "")
            else:
                head = "\n".join(hlines).strip()
            segs.append(head)
            mid_s = pg_s + 1
        else:
            segs.append(pages[pg_s])
            mid_s = pg_s + 1
        if mid_s <= pg_e:
            segs.extend(pages[mid_s:pg_e + 1])
        text = join_pages(segs, force_sep=ch_title in INDEX_CHS)
        if ch_title == "中译者导言":
            # 节标题行独立成段（C16: section 锚点块须精确 == 标题行）
            sec_norms = {norm(s) for s in DAOYAN_SECS}
            new_lines = []
            for l in text.split("\n"):
                if norm(l) in sec_norms:
                    if new_lines and new_lines[-1] != "":
                        new_lines.append("")
                    new_lines.append(l.strip())
                    new_lines.append("")
                else:
                    new_lines.append(l)
            text = "\n".join(new_lines)
        blocks = blocks_from_text(text, ch_title)
        files[ch_index] = {"index": ch_index, "title": ch_title, "content": blocks}
        total_chars = sum(len(b["value"]) for b in blocks)
        first = blocks[0]["value"][:30].replace("\n", " ")
        print(f"  [{'part' if part_title else '顶'}] {ch_title} 页{pg_s}-{pg_e} 块{len(blocks)} {total_chars}字 首: {first}…")
        # section（仅导言）: 标题行所在块作锚点（全块搜索）
        if ch_title == "中译者导言":
            for s_title in DAOYAN_SECS:
                tn = norm(s_title)
                hit = None
                for bi, b in enumerate(blocks):
                    if norm(b["value"]) == tn:
                        hit = bi
                        break
                if hit is None:
                    warns.append(f"导言节[{s_title}] 未找到锚点块")
                else:
                    toc.append({"type": "section", "title": s_title, "index": ch_index, "sec": hit, "level": 2})
        ch_index += 1
for w in warns:
    print("⚠", w)

# ── 写盘 ──
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
    "title": "西塞罗全集·修辞学卷",
    "author": "西塞罗",
    "toc": toc,
    "cover": None,
    "chapterCount": len(files),
    "chapterTitles": [ch["title"] for ch in files.values()],
}
json.dump(meta, open(os.path.join(OUT, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ── book_detail 更新 ──
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
print("章节标题:", [ch["title"] for ch in files.values()])
