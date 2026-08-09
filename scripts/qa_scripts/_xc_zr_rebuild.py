# -*- coding: utf-8 -*-
"""自然与快乐 重建（目录驱动, 2026-08-08 v1）
问题: 旧版 81 章平铺（书内数字.格式节标题被误当章节）+ A2 压扁（OCR 无段落空行）+ 0 part。
依据: 书内目录(p14-15) 印刷页码→PDF 偏移 +15（3→p18, 84→p99, 218→p233 验证）。
结构: 2 part（上编 伊壁鸠鲁文存 index=3 / 下编 万物本性论 index=12）+ 19 章 + 88 节。
前置(顶层): 2016年再版序/2004年译丛总序/中译者导言; 译名对照表顶层（同 CPR 索引章）。
上编: 9 篇（3 书信 18 节数字.格式 + 遗嘱/临终书信 + 4 格言条目章）。
下编: 6 卷卢克莱修诗体, 每卷 大节(一~四,汉字数字)+数字小节 全做 section; 散文断段
（2026-08-09 修复: 源页为 20-32 字窄栏行, 行级拆段导致读者端每段半行宽右半空白）,
对照表行级拆段。
页眉: 偶页=书名+部分名（自然与快乐：伊壁鸠鲁的哲学1上编伊壁鸠鲁文存）, 奇页=章名（可带篇序号前缀）。
OCR 无段落空行 → 散文行尾句号(。！？…)断段+脚注标记(①…)强制断段; 格言编号行(^\d+[.．])断段。
孤立单字一~九行: 诗体删; 散文仅当紧邻标题块删（p18"一"篇序号）, 正文保留（p11 导言"二"）。
用法: python _xc_zr_rebuild.py
"""
import sys, os, json, re
sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.abspath(__file__))
PAGES = json.load(open(os.path.join(BASE, "_xc_tmp_pages.json"), encoding="utf-8"))
# __FAILED__ 页 = 空白/篇章间隔页, 视为空页（不产生文本块）
PAGES = {k: ("" if str(v).strip() == "__FAILED__" else v) for k, v in PAGES.items()}
N = len(PAGES)
BID = "221f09d04944"
OUT = rf"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
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

_PAGE_PAT = re.compile(r"^\d{1,3}$")          # 页号/脚注号
_HDR_BOOK = re.compile(r"^自然与快乐[:：]?伊壁鸠鲁的哲学[0-9A-Za-z！!|丨：:]{0,8}[0-9一-龥：:]{0,18}$")
_NUM_CHAR = "一二三四五六七八九"
_NOISE_PAT = re.compile(r"^[0-9a-zA-Z|+.:·．!?=*\-~/\\()<>\[\]\"'“”…\s]{1,16}$")
_PUNCT_ONLY = re.compile(r"^[、，。：；！？…—·\"'“”‘’【】■↓=*+\-./~|!?()<>\[\]{}①②③④⑤⑥⑦⑧⑨⑩]{1,4}$")
_ITEM_PAT = re.compile(r"^\d+[.．]")          # 格言条目编号行
_LONE_CN = re.compile(r"^[一二三四五六七八九]$")
_FOOT = re.compile(r"^[①②③④⑤⑥⑦⑧⑨⑩]")
_HAN_NUM_PRE = re.compile(r"^[一二三四五六七八九]")

CH_TITLES = [
    "2016年再版序", "2004年译丛总序", "中译者导言",
    "致希罗多德信（论自然纲要）", "致皮索克勒信（天文学纲要）", "致梅瑙凯信（伦理学纲要）",
    "伊壁鸠鲁的遗嘱", "伊壁鸠鲁临终书信", "伊壁鸠鲁基本要道",
    "《梵蒂冈馆藏格言集》", "贤人论", "奥依诺安达的第欧根尼 铭文残篇选",
    "第一卷 原子与虚空", "第二卷 原子的运动与性质", "第三卷 灵魂的本性",
    "第四卷 灵魂的功能", "第五卷 世界和文明的起源发展", "第六卷 天文地理和疾病",
    "译名对照表",
]
HDRS = {norm(s) for s in CH_TITLES}

def is_noise(s):
    n = norm(s)
    if not n:
        return False
    if _PAGE_PAT.match(s):
        return True
    return bool(_NOISE_PAT.match(n))

def is_hdr(n):
    """页眉: 章名(可带编号前缀/OCR 微变) 或 书名+部分名"""
    if n in HDRS:
        return True
    if _HDR_BOOK.match(n):
        return True
    if n and _HAN_NUM_PRE.match(n) and n[1:] in HDRS:
        return True
    for h in HDRS:
        if len(h) >= 6 and fuzzy_equal(n, h):
            return True
    return False

def clean_page(t, keep_lines, mode, permissive=False):
    ls = t.split("\n")
    i = 0
    while i < len(ls):
        if i in keep_lines:
            break
        s = ls[i].strip()
        n = norm(s)
        if not s or is_noise(s) or is_hdr(n) or n == "厂":
            i += 1
            continue
        break
    j = len(ls)
    while j > i:
        s = ls[j - 1].strip()
        if is_noise(s) or is_hdr(norm(s)):
            j -= 1
            continue
        break
    out = []
    last_was_keep = False
    for k, l in enumerate(ls[i:j], start=i):
        s = l.strip()
        n = norm(s)
        if not s:
            out.append("")
            last_was_keep = False
            continue
        if k in keep_lines:
            out.append(l)
            last_was_keep = True
            continue
        if is_noise(s) or is_hdr(n) or n == "厂" or _PUNCT_ONLY.match(s):
            last_was_keep = False
            continue
        if _LONE_CN.match(n):
            # 诗体: 装饰编号行删; 散文: 紧邻标题块的篇序号删, 正文分节编号保留
            if mode == "poem" or last_was_keep:
                last_was_keep = False
                continue
            out.append(l)
            last_was_keep = False
            continue
        if permissive:
            out.append(l)
            last_was_keep = False
            continue
        if _NOISE_PAT.match(n):
            last_was_keep = False
            continue
        out.append(l)
        last_was_keep = False
    return "\n".join(out).strip()

def match_line(line, title):
    n, n2 = norm(line), norm2(line)
    if not n:
        return False
    tn, tn2 = norm(title), norm2(title)
    if tn2 and n2 == tn2:
        return True
    if tn2 and fuzzy_equal(n2, tn2):
        return True
    return False

def find_ch_block(lines, title):
    """章题块: 连续 1-3 行拼接(norm2) == 标题（可剥"一二三…九"篇序号前缀）; 仅页首 3 行"""
    tn2 = norm2(title)
    for i in range(min(3, len(lines))):
        for j in range(i, min(i + 3, len(lines))):
            bn = norm2("".join(lines[i:j + 1]))
            if bn == tn2:
                return i, j + 1
            if len(bn) > len(tn2) and bn[1:] == tn2 and _HAN_NUM_PRE.match(bn):
                return i, j + 1
    return -1, -1

def find_major_block(lines, title):
    """大节标题块: 单行/跨行拼接(正反) / '序诗'单行特例 / fuzzy 单行（OCR 噪声'一'）"""
    tn2 = norm2(title)
    if title.endswith("、序诗"):
        for i, l in enumerate(lines):
            if norm2(l) == "序诗":
                return i, i + 1
    for i in range(len(lines)):
        for j in range(i, min(i + 3, len(lines))):
            bn = norm2("".join(lines[i:j + 1]))
            if bn == tn2 or bn[::-1] == tn2:
                return i, j + 1
    for i, l in enumerate(lines):
        if fuzzy_equal(norm2(l), tn2):
            return i, i + 1
    return -1, -1

def find_sec_line(lines, title):
    for li, l in enumerate(lines):
        if match_line(l, title):
            return li
    return -1

def join_pages(pg_list):
    return "\n\n".join(s for s in pg_list if s)

# ── 结构: (章标题, 首页, 末页, 模式, [(kind, 标题, 预期页)]) kind: major=大节 sec=小节 ──
CHS = [
    ("2016年再版序", 3, 4, "prose", []),
    ("2004年译丛总序", 5, 7, "prose", []),
    ("中译者导言", 8, 13, "prose", []),
    ("致希罗多德信（论自然纲要）", 18, 33, "prose", [
        ("sec", "1.导论①", 18), ("sec", "2.标准", 19), ("sec", "3.基本原则", 19),
        ("sec", "4.影像与感觉", 22), ("sec", "5.原子及其属性", 24), ("sec", "6.灵魂及其性质", 27),
        ("sec", "7.属性与偶性", 28), ("sec", "8.其他世界", 30), ("sec", "9.语言和文化的产生", 30),
        ("sec", "10.天体", 31), ("sec", "11.结论", 32),
    ]),
    ("致皮索克勒信（天文学纲要）", 34, 43, "prose", [
        ("sec", "1.方法论", 34), ("sec", "2.诸世界", 35), ("sec", "3.气象学", 38),
        ("sec", "4.关于星星的一些问题", 41), ("sec", "5.结论", 43),
    ]),
    ("致梅瑙凯信（伦理学纲要）", 44, 48, "prose", [
        ("sec", "1.幸福的前提", 44), ("sec", "2.美好生活", 46),
    ]),
    ("伊壁鸠鲁的遗嘱", 49, 50, "prose", []),
    ("伊壁鸠鲁临终书信", 51, 51, "prose", []),
    ("伊壁鸠鲁基本要道", 52, 56, "items", []),
    ("《梵蒂冈馆藏格言集》", 57, 63, "items", []),
    ("贤人论", 64, 66, "items", []),
    ("奥依诺安达的第欧根尼 铭文残篇选", 67, 67, "items", []),
    ("第一卷 原子与虚空", 70, 98, "poem", [
        ("major", "一、序诗", 70), ("major", "二、原子与虚空", 74), ("sec", "1.原子：物质的永恒性", 74),
        ("sec", "2.虚空的存在及其性质", 78), ("sec", "3.除了原子与虚空，没有其他独立存在者", 80),
        ("sec", "4.物质永恒性再证明", 82), ("major", "三、批驳其他自然哲学家的始基论", 86),
        ("sec", "1.批评赫拉克里特（一本原说）", 86), ("sec", "2.批评恩培多克勒（四元素说）", 88),
        ("sec", "3.批评阿那克萨戈拉（种子说）", 91), ("major", "四、宇宙无限", 93),
    ]),
    ("第二卷 原子的运动与性质", 99, 129, "poem", [
        ("major", "一、序诗", 99), ("major", "二、原子的运动", 100), ("sec", "1.原子永远快速运动", 100),
        ("sec", "2.原子的向下运动和偏斜", 104), ("major", "三、原子的形状和它们的结合", 107),
        ("sec", "1.原子的形状多样，但不是无限多样", 107), ("sec", "2.同一种形状的原子数量无限", 112),
        ("sec", "3.事物由多种原子组成", 114), ("sec", "4.原子组成事物的方式不是无穷多", 117),
        ("major", "四、原子没有宏观事物的特性", 118), ("sec", "1.原子没有颜色、冷热", 118),
        ("sec", "2.原子没有心理活动", 121), ("sec", "5.世界数量无限，有生有灭", 124),
    ]),
    ("第三卷 灵魂的本性", 130, 160, "poem", [
        ("major", "一、序诗", 130), ("major", "二、灵魂的本性", 132), ("sec", "1.灵魂是干分精细的物体", 132),
        ("sec", "2.灵魂不能独立于身体存在", 139), ("sec", "3.灵魂是有死的", 141),
        ("major", "三、怕死的愚蠢", 152), ("sec", "1.死与我们无关", 152),
    ]),
    ("第四卷 灵魂的功能", 161, 194, "poem", [
        ("major", "一、序诗", 161), ("major", "二、影像与感觉", 162), ("sec", "2.影像与视觉，感觉的可靠性", 166),
        ("sec", "3.听觉、味觉与嗅觉", 174), ("major", "三、心灵与影像", 179), ("sec", "1.影像与心灵", 179),
        ("sec", "2.批判目的论", 182), ("sec", "3.睡眠与梦", 184), ("major", "四、情欲", 187),
        ("sec", "1.情爱徒劳无益", 187), ("sec", "2.情欲应当服务于生育", 191),
    ]),
    ("第五卷 世界和文明的起源发展", 195, 232, "poem", [
        ("major", "一、序诗", 195), ("sec", "1.序诗A", 195), ("sec", "2.序诗B", 197),
        ("major", "二、世界的起源", 198), ("sec", "1.世界不是神圣的和永恒的", 198), ("sec", "2.世界的形成", 205),
        ("sec", "3.天象，天体的运动", 208), ("sec", "4.昼夜和季节的变化", 211), ("sec", "5.大地的幼年", 214),
        ("major", "三、人类和文明的起源", 218), ("sec", "1.原始人的生活", 218), ("sec", "2.语言的出现", 220),
        ("sec", "3.国家法律的出现", 223), ("sec", "4.宗教的起源", 224), ("sec", "5.金属工具和武器的发明", 226),
        ("major", "四、享受大自然的快乐", 230),
    ]),
    ("第六卷 天文地理和疾病", 233, 268, "poem", [
        ("major", "一、序诗", 233), ("major", "二、气象的解释", 236), ("sec", "1.打雷和闪电", 236),
        ("sec", "2.霹雳", 239), ("sec", "3.海旋、云、雨和彩虹", 245), ("major", "三、地理“异常现象”解释", 248),
        ("sec", "1.地震", 248), ("sec", "2.火山爆发，尼罗河泛滥", 251), ("sec", "4.磁石", 258),
        ("major", "四、疾病与瘟疫", 263), ("sec", "1.疾病的原因", 263), ("sec", "2.雅典的瘟疫", 265),
    ]),
    ("译名对照表", 269, 272, "table", []),
]
PARTS = [(3, "上编 伊壁鸠鲁文存"), (12, "下编 万物本性论")]

PERMISSIVE = {pg for t, a, b, m, _s in CHS if m == "table" for pg in range(a, b + 1)}

# ── 1) 定位全部保留行 ──
keep = {}
warns = []

def mark(pg, li):
    if li >= 0:
        keep.setdefault(pg, set()).add(li)

for ch_title, pg_s, pg_e, mode, secs in CHS:
    i, j = find_ch_block(PAGES.get(str(pg_s), "").split("\n"), ch_title)
    if i < 0:
        warns.append(f"章[{ch_title}] 页{pg_s} 标题块未定位")
    for li in range(i, j):  # [i, j) 半开: j 为块后第一行
        mark(pg_s, li)
    for kind, sec_title, exp_pg in secs:
        hit = (-1, -1)
        for pg in range(max(pg_s, exp_pg - 2), min(pg_e, exp_pg + 3) + 1):
            lines = PAGES.get(str(pg), "").split("\n")
            if kind == "major":
                rng = find_major_block(lines, sec_title)
            else:
                li = find_sec_line(lines, sec_title)
                rng = (li, li) if li >= 0 else (-1, -1)
            if rng[0] >= 0:
                hit = (pg, rng)
                break
        if hit[0] < 0:
            warns.append(f"[{kind}] {sec_title} 预期页{exp_pg} 未定位")
        else:
            for li in range(hit[1][0], hit[1][1]):  # 半开区间
                mark(hit[0], li)

print("定位: 保留行页数", len(keep), "警告", len(warns))
for w in warns:
    print("⚠", w)

# ── 2) 清洗全部页（按章模式: 诗体/散文/条目/对照表 的孤立单字处理不同）──
pages = [""] * N
for ch_title, pg_s, pg_e, mode, secs in CHS:
    for k in range(pg_s, pg_e + 1):
        pages[k] = clean_page(PAGES[str(k)], keep.get(k, set()), mode, permissive=(k in PERMISSIVE))

# ── 3) 页级标题替换（章/大节/小节 → 标准标题段）──
def apply_replacements(page_lines, items):
    repl = {}
    for kind, title in items:
        if kind == "ch":
            rng = find_ch_block(page_lines, title)
            if rng[0] < 0:
                continue
        elif kind == "major":
            rng = find_major_block(page_lines, title)
            if rng[0] < 0:
                continue
        else:
            li = find_sec_line(page_lines, title)
            rng = (li, li + 1) if li >= 0 else (-1, -1)
            if li < 0:
                continue
        repl[rng[0]] = title
        for x in range(rng[0] + 1, rng[1]):
            repl[x] = None
    if not repl:
        return page_lines
    out = []
    for i, l in enumerate(page_lines):
        if i in repl:
            v = repl[i]
            if v:
                if out and out[-1] != "":
                    out.append("")
                out.append(v)
                out.append("")
        else:
            out.append(l)
    return out

# ── 4) 断段 ──
def split_prose(text):
    """散文: 空行保留为段界; 行尾句号(。！？…)断段 + 脚注标记(①…)强制断段（OCR 无段落空行）"""
    lines = text.split("\n")
    out = []
    for l in lines:
        s = l.strip()
        if not s:
            out.append("")
            continue
        if _FOOT.match(s) and out and out[-1] != "":
            out.append("")
        out.append(s)
        if re.search(r"[。！？…]$", s) and out and out[-1] != "":
            out.append("")
    return "\n".join(out)

def split_items(text):
    """格言: 空行保留为段界; 编号行(^\d+[.．])断段, 条目内续行保留"""
    lines = text.split("\n")
    out = []
    for l in lines:
        s = l.strip()
        if not s:
            out.append("")
            continue
        if _ITEM_PAT.match(s) and out and out[-1] != "":
            out.append("")
        out.append(s)
    return "\n".join(out)

def line_paras(text):
    """诗体/对照表: 行级拆段（每行独立成段）"""
    return [{"type": "text", "value": p.strip()} for p in text.split("\n") if p.strip()]

def blocks_from_text(text, hint=None):
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paras:
        paras = [hint or ""]
    return [{"type": "text", "value": v} for v in paras]

# ── 5) 组装章节 ──
toc = []
files = {}
ch_index = 0
sec_total = 0

for ch_title, pg_s, pg_e, mode, secs in CHS:
    if ch_index == PARTS[0][0]:
        toc.append({"type": "part", "title": PARTS[0][1], "level": 0, "index": ch_index})
    if ch_index == PARTS[1][0]:
        toc.append({"type": "part", "title": PARTS[1][1], "level": 0, "index": ch_index})
    toc.append({"type": "chapter", "title": ch_title, "index": ch_index, "level": 1})
    # 页级替换（章标题 + 本页大节/小节）
    cleaned = []
    for k in range(pg_s, pg_e + 1):
        items = [("ch", ch_title)] if k == pg_s else []
        items += [(kind, t) for kind, t, e in secs if e in range(k - 2, k + 4)]
        cleaned.append(apply_replacements(pages[k].split("\n"), items))
    text = join_pages(["\n".join(c) for c in cleaned])
    if mode == "prose":
        text = split_prose(text)
        blocks = blocks_from_text(text, ch_title)
    elif mode == "items":
        text = split_items(text)
        blocks = blocks_from_text(text, ch_title)
    elif mode == "table":  # 对照表: 行级拆段（每行独立成段）
        blocks = line_paras(text)
    else:  # poem: 窄栏散文行 → 散文断段（2026-08-09 修复行级拆段右半空白）
        text = split_prose(text)
        blocks = blocks_from_text(text, ch_title)
    sec_anchors = {}
    for kind, sec_title, exp_pg in secs:
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

# ── 6) 抽查全部节锚点（前块尾/本块首/后块首）──
print("\n===== 节锚点抽查 =====")
bad = 0
for ci, ch in files.items():
    meta_toc = [t for t in toc if t["type"] == "section" and t["index"] == ci]
    for t in meta_toc:
        at = t["sec"]
        blocks = ch["content"]
        prev = blocks[at - 1]["value"][-20:] if at > 0 else "(无前块)"
        cur = blocks[at]["value"][:20]
        nxt = blocks[at + 1]["value"][:20] if at + 1 < len(blocks) else "(无后块)"
        print(f"[{ch['title']}] {t['title']} @{at}: 前…{prev!r} | 本{cur!r} | 后{nxt!r}")

# ── 7) 写盘 ──
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
    "title": "自然与快乐",
    "author": "伊壁鸠鲁、卢克莱修",
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
print(f"\nchapterCount={len(files)}, toc 条目={len(toc)} (part2 章{len(files)} 节{sec_total}), 全文字数={total_chars}")
