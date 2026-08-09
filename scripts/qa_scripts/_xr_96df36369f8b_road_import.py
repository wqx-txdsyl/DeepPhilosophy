# -*- coding: utf-8 -*-
"""结构之后的路（96df36369f8b）主线1补录入库（库恩，邱慧译，北京大学出版社）
OCR 正在补尾（引擎从 121 页续 OCR 到 181 页）。等 checkpoint 该 key 满 181 页后运行。
结构（对照目录页 + 标题行定位，双页扫描页序，三套独立印刷页码）:
  页0-2 书名页与简介 | 3 目录(弃)
  页4-5 前言（杰海娜·库恩）| 页5'■编者导言■'起-页10左栏 编者导言
  页10右栏-20 第一章什么是科学革命 | 21-34 第二章可通约性 | 35-50 第三章科学史中的可能世界
  51-58 第四章《结构》之后的路 | 59-66 第五章历史的科学哲学之困扰
  67右栏-95 第六章回应我的批评者 | 96-106左栏 第七章对斯尼德形式主义的评论
  106右栏-112左栏 第八章科学中的隐喻 | 112右栏-117左栏 第九章合理性与理论选择
  117右栏-120+ 第十章自然科学与人文科学
  121特殊 第十一章后记 | 122-135 整页 | 136左栏 后记尾
  136右栏+137-168 第三部分：与托马斯·库恩的讨论（访谈，双页交错奇偶分流）
特殊页（双栏交错，人工重组）:
  页10: 左栏=编者导言尾段（'第三部分：与托马斯·库恩的讨论'…'完整重印。''本书最后附上了…'）
        右栏='第一部分''■重审科学革命''第一章什么是科学革命'+编者按+正文
  页67: 左栏=第五章尾（行0-9 交错），右栏='第二部分''■评论与答复■''第六章回应我的批评者'
  页106/112/117: 左栏=上章尾，右栏=下章标题+头（行级切分）
  页121: 双页交错（222页=正文前半'在接受这件礼物时'…'普遍化。（1）'；223页=标题'第十一章后记'
        +编者按'《后记》是库恩对九篇文章的回应…'+正文后半'重读这本论文集中的文章…'）
  页136: 左栏=后记尾2段（行2,4,5,7,8,10,12,14,15,17,19,21,23），右栏=第三部分头
        （'第三部分''■与托马斯·库恩的讨论''名单3人'+编者按+访谈正文）
  页137-168: 访谈正文双页交错（每页=印刷2页并排，奇数行=左页先读，偶数行=右页后读）
剥除: 书眉'结构之后的路'(含OCR错字'结构之后的监')、页码行、'第X部分/眉名NNN'连行
用法: python _xr_96df36369f8b_road_import.py [--dry]
"""
import json, os, re, sys, shutil

BID = "96df36369f8b"
CKPT = "f:/program/Python/PhiAgent/backend/data/dp_pdf_import_ckpt.json"
KEY = "西方_托马斯_库恩_结构之后的路.pdf"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DST2 = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters/{BID}"
DETAIL_DA = f"f:/program/Python/PhiAgent/app/public/book_detail/{BID}.json"
DETAIL_DB = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

ck = json.load(open(CKPT, encoding="utf-8"))
pages = ck["ocr"][KEY]
print(f"checkpoint 页数: {len(pages)}（等 181）")
if len(pages) < 181 and "--partial" not in sys.argv:
    sys.exit("OCR 未完成，等引擎补完 181 页再跑（--partial 仅验证 0-120 部分）")
text_all = "\n".join(str(v) for v in pages.values())
print(f"OCR 文本: {len(text_all)} 字")

def lines_of(pn):
    return [l.strip() for l in str(pages[str(pn)]).split("\n") if l.strip()]

def is_bookhead(l):
    return l.startswith("结构之后")          # 书眉（含 OCR 错字 '结构之后的监'）
def is_pageno(l):
    return re.match(r"^[0-9.]{1,5}$", l)      # 页码 '192' '0' '2.58'(OCR 变体)
def is_volhead(l):
    return re.match(r"^第[一二三]+部分(?:/[^0-9]{1,14}\d{1,3})?$", l)  # '第二部分' '第一部分/重审科学革命23'
    # OCR 错字容忍: '第二部分/评论与签复207' '第二部分/评论与答复195'

def strip_header(lines):
    """剥前 3 行内的书眉/页码/部分眉（页 10 页码'0'例外特殊页处理）"""
    out = []
    for i, l in enumerate(lines):
        if i < 3 and (is_bookhead(l) or is_pageno(l) or is_volhead(l)):
            continue
        out.append(l)
    return out

# ---- 特殊页手工重组 ----
def page10_split():
    """页10: 返回 (编者导言尾行, 第一章头行) 双栏交错重组
    左栏（编者导言尾）: '第三部分：与托马斯·库恩的讨论' 起 4 行 + '整重印。' + '本书最后附上了…'
    右栏（第一章头）: '第一部分'/'■重审科学革命'/'第一章什么是科学革命'+其余（剔除左栏残留两行）"""
    L = lines_of(10)                     # 眉/页码/部分标题交错
    assert L[0].startswith("结构之后") and L[1] == "0", L[:3]
    body = L[2:]
    # 定位关键行
    i_part = next(i for i, l in enumerate(body) if l == "第一部分")
    i_third = next(i for i, l in enumerate(body) if l.startswith("第三部分：与托马斯·库恩的讨论"))
    i_ch1 = next(i for i, l in enumerate(body) if l.startswith("第一章什么是科学革命"))
    i_booklist = next(i for i, l in enumerate(body) if "本书最后附上了库恩已出版作品的完整书目" in l)
    # 左栏(编者导言尾): '第三部分：…' 起 4 行 + '整重印。'(与'奇·金迪…完'同句折行) + '本书最后附上了…'
    tail = [body[i_third], body[i_third + 1], body[i_third + 2], body[i_third + 3]]
    wanzheng = [l for l in body if l.startswith("整重印")]
    booklist = [body[i_booklist]]
    editor_tail = tail + wanzheng + booklist
    # 右栏(第一章头): '第一部分'/'■重审科学革命'/'第一章…'+其余，剔除左栏残留行（'整重印。'/'本书最后附上了…' 输出序在 '第一章…' 之后）
    rest = [l for l in body[i_ch1:] if l not in wanzheng and "本书最后附上了库恩已出版作品的完整书目" not in l]
    ch1_head = [body[i_part]] + [l for l in body if l.startswith("■重审科学革命")] + rest
    return editor_tail, ch1_head

def page121_split():
    """页121: 双页交错（印刷222=正文前半，223=标题+编者按+正文后半）
    返回 (title, note, body)：title='第十一章后记'，note=编者按，body=222正文+223正文+脚注"""
    L = lines_of(121)
    assert L[0].startswith("结构之后") and L[1] == "222", L[:3]
    body = L[3:]                       # 剥 书眉/'222'/'第二部分/评论与答复223'
    title = body[1]                    # 223页 标题行
    note = "\n".join(body[i] for i in (5, 7, 9, 11, 13, 15, 17, 19, 21))      # 223页 编者按
    y = [body[i] for i in (0, 2, 3, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 23, 25, 28, 30, 31, 34, 36, 38, 40)]
    x = [body[i] for i in (24, 26, 27, 29, 32, 33, 35, 37, 39, 41)]
    fn = body[42:]                     # 脚注 L45-51（Hempel + 感谢 + 布雷斯卫特）
    return title, note, "\n".join(y) + "\n\n" + "\n".join(x) + "\n\n" + "\n".join(fn)

def page136_split():
    """页136: 左栏=后记尾（行2,4,5,7,8,10,12,14,15,17,19,21,23），右栏=第三部分头（其余）"""
    L = lines_of(136)
    assert L[0].startswith("结构之后") and L[1] == "252", L[:3]
    body = L[2:]
    left_idx = (0, 2, 3, 5, 6, 8, 10, 12, 13, 15, 17, 19, 21)
    left = "\n".join(body[i] for i in left_idx)
    right = "\n".join(body[i] for i in range(len(body)) if i not in left_idx)
    return left, right

def is_fn_line(l):
    """脚注行识别：行首 [1] / [1〕/ [ 1 ] + 行中 'Current Books'/'Salonice'/大学 Press"""
    if re.match(r"^\[[ 1]+\]?[〕)]", l) or re.match(r"^\[ 1 \]", l):
        return True
    if "Current Books" in l or "Salonice" in l:
        return True
    if re.search(r"(Cambridge|Harvard|Oxford|Princeton|Yale|Chicago|Indiana) University Press", l):
        return True
    return False

def page_interview(pn):
    """访谈页（137-168）双页交错：奇数行=左页(先读)，偶数行=右页(后读)。
    尾段修正：左页行数<右页时右页尾行按奇偶落位错乱——
    检测 odd 流内断裂（odd[i] 行首接续字 且 odd[i-1] 句号结尾），断裂起按物理序并入 even。"""
    L = strip_header(lines_of(pn))
    fn_idx = [i for i, l in enumerate(L) if is_fn_line(l)]
    fn = [L[i] for i in fn_idx]
    body = [(i, l) for i, l in enumerate(L) if i not in fn_idx]
    odd, even = body[0::2], body[1::2]
    # 断裂检测：odd[i] 行首接续字 且 odd[i-1] 句号结尾 → 断裂，odd[i:] 与 even 后半按物理序重排
    split_at = None
    for i in range(1, len(odd)):
        if re.match(r"^[的了又在并而且但这]", odd[i][1]) and odd[i - 1][1].rstrip().endswith(("。", "！", "？")):
            split_at = i
            break
    if split_at is not None:
        # 断裂点后的 odd 尾 + 断裂点前的 even 尾 → 按物理行号排序并入 even
        tail = odd[split_at:]
        k = 0
        while k < len(even) and even[k][0] < tail[0][0]:
            k += 1
        even = even[:k] + sorted(tail + even[k:], key=lambda x: x[0])
        odd = odd[:split_at]
    odd_t = "\n".join(l for _, l in odd)
    even_t = "\n".join(l for _, l in even)
    if fn:
        even_t += "\n\n" + "\n".join(fn)
    return odd_t + "\n\n" + even_t

def page67_split():
    """页67: 返回 (第五章尾行, 第六章头行)"""
    L = lines_of(67)
    assert L[0].startswith("结构之后") and L[1] == "114", L[:3]
    body = L[2:]
    i_ch6 = next(i for i, l in enumerate(body) if l.startswith("第六章回应我的批评者"))
    # 左栏（第五章尾）: 正文行 0..i_ch6（剔除'第二部分''■评论与答复■'）
    left = [l for l in body[:i_ch6] if l != "第二部分" and not l.startswith("■评论与答复")]
    # 右栏（第六章头）: '第二部分' + '■评论与答复■' + 标题行起
    right = ["第二部分"] + [l for l in body[:i_ch6] if l.startswith("■评论与答复")] + body[i_ch6:]
    return left, right

# ---- 工具 ----
def page_text(pn):
    return "\n".join(strip_header(lines_of(pn)))

def find_title(pn, prefix):
    """页内定位标题行索引（跨章页用）——统一用剥页眉后的行序（与 page_slice 一致）"""
    for i, l in enumerate(strip_header(lines_of(pn))):
        if l.startswith(prefix):
            return i
    return -1

# 页5 前言部分：'■编者导言■' 之前
def page5_qianyan():
    L = strip_header(lines_of(5))
    i = next((i for i, l in enumerate(L) if l.startswith("■编者导言")), len(L))
    return "\n".join(L[:i])

def page_slice(pn, prefix, side):
    """跨章页按标题行切片: side='left' 标题前(归上章), side='right' 标题起(归下章)"""
    idx = find_title(pn, prefix)
    assert idx >= 0, (pn, prefix)
    L = strip_header(lines_of(pn))
    return "\n".join(L[:idx] if side == "left" else L[idx:])

chs = []
# 书名页与简介（页0-2，目录页3弃）
chs.append({"index": len(chs), "title": "书名页与简介",
            "content": [{"type": "text", "value": p} for p in
                        "\n\n".join(page_text(pn) for pn in (0, 1, 2)).split("\n\n") if p.strip()]})
# 前言（页4 + 页5前半）
chs.append({"index": len(chs), "title": "前　言",
            "content": [{"type": "text", "value": p} for p in
                        (page_text(4) + "\n\n" + page5_qianyan()).split("\n\n") if p.strip()]})
# 编者导言（页5'■编者导言■'起 + 页6-9 + 页10左栏）
L5 = strip_header(lines_of(5))
i_ed = next(i for i, l in enumerate(L5) if l.startswith("■编者导言"))
editor_body = ["\n".join(L5[i_ed:])]
for pn in (6, 7, 8, 9):
    editor_body.append(page_text(pn))
editor_body.append("\n".join(page10_split()[0]))
chs.append({"index": len(chs), "title": "编者导言",
            "content": [{"type": "text", "value": p} for p in "\n\n".join(editor_body).split("\n\n") if p.strip()]})
# 第一章起（页10右栏 + 页11-20）
ch1_body = ["\n".join(page10_split()[1])]
for pn in range(11, 21):
    ch1_body.append(page_text(pn))
chs.append({"index": len(chs), "title": "第一章 什么是科学革命",
            "content": [{"type": "text", "value": p} for p in "\n\n".join(ch1_body).split("\n\n") if p.strip()]})

def plain(title, p0, p1):
    """整页章：页p0-p1"""
    body = [page_text(pn) for pn in range(p0, p1 + 1)]
    chs.append({"index": len(chs), "title": title,
                "content": [{"type": "text", "value": p} for p in "\n\n".join(body).split("\n\n") if p.strip()]})

def mixed(title, slices):
    """切片章: slices = [(start, end, page_text_fn)…]"""
    body = []
    for s in slices:
        if len(s) == 3:
            p0, p1, fn = s
        else:
            p0, p1, fn = s[0], s[1], page_text
        for pn in range(p0, p1 + 1):
            body.append(fn(pn))
    chs.append({"index": len(chs), "title": title,
                "content": [{"type": "text", "value": p} for p in "\n\n".join(body).split("\n\n") if p.strip()]})

plain("第二章 可通约性、可比较性、可交流性", 21, 34)
plain("第三章 科学史中的可能世界", 35, 50)
plain("第四章 《结构》之后的路", 51, 58)
plain("第五章 历史的科学哲学之困扰", 59, 66)
# 第六章（页67右栏 + 68-95）
mixed("第六章 回应我的批评者", [(67, 67, lambda pn: "\n".join(page67_split()[1])), (68, 95)])
# 第七章（页96标题起 + 97-105 + 106左栏；页96 标题第二行'形式主义的评论'独立行剥除）
def p96_ch7(pn):
    t = page_slice(96, "第七章作为结构变化的理论变化", "right")
    return "\n".join(l for l in t.split("\n") if l != "形式主义的评论")
mixed("第七章 作为结构变化的理论变化：对斯尼德形式主义的评论",
      [(96, 96, lambda pn: p96_ch7(96)), (97, 105),
       (106, 106, lambda pn: page_slice(106, "第八章科学中的隐喻", "left"))])
# 第八章（106右栏 + 107-111 + 112左栏）
mixed("第八章 科学中的隐喻",
      [(106, 106, lambda pn: page_slice(106, "第八章科学中的隐喻", "right")),
       (107, 111),
       (112, 112, lambda pn: page_slice(112, "第九章合理性与理论选择", "left"))])
# 第九章（112右栏 + 113-116 + 117左栏）
mixed("第九章 合理性与理论选择",
      [(112, 112, lambda pn: page_slice(112, "第九章合理性与理论选择", "right")),
       (113, 116),
       (117, 117, lambda pn: page_slice(117, "第十章自然科学与人文科学", "left"))])
# 第十章（117右栏 + 118-120）
mixed("第十章 自然科学与人文科学",
      [(117, 117, lambda pn: page_slice(117, "第十章自然科学与人文科学", "right")),
       (118, 120)])
# 第十一章 后记（页121 特殊 + 122-135 整页 + 136 左栏）
t_ch11, note_ch11, body121 = page121_split()
ch11_body = [note_ch11, body121]
for pn in range(122, 136):
    ch11_body.append(page_text(pn))
ch11_body.append(page136_split()[0])
chs.append({"index": len(chs), "title": "第十一章 后记",
            "content": [{"type": "text", "value": p} for p in "\n\n".join(ch11_body).split("\n\n") if p.strip()]})
# 第三部分 与托马斯·库恩的讨论（136 右栏 + 137-168 访谈页）
ch12_body = [page136_split()[1]]
for pn in range(137, 169):
    ch12_body.append(page_interview(pn))
chs.append({"index": len(chs), "title": "第三部分 与托马斯·库恩的讨论",
            "content": [{"type": "text", "value": p} for p in "\n\n".join(ch12_body).split("\n\n") if p.strip()]})

TITLES = [c["title"] for c in chs]

# ---- 验证 ----
tot = 0
for c in chs:
    n = sum(len(b["value"]) for b in c["content"])
    tot += n
    first = c["content"][0]["value"][:26] if c["content"] else "(空)"
    print(f"[{c['index']}] {c['title'][:22]:<24s} {n:7d}字 {len(c['content']):3d}段  首: {first!r}")
print(f"已建 {len(chs)} 章 {tot} 字（原文 {len(text_all)} 字，保留 {tot/len(text_all):.0%}）")
empty = [c["index"] for c in chs if not c["content"]]
print("空章:", empty if empty else "无")

if "--dry" in sys.argv or "--partial" in sys.argv:
    sys.exit(0)

# ---- 写入三处 ----
if os.path.isdir(SRC):
    suf = "_old_bad"
    i2 = 2
    while os.path.isdir(SRC + suf):
        suf = f"_old_bad{i2}"
        i2 += 1
    os.rename(SRC, SRC + suf)
    print(f"\n备份旧数据 → {os.path.basename(SRC) + suf}")
os.makedirs(SRC)
for c in chs:
    json.dump({"index": c["index"], "title": c["title"], "content": c["content"]},
              open(os.path.join(SRC, f"{c['index']}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
meta = {"bookId": BID, "title": "结构之后的路", "author": "托马斯·库恩",
        "toc": [{"type": "chapter", "title": t, "index": i} for i, t in enumerate(TITLES)],
        "cover": None, "chapterCount": len(chs), "chapterTitles": TITLES}
json.dump(meta, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print(f"✓ 写入 {SRC}: {len(chs)} 章")
shutil.rmtree(DST, ignore_errors=True); shutil.copytree(SRC, DST)
shutil.rmtree(DST2, ignore_errors=True); shutil.copytree(SRC, DST2)
print("✓ 同步 DST/DST2")

# ---- detail 双端（保留原 summary/tags/cover） ----
for p in (DETAIL_DA, DETAIL_DB):
    d = json.load(open(p, encoding="utf-8"))
    d["author"] = "托马斯·库恩"
    d["toc"] = meta["toc"]
    d["chapterCount"] = len(chs)
    d["chapterTitles"] = TITLES
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
    print(f"✓ detail: {p.split('/')[-2]}")

# ---- books.json（cc） ----
books = json.load(open(BOOKS, encoding="utf-8"))
for x in books:
    if str(x.get("id")) == BID:
        old = x["chapterCount"]
        x["chapterCount"] = len(chs)
        x["author"] = "托马斯·库恩"
        print(f"✓ books.json {BID} cc {old}→{len(chs)}")
json.dump(books, open(BOOKS, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
print("✓ books.json 写入完成")
