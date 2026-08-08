# -*- coding: utf-8 -*-
"""三大批判合集（上下）重建: 2 part + 17 章 + ~160 节
从 ckpt 页级 OCR 缓存重建（自然与快乐同模式）。
本书特殊性:
  - 书眉: 《实践理性批判》/《判断力批判》书眉行、'第X卷第X章'式固定书眉、节标题型页眉(行0)
  - 真实节标题行>=1, 章标题页行0 可为真实(exp_pg 特例)
  - 节号'8'前缀噪声 + 罗马数字OCR变体(Ⅵ→V1/Ⅶ→Il/Ⅸ→K区/Ⅲ→血) + 页码粘连(33IX.)
  - 页边码插正文(条34件) -> 行中删
  - FAILED 页 p33(第一卷标题页)/p399(第一章标题页) -> 注入标题行
"""
import json, sys, os, re
sys.stdout.reconfigure(encoding="utf-8")

BASE = os.path.dirname(os.path.abspath(__file__))
CKPT = json.load(open("f:/program/Python/PhiAgent/backend/data/dp_pdf_import_ckpt.json", encoding="utf-8"))
PAGES = CKPT["ocr"]["西方_伊曼努尔_康德_康德三大批判合集_上下_.pdf"]
PAGES = {k: ("" if str(v).strip() == "__FAILED__" else v) for k, v in PAGES.items()}
_INJECT = {"33": "第一卷 纯粹实践理性的分析论", "399": "第一章 目的论判断力的分析论"}
for k, v in _INJECT.items():
    if not PAGES.get(k, "").strip():
        PAGES[k] = v

OUT = "f:/program/Python/PhiAgent/backend/data/book_chapters/10e1874c2255"
DDIR = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters"
BID = "10e1874c2255"

warns = []

# ── 基础工具 ──
def norm(s):
    return re.sub(r"\s+", "", s or "")

def norm2(s):
    return re.sub(r"[^\u4e00-\u9fffA-Za-z0-9]", "", s or "")

def lev(a, b):
    if a == b:
        return 0
    la, lb = len(a), len(b)
    if la < lb:
        a, b = b, a
        la, lb = lb, la
    if lb == 0:
        return la
    prev = list(range(lb + 1))
    for i in range(1, la + 1):
        cur = [i]
        for j in range(1, lb + 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (0 if a[i - 1] == b[j - 1] else 1)))
        prev = cur
    return prev[lb]

# ── 编号解析（数字/全角罗马/拉丁罗马/OCR变体 + '8'前缀 + 页码粘连）──
_ROM_F = {"Ⅰ": 1, "Ⅱ": 2, "Ⅲ": 3, "Ⅳ": 4, "Ⅴ": 5, "Ⅵ": 6, "Ⅶ": 7, "Ⅷ": 8, "Ⅸ": 9, "Ⅹ": 10}
_OCR_ROM = {"M": 8, "血": 3, "K": 9, "区": 9, "Il": 7, "l": 1, "I区": 9}
_LAT = {"I": 1, "V": 5, "X": 10}

def head_num(s):
    if s is None:
        return None
    if re.fullmatch(r"\d{1,3}", s):
        return int(s)
    if s in _ROM_F:
        return _ROM_F[s]
    if re.fullmatch(r"[IVX]{1,4}", s):
        val = 0
        i = 0
        while i < len(s):
            if i + 1 < len(s) and _LAT[s[i]] < _LAT[s[i + 1]]:
                val += _LAT[s[i + 1]] - _LAT[s[i]]
                i += 2
            else:
                val += _LAT[s[i]]
                i += 1
        return val
    if s in _OCR_ROM:
        return _OCR_ROM[s]
    m = re.fullmatch(r"(\d{1,3})([IVX]{1,4})", s)   # 页码粘连 "33IX." -> 取罗马
    if m:
        return head_num(m.group(2))
    m = re.fullmatch(r"([IVX]{1,3})(\d)", s)         # "V1" -> Ⅵ 丢点
    if m:
        return head_num(m.group(1)) + int(m.group(2))
    return None

_HEAD_PAT = re.compile(r"^([0-9]{1,3}|[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]{1,4}|[IVX]{1,4}|[M血K区Il]{1,2}|[0-9]{1,3}[IVX]{1,4}|[IVX]{1,3}[0-9])[.．、]?")

def split_head(s):
    """返回 (编号段原文, 正文norm2)。行首段 = 数字/罗马/变体"""
    m = _HEAD_PAT.match(s.strip())
    if not m:
        return None, norm2(s)
    return m.group(1), norm2(s[len(m.group(0)):])

_BODY_HEAD = re.compile(r"^\s*(?:[0-9]{1,3}[IVX]{1,4}|[IVX]{1,3}[0-9]|[0-9]{1,3}|[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]{1,4}|Il|[IVX]{1,4}|[M血K区Il]{1,2})[.．、]?")

def body_n2(s):
    """拼接文本统一比较: 剥行首编号段(数字/罗马/变体/粘连)后的 norm2"""
    m = _BODY_HEAD.match(s or "")
    if m:
        return norm2(s[m.end():])
    return norm2(s or "")

_LEAD_NOISE = re.compile(r"^\s*[g多]\s*")   # 跨行标题前导 OCR 噪声
_TRAIL_PG = re.compile(r"\d{1,4}\s*$")      # 行尾页码残留

def body_n2_loose(s):
    """松体: 剥前导噪声(g/多) + 首编号段 + 尾页码 后 norm2（跨行标题 OCR 残留）"""
    s = _LEAD_NOISE.sub("", s or "")
    s = body_n2(s)
    return _TRAIL_PG.sub("", s)

def match_sec_loose(line, title):
    """match_sec 的松体版: 剥前导噪声 + 尾页码"""
    s = _LEAD_NOISE.sub("", line or "")
    return match_sec(_TRAIL_PG.sub("", s), title)

def head_eq(ha, hb):
    """编号等价: 相等 / 罗马差1(OCR丢点 ⅤvsⅥ) / 数字剥'8'前缀; 无编号侧放行。
    数字相邻(3vs4)不允许 —— 防近邻节标题模糊误配页眉"""
    if ha is None or hb is None:
        return True
    va, vb = head_num(ha), head_num(hb)
    if va is None or vb is None:
        return True
    if va == vb:
        return True
    is_rom = lambda h: bool(h) and (h[0] in _ROM_F or h[0] in "IVXM血K区Il" or h[0].isdigit() is False)
    if abs(va - vb) == 1 and (is_rom(ha) or is_rom(hb)):
        return True
    if isinstance(va, int) and isinstance(vb, int) and va >= 10 and str(va)[1:] == str(vb):
        return True
    return False

def body_match(ta, tb):
    if ta == tb:
        return True
    if min(len(ta), len(tb)) < 6:
        return False
    if abs(len(ta) - len(tb)) > 3:
        return False
    return lev(ta, tb) <= 2

def match_sec(line, title):
    ha, ba = split_head(line)
    hb, bb = split_head(title)
    if ba == bb:
        return True   # 正文精确匹配 -> head 宽容（OCR 罗马丢点 I vs Ⅶ）
    if not head_eq(ha, hb):
        return False
    return body_match(ba, bb)

# ── 噪声/页眉 ──
_PAGE_PAT = re.compile(r"^\d{1,4}$")
_HDR_CRIT = re.compile(r"^[0-9]{0,4}《(实践理性批判|判断力批判)》.{0,20}$")
_HDR_CH = re.compile(r"^[0-9]{0,4}第[一二三四五六七八九十]+卷第[一二三四五六七八九十]+章")
_NOISE_PAT = re.compile(r"^[0-9a-zA-Z|+.:·．!?=*\-~/\\()<>\[\]\"'“”…\s]{1,16}$")
_PUNCT_ONLY = re.compile(r"^[、，。：；！？…—·\"'“”‘’【】■↓=*+\-./~|!?()<>\[\]{}①②③④⑤⑥⑦⑧⑨⑩]{1,4}$")
_PGEDGE = re.compile(r"(?<=[一-龥])\d{1,3}(?=[一-龥])")
_PGLINE = re.compile(r"^\s*\d{1,4}\s*$")

def is_noise(s):
    n = norm(s)
    if not n:
        return False
    if _PAGE_PAT.match(s):
        return True
    return bool(_NOISE_PAT.match(n))

def is_book_hdr(s):
    n = norm(s)
    return bool(_HDR_CRIT.match(n)) or bool(_HDR_CH.match(n))

# ── 定位 ──
def _join_skip_pg(lines, i, j):
    """拼接行 i..j（跳过纯页码行）"""
    return "".join(x for x in lines[i:j + 1] if not _PGLINE.match(x))

def find_ch_block(lines, title):
    """章题块: 页首3行内 1-3 行拼接(跳过页码行, 剥首编号段) == 标题正文; 无则 match_sec 回退"""
    tbn = body_n2(title)
    for i in range(min(3, len(lines))):
        for j in range(i, min(i + 3, len(lines))):
            if body_n2(_join_skip_pg(lines, i, j)) == tbn:
                return i, j + 1
    for i in range(min(6, len(lines))):
        if match_sec(lines[i], title):
            return i, i + 1
    return -1, -1

def find_major_block(lines, title):
    tbn = body_n2(title)
    for i in range(len(lines)):
        for j in range(i, min(i + 3, len(lines))):
            bn = body_n2(_join_skip_pg(lines, i, j))
            if bn == tbn or bn[::-1] == tbn:
                return i, j + 1
    for i, l in enumerate(lines):
        if match_sec(l, title):
            return i, i + 1
    return -1, -1

def find_sec_range(lines, title, page, exp_pg):
    """exp_pg 页行0 优先(真实标题在版心首行, 防页眉行0被抢);
    行1+ 跨行拼接(剥编号段) == 标题正文; match_sec 单行; 短标题前缀; 行0 特例回退"""
    tbn = body_n2(title)
    if page == exp_pg and len(lines):
        for k in range(0, 3):
            if k >= len(lines):
                break
            if body_n2(_join_skip_pg(lines, 0, k)) == tbn:
                return 0, k + 1
        if match_sec(lines[0], title):
            return 0, 1
    for i in range(1, len(lines)):
        for k in range(0, 3):
            if i + k >= len(lines):
                break
            j = _join_skip_pg(lines, i, i + k)
            if body_n2(j) == tbn or body_n2_loose(j) == tbn:   # 松体: g/多噪声+尾页码
                return i, i + k + 1
    for i in range(1, len(lines)):
        if match_sec(lines[i], title) or match_sec_loose(lines[i], title):
            return i, i + 1
    # 短标题前缀匹配（"第二契机"= 标题前段; 编号形态一致防正文误配）
    hb, bb = split_head(title)
    for i in range(1, len(lines)):
        ha, ba = split_head(lines[i])
        if (ha is None) == (hb is None) and len(ba) >= 4 and len(ba) < len(bb) and bb.startswith(ba):
            return i, i + 1
    if page == exp_pg and len(lines) and match_sec(lines[0], title):
        return 0, 1
    return -1, -1

# ── 结构: (章标题, 首页, 末页, 模式, [(kind, 标题, 预期页)]) kind: major=卷/章级 sec=节 ──
PARTS = [(0, "实践理性批判"), (9, "判断力批判")]

CHS = [
    # ── part1 实践理性批判 ──
    ("中译本序", 10, 17, "prose", []),
    ("序言", 18, 28, "prose", []),
    ("导言", 29, 31, "prose", []),
    ("第一部分 纯粹实践理性的要素论", 32, 161, "prose", [
        ("major", "第一卷 纯粹实践理性的分析论", 33),
        ("major", "第一章 纯粹实践理性的诸原理", 34),
        ("sec", "1.解题", 34),
        ("sec", "2.定理1.", 36),
        ("sec", "3.定理Ⅱ.", 37),
        ("sec", "绎理", 38),
        ("sec", "4.定理Ⅲ.", 42),
        ("sec", "5.课题1.", 44),
        ("sec", "6.课题Ⅱ.", 45),
        ("sec", "7.纯粹实践理性的基本法则", 47),
        ("sec", "8.定理V.", 49),
        ("sec", "Ⅰ.纯粹实践理性原理的演绎", 58),
        ("sec", "Ⅱ.纯粹理性在实践运用中进行一种在思辨运用中它自身不可能的扩展的权利", 66),
        ("major", "第二章 纯粹实践理性的对象的概念", 74),
        ("sec", "就善与恶的概念而言的自由范畴表", 82),
        ("sec", "纯粹实践判断力的模型论", 84),
        ("major", "第三章 纯粹实践理性的动机", 89),
        ("sec", "对纯粹实践理性的分析论的批判性说明", 105),
        ("major", "第二卷 纯粹实践理性的辩证论", 123),
        ("sec", "第一章 纯粹实践理性的一般辩证论", 123),
        ("major", "第二章 纯粹理性在规定至善概念时的辩证论", 126),
        ("sec", "Ⅰ.实践理性的二律背反", 129),
        ("sec", "Ⅱ.对实践理性的二律背反的批判的消除", 130),
        ("sec", "Ⅲ.纯粹实践理性在其与思辨理性结合时的优先地位", 135),
        ("sec", "Ⅳ.灵魂不朽，作为纯粹实践理性的一个悬设", 137),
        ("sec", "Ⅴ.上帝存有，作为纯粹实践理性的一个悬设", 139),
        ("sec", "Ⅵ.总论纯粹实践理性的悬设", 146),
        ("sec", "Ⅶ.如何能够设想纯粹理性在实践意图中的扩展而不与此同时扩展其思辨的知识？", 148),
        ("sec", "Ⅷ.出于纯粹理性的某种需要的认其为真", 156),
        ("sec", "Ⅸ.人的认识能力与他的实践使命的明智适当的比例", 160),
    ]),
    ("第二部分 纯粹实践理性的方法论", 162, 174, "prose", []),
    ("结论", 175, 177, "prose", []),
    ("德汉术语索引", 178, 195, "table", []),
    ("汉德术语对照表", 196, 205, "table", []),
    ("人名索引", 206, 208, "table", []),
    # ── part2 判断力批判 ──
    ("中译本序", 216, 220, "prose", []),
    ("序言", 221, 224, "prose", []),
    ("导言", 225, 249, "prose", [
        ("sec", "Ⅰ.哲学的划分", 225),
        ("sec", "Ⅱ.一般哲学的领地", 227),
        ("sec", "Ⅲ.判断力的批判作为把哲学的这两部分结合为一个整体的手段", 230),
        ("sec", "Ⅳ.判断力，作为一种先天立法能力", 232),
        ("sec", "Ⅴ.自然的形式的合目的性原则是判断力的一个先验原则", 234),
        ("sec", "Ⅵ.愉快的情感和自然合目的性概念的联结", 240),
        ("sec", "Ⅶ.自然的合目的性的审美表象", 241),
        ("sec", "Ⅷ.自然合目的性的逻辑表象", 244),
        ("sec", "Ⅸ.知性和理性的各种立法通过判断力而联结", 247),
    ]),
    ("第一部分 审美判断力批判", 250, 397, "prose", [
        ("major", "第一章 审美判断力的分析论", 252),
        ("major", "第一卷 美的分析论", 252),
        ("sec", "第一契机 鉴赏判断按照质来看的契机", 252),
        ("sec", "1.鉴赏判断是审美的②", 252),
        ("sec", "2.那规定鉴赏判断的愉悦是不带任何利害的①", 253),
        ("sec", "3.对快适的愉悦是与利害结合着的", 254),
        ("sec", "4.对于善的愉悦是与利害结合着的", 256),
        ("sec", "5.三种不同特性的愉悦之比较", 258),
        ("sec", "第二契机 鉴赏判断按照其量来看的契机", 259),
        ("sec", "6.美是无概念地作为一个普遍愉悦的客体被设想的", 259),
        ("sec", "7.按上述特征把美和快适及善加以比较", 260),
        ("sec", "8.愉悦的普遍性在一个鉴赏判断中只表现为主观的", 262),
        ("sec", "9.研究这问题：在鉴赏判断中愉快感先于对象之评判还是后者先于前者", 265),
        ("sec", "第三契机 鉴赏判断按照它里面所观察到的目的关系来看的契机", 267),
        ("sec", "10.一般合目的性", 267),
        ("sec", "11.鉴赏判断只以一个对象（或其表象方式）的合目的性形式为根据", 268),
        ("sec", "12.鉴赏判断基于先天的根据", 269),
        ("sec", "13.纯粹鉴赏判断是不依赖于刺激和激动的", 270),
        ("sec", "14.通过例子来说明", 271),
        ("sec", "15.鉴赏判断完全不依赖于完善性概念", 274),
        ("sec", "16.使一个对象在某个确定概念的条件下被宣称为美的那个鉴赏判断是不纯粹的", 276),
        ("sec", "17.美的理想", 278),
        ("sec", "第四契机 鉴赏判断按照对对象的愉悦的模态来看的契机", 283),
        ("sec", "18.什么是一个鉴赏判断的模态", 283),
        ("sec", "19.我们赋予鉴赏判断的那种主观必然性是有条件的", 284),
        ("sec", "20.鉴赏判断所预定的必然性条件就是共通感的理念", 284),
        ("sec", "21.人们是否有根据预设一个共通感", 285),
        ("sec", "22.在一个鉴赏判断里所想到的普遍赞同的必然性是一种主观必然性，它在某种共通感的前提之下被表象为客观的", 286),
        ("sec", "对分析论第一章的总注释", 287),
        ("major", "第二卷 崇高的分析论", 291),
        ("sec", "23.从对美的评判能力过渡到对崇高的评判能力", 291),
        ("sec", "24.对崇高情感研究的划分", 293),
        ("sec", "A.数学的崇高", 294),
        ("sec", "25.崇高的名称解说", 294),
        ("sec", "26.崇高理念所要求的对自然物的大小估量", 297),
        ("sec", "27.在崇高的评判中愉悦的性质", 303),
        ("sec", "B.自然界的力学的崇高", 306),
        ("sec", "28.作为强力的自然", 306),
        ("sec", "29.对自然界崇高的判断的模态", 310),
        ("sec", "对审美的反思判断力的说明的总注释", 312),
        ("sec", "纯粹审美判断的演绎", 324),
        ("sec", "30.关于自然对象的审美判断的演绎不可针对我们在自然中称为崇高的东西，而只能针对美", 324),
        ("sec", "31.鉴赏判断的演绎的方法", 325),
        ("sec", "32.鉴赏判断的第一特性", 326),
        ("sec", "33.鉴赏判断的第二特性", 328),
        ("sec", "34.不可能有鉴赏的任何客观原则", 330),
        ("sec", "35.鉴赏的原则是一般判断力的主观原则", 331),
        ("sec", "36.鉴赏判断之演绎的课题", 332),
        ("sec", "37.在对一个对象的鉴赏判断中真正先天地断言的是什么？", 333),
        ("sec", "38.鉴赏判断的演绎", 334),
        ("sec", "39.感觉的可传达性", 335),
        ("sec", "40.鉴赏作为共通感的一种", 337),
        ("sec", "41.对美的经验性的兴趣", 340),
        ("sec", "42.对美的智性的兴趣", 342),
        ("sec", "43.一般的艺术", 346),
        ("sec", "44.美的艺术", 348),
        ("sec", "45.美的艺术是一种当它同时显得像是自然时的艺术", 349),
        ("sec", "46.美的艺术是天才的艺术", 350),
        ("sec", "47.对上述有关天才的说明的阐释和证明", 352),
        ("sec", "48.天才对鉴赏的关系", 354),
        ("sec", "49.构成天才的各种内心能力", 356),
        ("sec", "50.在美的艺术的作品里鉴赏力和天才的结合", 362),
        ("sec", "51.美的艺术的划分", 363),
        ("sec", "52.在同一个作品里各种美的艺术的结合", 368),
        ("sec", "53.各种美的艺术相互之间审美价值的比较", 369),
        ("sec", "54.注释", 373),
        ("major", "第二章 审美判断力的辩证论", 379),
        ("sec", "56.鉴赏的二律背反的表现", 379),
        ("sec", "57.鉴赏的二律背反的解决", 381),
        ("sec", "58.自然及艺术的合目的性的观念论，作为审美判断力的唯一原则", 388),
        ("sec", "59.美作为德性的象征", 392),
        ("sec", "60.附录鉴赏的方法论", 395),
    ]),
    ("第二部分 目的论判断力批判", 398, 520, "prose", [
        ("major", "第一章 目的论判断力的分析论", 399),
        ("sec", "61.自然界的客观合目的性", 400),
        ("sec", "62.与质料上的客观合目的性不同的单纯形式上的客观合目的性", 402),
        ("sec", "63.自然的相对合目的性区别于自然的内在合目的性", 406),
        ("sec", "64.作为自然目的之物的特有性质", 409),
        ("sec", "65.作为自然目的之物就是有机物", 411),
        ("sec", "66.评判有机物中的内在合目的性的原则", 415),
        ("sec", "67.把一般自然从目的论上评判为目的系统的原则", 417),
        ("sec", "68.目的论原则作为自然科学的内部原则", 420),
        ("major", "第二章 目的论判断力的辩证论", 424),
        ("sec", "69.什么是判断力的二律背反", 424),
        ("sec", "70.这种二律背反的表现", 425),
        ("sec", "71.解决上述二律背反的准备", 427),
        ("sec", "72.关于自然的合目的性的各种各样的系统", 428),
        ("sec", "73.上述系统没有一个做到了它所预定的事", 431),
        ("sec", "74.不能独断地处理自然技艺概念的原因是自然目的之不可解释性", 434),
        ("sec", "75.自然的客观合目的性概念是反思性判断力的一条理性批判原则", 436),
        ("sec", "76.注释", 439),
        ("sec", "77.使自然目的概念对我们成为可能的那种人类知性的性质", 443),
        ("sec", "78.物质的普遍机械作用原则与自然技术中的目的论原则的结合", 448),
        ("major", "附录 目的论判断力的方法论", 453),
        ("sec", "79.是否必须把目的论当作属于自然学说的来讨论", 453),
        ("sec", "80.在将一物解释为自然目的时机械论原则必须从属于目的论原则", 454),
        ("sec", "81.在解释一个作为自然产物的自然目的时机械论对目的论原则的参与", 458),
        ("sec", "82.在有机物的外在关系中的目的论体系", 461),
        ("sec", "83.作为一个目的论系统的自然的最后目的", 466),
        ("sec", "84.一个世界的存有的终极目的即创造本身的终极目的", 470),
        ("sec", "85.自然神学", 472),
        ("sec", "86.伦理学神学", 478),
        ("sec", "87.上帝存有的道德证明", 482),
        ("sec", "88.这个道德证明的有效性的限制", 488),
        ("sec", "89.这个道德证明的用处", 494),
        ("sec", "90.在上帝存有的目的论证明中的认其为真之方式", 496),
        ("sec", "91.由实践的信念而来的认其为真的方式", 501),
        ("sec", "对于目的论的总注释", 509),
    ]),
    ("附录：第一导言", 521, 568, "prose", [
        ("sec", "Ⅰ.作为体系的哲学", 521),
        ("sec", "Ⅱ.为哲学奠基的高级认识能力的体系", 525),
        ("sec", "Ⅲ.人的内心一切能力的体系", 528),
        ("sec", "Ⅳ.对判断力成为系统的经验", 530),
        ("sec", "Ⅴ.反思性的判断力", 532),
        ("sec", "Ⅵ.作为这样多特殊系统的诸自然形式的合目的性", 537),
        ("sec", "Ⅶ.判断力的技术，作为某种自然技术之理念的根据", 538),
        ("sec", "Ⅷ.评判能力的感性学（Aesthetik）", 542),
        ("sec", "Ⅸ.目的论的评判", 550),
        ("sec", "Ⅹ.寻求一条技术性的判断力的原则", 555),
        ("sec", "Ⅺ.在纯粹理性批判体系中判断力批判的全景式的导论", 560),
    ]),
    ("汉德词汇索引", 569, 594, "table", []),
]

# 全部标题（节标题型行删除用; 短标题不参与行删除）
ALL_TITLES = [t for _, _, _, _, secs in CHS for _, t, _ in secs]
SEC_DEL = [t for t in ALL_TITLES if len(norm2(t)) >= 4]

# ── 0) 页级预处理（标题与正文粘连/书名式页眉/竖排标题）──
def preprocess_pages():
    # p10/p216: 行0"《…》中译本序" -> "中译本序"
    for pg, old, new in (("10", "《实践理性批判》中译本序", "中译本序"),
                         ("216", "《判断力批判》中译本序", "中译本序")):
        ls = PAGES[pg].split("\n")
        if ls and norm(ls[0]) == norm(old):
            ls[0] = new
            PAGES[pg] = "\n".join(ls)
    # p29: 行1"导言实践理性批判的理念" 拆为 "导言"标题 + 正文
    ls = PAGES["29"].split("\n")
    for i, l in enumerate(ls):
        if norm(l).startswith("导言") and len(norm(l)) > 2:
            rest = norm(l)[2:]
            ls.insert(i, "导言")
            ls[i + 1] = rest
            break
    PAGES["29"] = "\n".join(ls)
    # p206: 竖排"人/名/索" -> 单行"人名索引"
    ls = PAGES["206"].split("\n")
    if len(ls) >= 3 and norm(ls[0]) == "人" and norm(ls[1]) == "名":
        ls[0] = "人名索引"
        ls[1] = ""
        ls[2] = ""
        PAGES["206"] = "\n".join(ls)

preprocess_pages()

# ── 1) 定位全部锚点: keep = {pg: {li: 规范标题}} (跨行锚点后续行 li -> None) ──
keep = {}

def mark(pg, li, title):
    if li < 0:
        return
    keep.setdefault(pg, {})[li] = title

for ch_title, pg_s, pg_e, mode, secs in CHS:
    hit = None
    for pg in range(max(0, pg_s - 1), pg_s + 2):
        i, j = find_ch_block(PAGES.get(str(pg), "").split("\n"), ch_title)
        if i >= 0:
            hit = (pg, i, j)
            break
    if hit:
        pg, i, j = hit
        keep.setdefault(pg, {})[i] = ch_title
        for li in range(i + 1, j + 1):
            keep.setdefault(pg, {}).setdefault(li, None)   # 不覆盖已有锚点
    else:
        warns.append(f"!! 章未定位: {ch_title} @{pg_s}")
    for kind, sec_title, exp_pg in secs:
        found = None
        # exp_pg 优先（真实标题在首页行0），其余按距离升序 —— 防相邻页页眉抢占
        pgs = sorted(
            range(max(pg_s, exp_pg - 2), min(pg_e, exp_pg + 3) + 1),
            key=lambda p: (p != exp_pg, abs(p - exp_pg)),
        )
        for pg in pgs:
            lines = PAGES.get(str(pg), "").split("\n")
            if kind == "major":
                rng = find_major_block(lines, sec_title)
                if rng[0] >= 0:
                    found = (pg, rng)
                    break
            else:
                a, b = find_sec_range(lines, sec_title, pg, exp_pg)
                if a >= 0:
                    found = (pg, (a, b))
                    break
        if found:
            pg, (a, b) = found
            keep.setdefault(pg, {})[a] = sec_title
            for li in range(a + 1, b + 1):
                keep.setdefault(pg, {}).setdefault(li, None)   # 不覆盖已有锚点
        else:
            warns.append(f"!! 节未定位: {ch_title} > {sec_title} @{exp_pg}")

print(f"定位完成: {len(keep)} 页有锚点, {len(warns)} 条未定位警告")

# ── 2) 清洗 + 锚点替换（合并: keep 行直接替换为规范标题, 前后插空行独立成段）──
def clean_page(t, keep_map, permissive=False):
    ls = t.split("\n")
    out = []
    for k, l in enumerate(ls):
        s = l.strip()
        n = norm(s)
        if k in keep_map:
            v = keep_map[k]
            if v is None:            # 跨行锚点的后续行 -> 删
                continue
            if out and out[-1] != "":
                out.append("")
            out.append(v)
            out.append("")
            continue
        if not s:
            out.append("")
            continue
        if is_noise(s) or is_book_hdr(s) or _PUNCT_ONLY.match(s):
            continue
        if not permissive and _NOISE_PAT.match(n):
            continue
        # 节标题型行（页眉/重复/OCR变体）-> 删; 真实标题在 keep
        if not permissive:
            hit = False
            ss = re.sub(r"\d{1,3}$", "", s)     # 剥行尾页码（页眉变体"…原则231"）
            for t2 in SEC_DEL:
                if match_sec(ss, t2) or match_sec_loose(ss, t2):
                    hit = True
                    break
            if not hit and k == 0:
                # 行0 页眉位: 匹配标题任意连续子串(>=8字) —— 页眉截断变体"58.作为审美判断力的唯一原则"
                n0 = norm2(ss)
                if len(n0) >= 8:
                    for t2 in SEC_DEL:
                        tn2 = norm2(t2)
                        if len(tn2) >= 8 and tn2 in n0:
                            hit = True
                            break
                # 行0 = 标题前段（页眉截断变体"M.判断力的技术"/"V.判断力的技术"）: head 等价或罗马差≤2 + body 是标题前段
                if not hit and len(n0) >= 5:
                    for t2 in SEC_DEL:
                        ha, ba = split_head(ss)
                        hb, bb = split_head(t2)
                        ok = head_eq(ha, hb)
                        if not ok and ha and hb:
                            va, vb = head_num(ha), head_num(hb)
                            if va is not None and vb is not None and abs(va - vb) <= 2 and \
                               (ha[0] in _ROM_F or ha[0] in "IVXM血K区Il" or not ha[0].isdigit()) and \
                               (hb[0] in _ROM_F or hb[0] in "IVXM血K区Il" or not hb[0].isdigit()):
                                ok = True
                        if ok and len(bb) >= len(ba) and bb.startswith(ba):
                            hit = True
                            break
            if hit:
                continue
        out.append(l)
    return "\n".join(out).strip()

def join_pages(pg_list):
    return "\n\n".join(s for s in pg_list if s)

# ── 3) 断段 ──
_FOOT = re.compile(r"^[①②③④⑤⑥⑦⑧⑨⑩]")

def split_prose(text):
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

def line_paras(text):
    return [{"type": "text", "value": p.strip()} for p in text.split("\n") if p.strip()]

def blocks_from_text(text, hint=None):
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if not paras:
        paras = [hint or ""]
    return [{"type": "text", "value": v} for v in paras]

# ── 4) 组装 ──
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
    cleaned = []
    for k in range(pg_s, pg_e + 1):
        t = PAGES.get(str(k), "")
        if not t.strip():
            continue
        t = _PGEDGE.sub("", t)
        c = clean_page(t, keep.get(k, {}), permissive=(mode == "table"))
        if c.strip():
            cleaned.append(c)
    text = join_pages(cleaned)
    if mode == "prose":
        text = split_prose(text)
        blocks = blocks_from_text(text, ch_title)
    else:  # table
        blocks = line_paras(text)
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

# ── 5) 抽查全部节锚点 ──
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

# ── 6) 写盘 ──
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
    "title": "康德三大批判合集（上下）",
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

print(f"\n完成: {len(files)} 章 + 2 part + {sec_total} 节, {sum(len(v['content']) for v in files.values())} 块")
