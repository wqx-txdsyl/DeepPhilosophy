# -*- coding: utf-8 -*-
"""
dp_clean_book.py — 单本专项清洗（2026-08-07, 样例书: 纯粹现象学通论）
针对扫描书 OCR 输出的三类顽疾（页眉页脚混入 / 正文分割混乱 / 目录混乱）的增强清洗。

用法: python dp_clean_book.py <safe_key>
  safe_key: dp_pdf_import_ckpt.json 中 ocr 段的键, 如 西方_埃德蒙德_胡塞尔_纯粹现象学通论.pdf
输出 (backend/data/cleaned_pages/):
  {书名}_v4.json         {页索引: 干净页文本}
  {书名}_toc.json        目录页解析的结构化目录 [{level, num, title, page}]
  {书名}_chapters.json   正文编章切分 [{type, title, start_page, end_page, page_count}]

核心改进（相对 dp_pdf_import.py 内联清洗）:
  1. 页眉统计按【奇/偶页分组】——中文书版式: 左页页眉=书名, 右页页眉=章/编名。
     全局频率阈值(旧: >10%)抓不住低频章名页眉, 分组后"某文本在同奇偶性≥3页页首出现"即页眉。
  2. 页眉行判定覆盖页首 3 行 / 页尾 2 行（旧: 仅首行）, 并过滤纯数字页码。
  3. 目录区（"目录"起始块）整体识别, 不参与页眉统计与正文切分, 单独结构化解析。
  4. 正文编/章嵌套切分（旧: 仅章级平铺且编名页眉每2页出现→切碎）;
     编名页眉按频次滤除后再判标题行, 章名跨行合并。
  5. § 误识别修复: $3/S8/830/873/878 → §3/§8/§30/§73/§78（目录与正文节标题行）。
"""
import sys, io, os, json, re

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS_DIR = r"F:\philosophy"
CKPT = os.path.join(BASE_DIR, "data", "dp_pdf_import_ckpt.json")
OUT_DIR = os.path.join(BASE_DIR, "data", "cleaned_pages")
os.makedirs(OUT_DIR, exist_ok=True)

_positional = [a for a in sys.argv[1:] if not a.startswith("--")]
SAFE = _positional[0] if _positional else "西方_埃德蒙德_胡塞尔_纯粹现象学通论.pdf"
CJK = "一-鿿"
# ── 行分类正则 ──
RE_PART = re.compile(r"^第([一二三四五六七八九十百\d]+)编[、·．.,，]?\s*(.{0,24})")      # 编标题
RE_CHAP = re.compile(r"^第([一二三四五六七八九十百\d]+)[章卷篇部][、·．.,，]?\s*(.{0,24})")  # 章/卷/篇/部标题
RE_CHAP_NUM = re.compile(r"^(\d{1,2})(?:[ \t]*[|｜]?[ \t]*)(?=[一-鿿])")        # 数字式章标题(text-layer: "1 | 导论"/"4 权力意志")
RE_CN_CHAP = re.compile(r"^([一二三四五六七八九十]{1,2})$")                      # 汉字数字独立行章标题(罪与罚式: 页首"一"~"八", 每部从"一"重计; 3字"一二三"目录行排除)
CN_CHARS = "一二三四五六七八九十"
CN_NUM = {c: i for i, c in enumerate(CN_CHARS, 1)}

def _cn_to_int(s):
    """汉字数字转整数: 一=1 十=10 十一=11 二十=20 二十一=21"""
    if len(s) == 1:
        return CN_NUM[s]
    if s == "十":
        return 10
    if s.startswith("十"):
        return 10 + CN_NUM[s[1]]
    if s.endswith("十"):
        return CN_NUM[s[0]] * 10
    return CN_NUM[s[0]] * 10 + CN_NUM[s[1]]
RE_VOLUME = re.compile(r"^卷[（(][^）)）]{0,2}[）)]?\s*([一二三四五六七八九十百\d])?(.{0,20})")  # 卷（A）一式（政治学: 希腊字母卷号）
RE_CHAP_NESTED = re.compile(r"^第[一二三四五六七八九十百\d]+[章卷篇部]")                   # 编标题后跟章(术语对照区条目)
RE_FRONT = re.compile(r"^(中译者序|第五版编辑前言|编者导言|出版说明|译者前言|导论|导言|引论|代序|序[言文]?|前言|后记|跋|题记)$")
RE_SEC = re.compile(r"^(\d{1,3})(?:[、．.][\s　]*)?(?=[%s])" % CJK)                    # 节标题: 数字(+分隔符)+中文(1自然认识/1. 关于…)
RE_SEC_S = re.compile(r"^[§S$8。]{1}\s*(\d{1,3})\s*$")                                    # §误识别独立行: $3 / S8 / 830
RE_SEC_S2 = re.compile(r"^[§S$8]{1}\s*(\d{1,3})\s*([%s].*)$" % CJK)                       # §误识别+标题同行: 830自然态度的总设定
RE_PAGENUM = re.compile(r"^\d{1,4}$")                                                     # 孤立页码
RE_GLUE_PAGE = re.compile(r"^(\d{2,4})([%sA-Za-z].*)$" % CJK)                             # 粘连页码: 128导论(数字≥100)
DOTTAIL = re.compile(r"[·…~\.\s]+$")                                                      # 目录点线（含 ASCII 点: 西塞罗目录用"...."）
RE_APPENDIX = re.compile(r"^附录[:：]?")
SENT_END = "。！？；：”』」）】…—-"
# 节题正文特征词: 讲义编号段（"1. 古代诠释学首先被用来…"/"19世纪…"）→ 非节题
SEC_BAD = ("首先", "但是", "可是", "不过", "由于", "随着", "总之", "然而", "尽管", "如果",
           "因为", "所以", "而且", "这种", "这样", "这些", "所谓", "可以说",
           "被用来", "用来", "意思是", "也就是说", "那就是", "事实上", "实际上", "当然",
           "在于", "世纪", "年代", "时期")


def norm_header(s):
    """页眉归一化: 编/章号后的顿号逗号变体（'第四编、理性和现实'→'第四编理性和现实'）+ 尾部标点"""
    s = re.sub(r"^(第[一二三四五六七八九十百\d]+[编章节卷部])[、·．.,，]", r"\1", s)
    return s.rstrip("？?，,、·．.：:；;")


def load_pages():
    ckpt = json.load(open(CKPT, encoding="utf-8"))
    ocr = ckpt.get("ocr", {}).get(SAFE)
    if not ocr:
        raise SystemExit(f"ckpt 中无 ocr[{SAFE}], 可用: {list(ckpt.get('ocr', {}).keys())}")
    pages = []
    maxp = max(int(k) for k in ocr if str(k).isdigit())
    for i in range(maxp + 1):
        pages.append(ocr.get(str(i), "") or "")
    return pages


def strip_header_footer(pages, rel=None):
    """奇偶分组统计页首3行/页尾2行高频行 → 页眉页脚; 返回清洗后页列表 + 页眉集合 + 前置类页眉首次页"""
    from collections import Counter
    head_first = {0: Counter(), 1: Counter()}
    tail_last = {0: Counter(), 1: Counter()}

    def line_feats(s):
        # 破折号结尾不排除（页眉"附录二：…特征—"以破折号收尾）; 其他句末标点排除
        # 单字纯汉字排除: 罪与罚式章标题"一"~"八"每部循环出现, 同奇偶≥2 会被误判页眉而剥离
        if not s or RE_PAGENUM.match(s) or len(s) > 25 or (s[-1] in SENT_END and s[-1] != "—"):
            return None
        if re.fullmatch(r"[一-鿿]", s):
            return None
        # 行尾页码剥离（页眉"第一部分… 15"每页页码不同 → 变体不进 headers → 不剥离）:
        # 归一化后同一页眉累计, 根治页眉页码变体漏剥离
        return re.sub(r"\s*\d{1,4}$", "", s) or None

    for i, t in enumerate(pages):
        lines = [l.strip() for l in t.split("\n") if l.strip()]
        if not lines:
            continue
        parity = i % 2
        for l in lines[:3]:
            f = line_feats(l)
            if f:
                head_first[parity][f] += 1
        for l in lines[-2:]:
            f = line_feats(l)
            if f:
                tail_last[parity][f] += 1

    headers = {l for p in (0, 1) for l, c in head_first[p].items() if c >= 2}
    footers = {l for p in (0, 1) for l, c in tail_last[p].items() if c >= 2}
    # 排除纯编号截断变体（"第四编"→ 已有完整版"第四编理性和现实"）, 避免垃圾段
    headers = {h for h in headers
               if not (re.match(r"^第[一二三四五六七八九十百\d]+编$", h)
                       and any(x.startswith(h) and x != h for x in headers))}
    pagenums = set()
    for t in pages:
        lines = [l.strip() for l in t.split("\n") if l.strip()]
        for l in lines[-2:]:
            if RE_PAGENUM.match(l):
                pagenums.add(l)

    # 真标题页判定: header 存在"去标点变体行"（如"编者导言?"→"编者导言"）时用变体页,
    # 否则用首次出现页; 书名页眉（出现最多的 header）不保留（封面自带书名行）
    freq = {h: sum(c for p in (0, 1) for c in [head_first[p][h]]) for h in headers}
    book_title = max(headers, key=lambda x: freq[x]) if headers else None
    # 书名页眉 OCR 变体排除（"康德《实践理性批判》句读"的 }> ) 混识别变体）:
    # 与 rel 文件名（书名）模糊匹配的页眉只用于剥离, 不触发前置/附录判定（页53 误判附录吞 600 页根因）
    book_keys = set()
    if rel:
        bn = re.sub(r"[^一-鿿A-Za-z0-9]", "", os.path.splitext(os.path.basename(rel))[0])
        if len(bn) >= 4:
            import difflib
            for h in headers:
                hn = re.sub(r"[^一-鿿A-Za-z0-9]", "", h)
                # 包含或相似（OCR 错字变体: "纯粹现象学通论"→"纯梓现象学通论"）→ 书名页眉
                if hn and (bn in hn or hn in bn
                           or difflib.SequenceMatcher(None, bn, hn).ratio() >= 0.6):
                    book_keys.add(h)
    keep_pages = {}
    for h in sorted(headers, key=lambda x: freq[x]):
        if h == book_title or h in book_keys:
            continue  # 书名页眉全删（封面/扉页自带书名行, 不依赖页眉保留）
        var = None
        # text-layer 数字式章标题两行式（"1 "+"导论"）优先: 页眉兼章标题（尼采"导论"）首现页在第二行,
        # 按 first[0] 找会落到页眉页（18）→ RE_FRONT/附录 误判 → 与"第1章"重复段
        for i, t in enumerate(pages):
            first = [l.strip() for l in t.split("\n") if l.strip()]
            if len(first) >= 2 and re.fullmatch(r"\d{1,2}", first[0]) and first[1] == h:
                var = i
                break
        if var is None:
            for i, t in enumerate(pages):
                first = [l.strip() for l in t.split("\n") if l.strip()]
                if not first:
                    continue
                s = norm_header(first[0])
                if s == h and first[0].strip() != h:
                    var = i
                    break
        if var is None:
            for i, t in enumerate(pages):
                first = [l.strip() for l in t.split("\n") if l.strip()]
                if first and first[0] == h:
                    var = i
                    break
        if var is not None:
            keep_pages[h] = var

    clean = []
    for i, t in enumerate(pages):
        lines = [l.rstrip() for l in t.split("\n")]
        start = 0
        while start < len(lines):
            s = lines[start].strip()
            s_norm = re.sub(r"\s*\d{1,4}$", "", norm_header(s))
            if s_norm in headers and keep_pages.get(s_norm) != i:
                start += 1
            # 行首页码剥离仅限 ≥10: 一位数可能是 text-layer 数字式章标题（尼采"1 "+"导论"两行式）
            elif RE_PAGENUM.match(s) and int(s) >= 10:
                start += 1
            else:
                break
        end = len(lines)
        while end > start:
            s = lines[end - 1].strip()
            s_norm = re.sub(r"\s*\d{1,4}$", "", norm_header(s))
            if (s_norm in headers or s_norm in footers or s in pagenums) and keep_pages.get(s_norm) != i:
                end -= 1
            else:
                break
        clean.append("\n".join(lines[start:end]).strip())
    return clean, headers, keep_pages


def merge_tate_page(t):
    """竖排拆行页行合并: 文本层把竖排书每字拆成一行（"第\\n一\\n卷"）→ 连续短行合并
    判定: 非空行 ≥10 且行长中位数 ≤2（竖排拆行页一半以上行 ≤2 字; 横排正文页中位 15+）"""
    lines = [l.strip() for l in t.split("\n")]
    nonempty = [l for l in lines if l]
    if len(nonempty) < 10:
        return t
    ls = sorted(len(l) for l in nonempty)
    if ls[len(nonempty) // 2] > 2:
        return t
    out = []
    for l in nonempty:
        if out and len(out[-1]) <= 2 and len(l) <= 2:
            out[-1] += l
        else:
            out.append(l)
    return "\n".join(out)


def find_toc_span(pages):
    # 目录标题可能带空格（"目 录"/"目 次"）; 结束页判定行归一化后再匹配（"导 言"→导言）
    start = None
    for i, t in enumerate(pages):
        first = [l.strip() for l in t.split("\n") if l.strip()]
        if first and re.sub(r"\s+", "", first[0]) == "目录":
            start = i
            break
    if start is None:
        return None, None
    end = start + 1
    for i in range(start + 1, min(start + 40, len(pages))):
        first = [l.strip() for l in pages[i].split("\n") if l.strip()]
        if not first or re.sub(r"\s+", "", first[0]) == "目录":
            continue
        s = re.sub(r"\s+", "", first[0])
        if RE_FRONT.match(s) or RE_PART.match(s) or RE_CHAP.match(s):
            end = i
            break
    return start, end


def parse_toc(pages, start, end):
    entries = []
    for i in range(start, end):
        for l in pages[i].split("\n"):
            s = DOTTAIL.sub("", l.strip())
            if not s or s == "目录":
                continue
            page = None
            m = RE_GLUE_PAGE.match(s)
            if m and int(m.group(1)) > 100:
                page, s = int(m.group(1)), m.group(2)
            else:
                m = re.search(r"(\d{1,4})\s*$", s)
                if m:
                    page, s = int(m.group(1)), s[: m.start()].rstrip("·…~-")
            if not s:
                continue
            # 单字符节号 + 页码: '$' p3 → §3（OCR 把 § 拆行: "$" + 点线 + "3"）
            if re.match(r"^[§S$8]{1}$", s) and page is not None:
                entries.append({"level": "节", "num": "§" + str(page), "title": None, "page": None})
                continue
            m = RE_SEC_S.match(s)
            if m:
                entries.append({"level": "节", "num": "§" + m.group(1), "title": None, "page": page})
                continue
            m = RE_SEC_S2.match(s)
            if m:
                entries.append({"level": "节", "num": "§" + m.group(1), "title": m.group(2), "page": page})
                continue
            m = RE_PART.match(s)
            if m and len(s) <= 30:
                entries.append({"level": "编", "num": "第" + m.group(1) + "编", "title": m.group(2) or s, "page": page})
                continue
            m = RE_CHAP.match(s)
            if m and len(s) <= 30:
                entries.append({"level": "章", "num": "第" + m.group(1) + "章", "title": m.group(2) or s, "page": page})
                continue
            m = RE_SEC.match(s)
            if m:
                entries.append({"level": "节", "num": m.group(1), "title": s[m.end():] or None, "page": page})
                continue
            if entries and entries[-1]["level"] == "节" and entries[-1]["title"] is None:
                entries[-1]["title"] = s
            else:
                entries.append({"level": "前置", "num": None, "title": s, "page": page})
    return entries


def _clean_title(s):
    """章标题净化: 去尾部页码/注释符号（'方法的预备考察28'→'方法的预备考察'）"""
    return re.sub(r"[°·…～。\s\d”\"']+$", "", s)


def _join_title(first, next_line):
    """章名跨行合并: 首行短且行尾无句末标点 → 拼下一行(去尾部数字/符号)
    下一行若是节标题行(数字开头/§行)则不合并"""
    if not first or len(first) > 25 or first[-1] in SENT_END:
        return first
    if not next_line or len(next_line) > 40 or next_line[-1] in SENT_END:
        return first
    if re.match(r"^[\d§S$8]", next_line):
        return first
    merged = first + next_line
    # 拼合后仍是标题（≤15 字）才算跨行章名; 超过 = 下一行是正文首行（西塞罗"古老的家族"+正文行）
    if len(merged) > 15:
        return first
    return re.sub(r"[·…~\s\d]+$", "", merged)


def _num_title(s):
    """text-layer 数字式章标题剩余段: '4 权力意志'→'权力意志', 无中文/'18世纪…'/尾标点→None"""
    m = RE_CHAP_NUM.match(s)
    if not m:
        return None
    h = s[m.end():].strip()
    cjk = re.sub(r"[^一-鿿]", "", h)
    if 2 <= len(cjk) <= 10 and h == cjk and not any(w in h for w in SEC_BAD):
        return h
    return None


def chapterize(pages, toc_end, headers, front_first, toc=None):
    """编/章/前置/附录 嵌套切分。段结构: 顶层 = 前置|编|附录; 章作为编的子项"""
    sections = []   # 顶层段
    cur = None      # 当前段 {type,title,start,end,chapters?}
    appendix_done = False  # 附录区正文句子以"第X章"开头（法译本注释等）, 不再扫章
    # 章级标题预扫描（toc_end 之后, 排除页眉行）: RE_CHAP("第X章…") 或数字式
    # （"4 权力意志"单行 / "1"+"导论"两行式, text-layer 书）命中 ≥3 → 章书 → 关 RE_SEC
    # （防讲义编号段误切: b43aeb7ccc57"1. 古代诠释学首先…"）;
    # 否则节书 → RE_SEC 开（哲学谈话录 95 章节式结构; 尼采无 RE_CHAP 标题但数字式命中 → 章书）
    # 页眉必须排除: 哲学谈话录页眉"第一卷"309 次/图斯库兰页眉"第一章 论鄙视死亡"每页重复;
    #   front_first 只认页首行（尼采"导论"章标题在页 17 是第二行）→ 全局首次出现页 first_any
    first_any = {}
    if headers:
        for _i in range(toc_end, len(pages)):
            for _l in set(pages[_i].split("\n")):
                _ls = _l.strip()
                if _ls in headers and _ls not in first_any:
                    first_any[_ls] = _i
    chap_hits = num_hits = cn_hits = 0
    cn_one = 0  # "一"独立行章标题数（每部第一章, 用于"尾声"部命名）
    has_yws = False  # 目录区含"尾声"独立行（罪与罚: 最后一部是尾声; toc_end=0 时全书扫, 正文句内"尾声"不含独立行）
    for _i in range(len(pages)):
        for _l in pages[_i].split("\n"):
            if _l.strip() == "尾声":
                has_yws = True
                break
        if has_yws:
            break
    for i in range(toc_end, len(pages)):
        fl = [l.strip() for l in pages[i].split("\n") if l.strip()]
        if not fl:
            continue
        s0 = fl[0]
        if s0 in headers and i != first_any.get(s0):
            continue
        # RE_CHAP（"第X章"）放宽到 ≤26: 长章标题（b43"第一章 是从精神科学自身那种受方法论歪曲了的自我理解出"26 字）;
        # 数字式保持 ≤14（正文"18 世纪…"长行排除）
        if len(s0) <= 26:
            # 只认"第X章"（"第X卷"不算: 哲学谈话录 4 卷卷标题页会误判章书 → 崩 95→1）
            if re.match(r"^第[一二三四五六七八九十百\d]+章", s0):
                chap_hits += 1
            elif len(s0) <= 14 and _num_title(s0):
                num_hits += 1
        # 汉字数字独立行（罪与罚式: 页首"一"~"八", 每部从"一"重计; "一"触发新部）
        if len(s0) <= 3 and RE_CN_CHAP.match(s0):
            cn_hits += 1
            if s0 == "一":
                cn_one += 1
        # 两行式: 第二行是页眉时仅首次出现页计入（页眉兼章标题, 如尼采"导论"）
        if len(fl) >= 2 and re.fullmatch(r"\d{1,2}", s0) and \
                not (fl[1] in headers and i != first_any.get(fl[1])):
            if _num_title(s0 + " " + fl[1]):
                num_hits += 1
    has_chap = (chap_hits + num_hits + cn_hits) >= 3
    import os as _os2
    if _os2.environ.get("DBG_CHAP"):
        print(f"DBG_CHAP: has_chap={has_chap} chap_hits={chap_hits} num_hits={num_hits} cn_hits={cn_hits} cn_one={cn_one} has_yws={has_yws} toc_end={toc_end} n_pages={len(pages)}", flush=True)
    part_no = 0   # 汉字数字章标题的部号（罪与罚: 每出现"一"开新部）
    chn = 1       # 当前部内章号
    for i in range(toc_end, len(pages)):
        t = pages[i]
        first = [l.strip() for l in t.split("\n") if l.strip()]
        if not first:
            if cur:
                cur["end"] = i
            continue
        # 整页短行目录页（无"目录"标题书的目录, 如罪与罚"八 尾声 一"）: 跳过, 不切章
        # 正文页必含 ≥1 个长行（句子）, 短行页只可能是目录/扉页;
        # 仅 toc_end==0 启用（正常书目录已被 toc_end 隔离, 禁用防误跳章标题页）
        if toc_end == 0 and len(first) <= 4 and max(len(l) for l in first) <= 8:
            continue
        s = first[0]
        is_header = s in headers and not (i == front_first.get(s))
        m = RE_GLUE_PAGE.match(s)
        if m and int(m.group(1)) > 100:
            s = m.group(2)
        if not is_header and len(s) <= 30:
            m = RE_PART.match(s)
            if m and (m.group(2) or "").strip() and not RE_CHAP_NESTED.match(m.group(2) or ""):
                title = re.sub(r"[？?，,、·．\s]+$", "", (m.group(2) or "").strip())
                title = "第%s编 %s" % (m.group(1), title)
                # 前缀扩展: 前一编段是截断标题(如"关于纯粹现象学的") → 吸收, 不切新段
                if cur and cur["type"] == "编" and cur["title"].split(" ", 1)[-1] and \
                   title.split(" ", 1)[-1].startswith(cur["title"].split(" ", 1)[-1]) and cur["start"] != i:
                    cur["title"] = title
                    cur["end"] = i
                else:
                    if cur:
                        sections.append(cur)
                    cur = {"type": "编", "title": title, "start": i, "end": i, "chapters": []}
                # 不 continue: 编首页同页常印第一章标题（页80/127/211/383）, 需继续章扫描
            else:
                m = RE_FRONT.match(norm_header(s))
                if m:
                    if cur:
                        sections.append(cur)
                    cur = {"type": "前置", "title": norm_header(s), "start": i, "end": i}
                    continue
                # 附录段: 附录区页眉标题（主题索引/人名索引/法译本注释…）的首次出现页（须在目录区后）
                # 排除装饰/符号页眉（"• • •"、"一一"等装饰线 → 触发附录吞正文）:
                #   须含 ≥2 个汉字, 且非单字重复（"一一"→ 去非汉字后 single-char 重复）
                cjk = re.sub(r"[^一-鿿]", "", s)
                is_deco = (len(cjk) < 2 or re.fullmatch(r"(.)\1{1,4}", cjk))
                # 附录段仅限附录类标题（"宗教"等页眉兼章标题会误判附录吞全书 → 排除）:
                # 附录/索引/注释/参考/术语/书目/年表 类页眉
                if (i > toc_end and s in headers and i == front_first.get(s) and not is_deco
                        and any(w in s for w in ("附录", "索引", "注释", "参考", "术语", "书目", "年表"))):
                    if cur:
                        sections.append(cur)
                    cur = {"type": "附录", "title": s, "start": i, "end": i}
                    appendix_done = True
                    continue
        # 章标题: 整页扫描（章首页排版不固定, 标题可能在页中部行, 如页109行16）; 附录区跳过
        if not appendix_done:
            for j, s in enumerate(first):
                if s in headers and not (i == front_first.get(s)):
                    continue
                m = RE_CHAP.match(s)
                # 标题内容排除: group2 含句号（正文句）或"？"不在末尾（"分？是"式断词）→ 非章标题
                g2 = (m.group(2) or "").strip() if m else ""
                # "第一部分艺术经验…" → 组1="一" 部 组2="分艺术经验…" 的"分"残字（"部分"的多余字）
                if g2.startswith("分"):
                    g2 = g2[1:].strip()
                if m and g2 and len(s) <= 30 and not ("。" in g2 or ("？" in g2 and not g2.endswith("？"))):
                    title = "第%s章 %s" % (m.group(1),
                        _clean_title(_join_title(g2, first[j + 1] if j + 1 < len(first) else None)))
                    ch = {"type": "章", "title": title, "start": i, "end": i}
                else:
                    # text-layer 数字式章标题: 单行式("4 权力意志")/两行式(页首"1 "独立行+次行"导论")
                    # 排除正文编号段（"18世纪…"/"8 种可能的系列："尾标点/SEC_BAD）
                    nt = None
                    if not m and j == 0 and len(s) <= 14:
                        if len(first) >= 2 and re.fullmatch(r"\d{1,2}", s) and \
                                not (first[1] in headers and i != first_any.get(first[1])):
                            nt = _num_title(s + " " + first[1])
                        else:
                            nt = _num_title(s)
                    if nt:
                        ch = {"type": "章", "title": "第%s章 %s" % (s.split()[0], _clean_title(nt)),
                              "start": i, "end": i}
                    else:
                        # 汉字数字独立行章标题（罪与罚式: 页首"一"~"八", 每部从"一"重计）
                        # 命名: 首行"一"→ 开新部; 目录区含"尾声" → 最后一部命名"尾声 第X章"
                        m_cn = None
                        if not m and j == 0 and len(s) <= 3 and \
                                not (s in headers and i != first_any.get(s)):
                            m_cn = RE_CN_CHAP.match(s)
                        if m_cn:
                            cn_val = _cn_to_int(m_cn.group(1))
                            if cn_val == 1:
                                part_no += 1
                                chn = 1
                            else:
                                chn = cn_val
                            # part_no==0 说明首个命中不是"一"（如目录页"八"）→ 无部前缀;
                            # >10 用阿拉伯数字（CN_CHARS 仅到"十"）
                            if part_no == 0:
                                title = "第%s章" % (CN_CHARS[chn - 1] if chn <= 10 else str(chn))
                            elif has_yws and part_no == cn_one:
                                title = "尾声 第%s章" % (CN_CHARS[chn - 1] if chn <= 10 else str(chn))
                            else:
                                title = "第%s部 第%s章" % (
                                    CN_CHARS[part_no - 1] if part_no <= 10 else str(part_no),
                                    CN_CHARS[chn - 1] if chn <= 10 else str(chn))
                            ch = {"type": "章", "title": title, "start": i, "end": i}
                        elif not m or not g2:
                            mv = RE_VOLUME.match(s)
                            # 注意: RE_CHAP 命中但标题不合格（len>30/含句号, 如"第36卷，第848页…"引文）
                            # → 不进本分支也不进 nt → 必须 continue, 否则带着旧 ch fall-through 重复 append
                            # 卷标题"卷（A）"以括号结尾（SENT_END 含"）"会误杀）, 仅限短行;
                            # 卷 = 编级分组（part）—— 像现象学的"第X编"
                            if mv and len(s) <= 20:
                                if cur:
                                    sections.append(cur)
                                cur = {"type": "编", "title": _clean_title(s), "start": i, "end": i, "chapters": []}
                                break
                            else:
                                # 节级标题切块（仅非章书: 哲学谈话录"1. 关于我们能控制的和不能控制的事物"）;
                                # 章书（图斯库兰/尼采/真理与方法解读）的正文编号段会被 RE_SEC 误切
                                # 排除含句号的行（正文/译者注行"1. 人的主导原则…。这是…"）; 允许行尾"？"（疑问式节题）
                                # 正文编号段排除: "190 页即…"（页码引用）/ "120 一123）…"（页码区间 OCR 变体）/
                                #   "19世纪…"（年代）/ "年左右…"（"第160节 年左右所写的《农书》"——图斯库兰页码注）/
                                #   正文连接词（"1. 古代诠释学首先被用来…"→ 讲义正文段）
                                if not has_chap:
                                    ms = RE_SEC.match(s)
                                    if ms and len(s) <= 40 and "。" not in s:
                                        sec_head = s[ms.end():].lstrip()
                                        if (sec_head.startswith("页") or sec_head.startswith("年")
                                                or re.match(r"^[一\-～]\d", sec_head)
                                                or any(w in sec_head for w in SEC_BAD)):
                                            continue
                                        ch = {"type": "章", "title": "第%s节 %s" % (ms.group(1),
                                            _clean_title(s[ms.end():].strip())[:24]), "start": i, "end": i}
                                    else:
                                        continue
                                else:
                                    continue
                        else:
                            # RE_CHAP 命中但标题不合格（len>30/含句号, 如"第36卷，第848页…"引文）:
                            # 非标题行, 跳过（防 fall-through 带旧 ch 重复 append）
                            continue
                # 章/节眉重复（同标题 ≤30 页内再命中, 如节眉残留"9. 论变得无耻之徒"）→ 并入上一块
                # 标题归一化比较（全/半角标点变体: "…?" vs "…？"）
                prev_ch = (cur["chapters"][-1] if (cur and cur["type"] == "编" and cur.get("chapters"))
                           else (sections[-1] if sections and sections[-1]["type"] == "章" else None))
                # OCR 错字变体（"冲突"→"冲灾"）: 前 8 字符前缀匹配或短串是长串前缀（"第四编"⊂"第四编理性和现实"）
                norm_t = lambda t: re.sub(r"[？?，,。．.\s:：、；（）()—~]+", "", t or "")
                np_, nch = norm_t(prev_ch["title"]) if prev_ch else "", norm_t(ch["title"])
                same_t = (len(np_) >= 8 and len(nch) >= 8 and np_[:8] == nch[:8]) or \
                         (min(len(np_), len(nch)) > 0 and (nch.startswith(np_) or np_.startswith(nch)))
                if prev_ch and same_t and i - prev_ch["start"] <= 30:
                    prev_ch["end"] = i
                    break
                if cur and cur["type"] == "编":
                    cur["chapters"].append(ch)
                    cur["end"] = i
                else:
                    # 平铺章块 end 只在底部 elif 延续, 新章首页须先把旧章 end 关到 i-1
                    if sections and sections[-1]["type"] == "章":
                        sections[-1]["end"] = i - 1
                    if cur:
                        sections.append(cur)
                    sections.append(ch)
                    cur = None
                break
        if cur:
            cur["end"] = i
        elif sections and sections[-1]["type"] == "章":
            sections[-1]["end"] = i  # 平铺章块: 普通页延续到当前页
    if cur:
        sections.append(cur)
    if not sections:
        # 兜底段不预带 subs——merged(354) 会 setdefault+insert 唯一 sub, 预带会导致 2 个同页 subs → 重复块
        sections = [{"type": "前置", "title": "正文", "start": toc_end, "end": len(pages) - 1}]

    merged = []
    for c in sections:
        c["page_count"] = c["end"] - c["start"] + 1
        if c["type"] == "章":
            merged.append(c)
            continue
        if merged and merged[-1]["type"] == c["type"]:
            # 标点变体归一化（"附录二："vs"附录二；"）比较
            norm_t = re.sub(r"[？?，,。．.\s:：、；（）()—~]+", "", merged[-1]["title"])
            norm_c = re.sub(r"[？?，,。．.\s:：、；（）()—~]+", "", c["title"])
            if c["type"] in ("前置", "附录") or norm_t == norm_c:
                # 连续前置/附录段合并（title 追加标注, subs 记录子段）; 相邻同名编段合并（第一编@80变体+@81）
                merged[-1]["end"] = c["end"]
                merged[-1]["page_count"] = merged[-1]["end"] - merged[-1]["start"] + 1
                if c["type"] in ("前置", "附录"):
                    if c["title"] not in merged[-1]["title"]:
                        merged[-1]["title"] += " / " + c["title"]
                    merged[-1].setdefault("subs", []).append(
                        {"title": c["title"], "start": c["start"], "end": c["end"]})
                if c.get("chapters"):
                    merged[-1].setdefault("chapters", []).extend(c["chapters"])
                continue
        if c["type"] in ("前置", "附录"):
            c.setdefault("subs", []).insert(0, {"title": c["title"], "start": c["start"], "end": c["end"]})
        merged.append(c)
    return merged


def fix_section_marks(text):
    lines = text.split("\n")
    out = []
    for l in lines:
        s = l.strip()
        m = RE_SEC_S.match(s)
        if m:
            out.append("§" + m.group(1))
            continue
        m = RE_SEC_S2.match(s)
        if m:
            out.append("§%s %s" % (m.group(1), m.group(2)))
            continue
        out.append(l)
    return "\n".join(out)


def rebuild_chapters(clean, sections, safe, rel=None):
    """清洗结果回灌 DP 阅读器格式: book_chapters/{bid}/{i}.json + meta.json（并更新 ckpt books 条数）"""
    import hashlib
    ckpt = json.load(open(CKPT, encoding="utf-8"))
    books = ckpt.get("books", {})
    # rel 反查: 调用方可直传（新书未标记时）; 否则 safe 反查
    if rel is None:
        rel = next((k for k in books if re.sub(r"[^\w\-.]", "_", k) == safe), None)
    if rel is None:
        print(f"⚠ 未在 ckpt books 中找到 {safe} 对应的 rel, 跳过回灌", flush=True)
        return
    bid = hashlib.md5(rel.encode()).hexdigest()[:12]
    detail_fp = os.path.join(BASE_DIR, "data", "book_detail", f"{bid}.json")
    title = author = None
    if os.path.exists(detail_fp):
        det = json.load(open(detail_fp, encoding="utf-8"))
        title, author = det.get("title"), det.get("author")
    if not title:
        title = os.path.splitext(os.path.basename(safe))[0].split("_")[-1]
    if not author:
        author = "未知"

    # 块组装: 前置/附录 → subs 子段块; 编 → 编块 + 子章块
    # toc 同步生成: 编级为分组标题（type=part, 不可点击）; 块为可跳转条目（type=chapter, index=文件序号）
    blocks = []
    toc = []
    for s in sections:
        if s["type"] == "编":
            toc.append({"type": "part", "title": s["title"]})  # 分组标题: 编段第一个块前（含无子章的卷）
            if s.get("chapters"):
                subs = sorted(s["chapters"], key=lambda x: x["start"])
                prev = s["start"]
                bounds = [c["start"] for c in subs] + [s["end"] + 1]
                for k, ch in enumerate(subs):
                    seg_end = bounds[k + 1] - 1  # 章块覆盖到下一个章首页前（OCR 缺失的章并入）
                    if ch["start"] > prev:
                        blocks.append({"title": s["title"], "pages": [prev, ch["start"] - 1]})
                        toc.append({"type": "chapter", "title": s["title"], "index": len(blocks) - 1})
                    blocks.append({"title": ch["title"], "pages": [ch["start"], seg_end]})
                    toc.append({"type": "chapter", "title": ch["title"], "index": len(blocks) - 1})
                    prev = seg_end + 1
                if prev <= s["end"]:
                    blocks.append({"title": s["title"], "pages": [prev, s["end"]]})
                    toc.append({"type": "chapter", "title": s["title"], "index": len(blocks) - 1})
            else:
                blocks.append({"title": s["title"], "pages": [s["start"], s["end"]]})
                toc.append({"type": "chapter", "title": s["title"], "index": len(blocks) - 1})
        elif s["type"] in ("前置", "附录"):
            for sub in s.get("subs") or [{"title": s["title"], "start": s["start"], "end": s["end"]}]:
                blocks.append({"title": sub["title"], "pages": [sub["start"], sub["end"]]})
                toc.append({"type": "chapter", "title": sub["title"], "index": len(blocks) - 1})
        else:
            blocks.append({"title": s["title"], "pages": [s["start"], s["end"]]})
            toc.append({"type": "chapter", "title": s["title"], "index": len(blocks) - 1})

    bd = os.path.join(BASE_DIR, "data", "book_chapters", bid)
    os.makedirs(bd, exist_ok=True)
    for fn in os.listdir(bd):
        os.remove(os.path.join(bd, fn))
    def _title_subseq(s, t):
        """s 是否为 t 的子序列（标题页 OCR 断行变体: "下\n室" → "下室" 匹配 "地下室"）"""
        it = iter(t)
        return all(c in it for c in s)

    def _find_title_row(lines, ttl):
        """首页中找标题行（标题可在页中, 前部可能是上一章结尾残留）→ (行号, 是否长标题跨行) 或 None"""
        for j, ln in enumerate(lines[:25]):
            s = "".join(ln.strip().split())
            if not s:
                continue
            if s == ttl:
                return j, False
            if abs(len(s) - len(ttl)) <= 1:
                n = sum(1 for a, b in zip(s, ttl) if a == b)
                if n / max(len(s), len(ttl)) >= 0.6:
                    return j, False
            if len(s) <= len(ttl) + 15 and s.startswith(ttl):
                return j, True
        return None

    # 章首页剥离预处理: 块 i(>0) 首页中, 标题行之前的行 = 上一章结尾残留
    #   → 追加到块 i-1 的页序列末尾（按跨页段规则续接, 不误切段）
    #   → 块 i 从标题行之后开始（长标题附 ≤3 短续行, 与旧逻辑一致）
    page_extra = {i: [] for i in range(len(blocks))}
    stripped = {}
    for i in range(len(blocks)):
        ttl = "".join((blocks[i]["title"] or "").split())
        if len(ttl) < 2:
            continue
        lines = clean[blocks[i]["pages"][0]].split("\n")
        t_all = "".join("".join(lines).split())
        # 整页即标题页判断: 整页文字基本就是标题（含 OCR 断行/错字变体）才剔除;
        # 若页面含正文（远长于标题）, 标题只是页中一行 → 走逐行剥离, 不能整页删
        if (t_all == ttl or
                (len(ttl) >= 3 and ttl in t_all and len(t_all) <= len(ttl) + 3) or
                (len(ttl) >= 3 and len(ttl) - 2 <= len(t_all) <= len(ttl) + 3
                 and _title_subseq(t_all, ttl))):
            stripped[i] = ""  # 首页整页即标题（含 OCR 断行变体）→ 整页剔除
            continue
        hit = _find_title_row(lines, ttl)
        if hit is None:
            continue
        ti, is_long = hit
        if ti > 0 and i > 0:
            page_extra[i - 1].append("\n".join(lines[:ti]))  # 标题前行 = 上一章结尾残留
        rest = lines[ti + 1:]
        if is_long:
            n_skip = 0
            while rest and n_skip < 3 and len(rest[0].strip()) <= 20:
                rest = rest[1:]
                n_skip += 1
        while rest:  # 重复标题行（"致读者\n致读者"）循环剥
            hit2 = _find_title_row(rest, ttl)
            if hit2 is None:
                break
            ti2, is_long2 = hit2
            if ti2 > 0 and i > 0:
                page_extra[i - 1].append("\n".join(rest[:ti2]))  # 标题间行也归上一章尾
            rest = rest[ti2 + 1:]
            if is_long2:
                n_skip = 0
                while rest and n_skip < 3 and len(rest[0].strip()) <= 20:
                    rest = rest[1:]
                    n_skip += 1
        stripped[i] = "\n".join(rest) if rest else ""

    for idx, blk in enumerate(blocks):
        lo, hi = blk["pages"]
        # 段落重排（原书自然段粒度）: OCR 扫描行级处理 —
        #   行尾无句末标点 → 续行拼接（跨页/跨章句子不切断, 行内 \n 不保留, 段 = 自然段）
        #   行尾有句末标点 / 遇空行 → 段结束
        #   首页标题行已由剥离预处理剔除（Reader 的 h2 已显示标题, 避免重复）
        pages_iter = []
        if idx in stripped:
            pages_iter.append(stripped[idx])  # 首页（已剥标题行）; 空串也占位（整页标题页）
        else:
            pages_iter.append(clean[lo])      # 首页未命中剥离 → 原样
        pages_iter += [clean[p] for p in range(lo + 1, hi + 1)]
        pages_iter += page_extra.get(idx, [])  # 下一章首页顶部的本章残留（排最后, 续接本块尾段）
        paras = []
        buf = ""
        for t0 in pages_iter:
            t = t0.strip()
            if not t:
                continue
            lines = t.split("\n")
            for line in lines:
                s = line.strip()
                if not s:
                    if buf:
                        paras.append(buf)
                        buf = ""
                    continue
                if buf and buf[-1] not in SENT_END:
                    buf += s
                else:
                    if buf:
                        paras.append(buf)
                    buf = s
        if buf:
            paras.append(buf)
        ch = {"index": idx, "title": blk["title"],
              "content": [{"type": "text", "value": p} for p in paras]}
        json.dump(ch, open(os.path.join(bd, f"{idx}.json"), "w", encoding="utf-8"), ensure_ascii=False)
    # 块 end 扩展: 单页块（如卷标题页）内容并入直到下一个块起始前（卷（A）19-62 → 卷（B）63 起）;
    # 最后一块扩展到书尾（卷八 464 → 526）
    for k in range(len(blocks) - 1):
        if blocks[k]["pages"][1] < blocks[k + 1]["pages"][0] - 1:
            blocks[k]["pages"][1] = blocks[k + 1]["pages"][0] - 1
    if blocks:
        blocks[-1]["pages"][1] = max(blocks[-1]["pages"][1], len(clean) - 1)
    titles = [blk["title"] for blk in blocks]
    meta = {"bookId": bid, "title": title, "author": author, "toc": toc,
            "cover": None, "chapterCount": len(blocks), "chapterTitles": titles}
    json.dump(meta, open(os.path.join(bd, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False)
    books[rel] = {"chapters": len(blocks), "src": "ocr"}
    ckpt["books"] = books
    json.dump(ckpt, open(CKPT, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"\n已回灌 DP 阅读器: book_chapters/{bid}/ {len(blocks)} 块", flush=True)
    for blk in blocks:
        print(f"  - {blk['title']}  页{blk['pages'][0]}-{blk['pages'][1]}", flush=True)
    return bid


def process_pages(pages, safe, do_rebuild=False, rel=None):
    """核心清洗流程: 页数组 → 竖排合并 → 页眉/页码清理 → 编章切分 → §修复 → 输出 v4/toc/chapters + 回灌
    返回 (clean, chapters)"""
    pages = [merge_tate_page(t) for t in pages]
    toc_start, toc_end = find_toc_span(pages)
    toc_end = toc_end if toc_end is not None else 0  # 无目录页的书
    clean, headers, front_first = strip_header_footer(pages, rel=rel)
    toc = parse_toc(clean, toc_start or 0, toc_end) if toc_start is not None else []
    chapters = chapterize(clean, toc_end, headers, front_first, toc=toc)
    clean = [fix_section_marks(t) for t in clean]
    # 正文区孤立页码清理（书页码印在页中下部, 页首/尾检测抓不到; 附录索引区数字是索引页码不能删）
    appendix_start = next((c["start"] for c in chapters if c["type"] == "附录"), len(clean))
    for i in range(toc_end, appendix_start):
        lines = clean[i].split("\n")
        clean[i] = "\n".join(l for l in lines if not RE_PAGENUM.match(l.strip())).strip()
    base = os.path.splitext(os.path.basename(safe))[0]
    json.dump(clean, open(os.path.join(OUT_DIR, base + "_v4.json"), "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(toc, open(os.path.join(OUT_DIR, base + "_toc.json"), "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(chapters, open(os.path.join(OUT_DIR, base + "_chapters.json"), "w", encoding="utf-8"), ensure_ascii=False)
    if do_rebuild:
        rebuild_chapters(clean, chapters, safe, rel=rel)
    return clean, chapters, toc_end, appendix_start


def build_safe_map():
    """safe → rel 映射: 扫描 BOOKS_DIR（ckpt books 键已弃用, 2026-08-11）
    双变体: 规则式（· → _）与手工式（保留 ·）兼容既有 ocr KEY。"""
    m = {}
    for region in ["东方", "西方"]:
        rp = os.path.join(BOOKS_DIR, region)
        if not os.path.isdir(rp):
            continue
        for author in sorted(os.listdir(rp)):
            ap = os.path.join(rp, author)
            if not os.path.isdir(ap):
                continue
            for fn in sorted(os.listdir(ap)):
                fp = os.path.join(ap, fn)
                if not os.path.isfile(fp) or not fn.lower().endswith(".pdf"):
                    continue
                rel = os.path.relpath(fp, BOOKS_DIR).replace("\\", "/")
                m[re.sub(r"[^\w\-.]", "_", rel)] = rel   # 规则式
                m[re.sub(r"[^\w\-.·]", "_", rel)] = rel  # 手工式（保留 ·）
    return m


def main():
    rel = build_safe_map().get(SAFE)
    if not rel:
        print(f"✗ 磁盘上找不到 {SAFE} 对应的 PDF（扫描 {BOOKS_DIR}）, 退出", flush=True)
        return
    print(f"加载 OCR 文本: {SAFE}  →  {rel}", flush=True)
    pages = load_pages()
    print(f"共 {len(pages)} 页", flush=True)
    clean, chapters, toc_end, appendix_start = process_pages(pages, SAFE, do_rebuild=("--rebuild" in sys.argv), rel=rel)
    print(f"章节切分 {len(chapters)} 段", flush=True)
    for c in chapters:
        print(f"  [{c['type']}] {c['title']}  页{c['start']}-{c['end']} ({c['page_count']}页)", flush=True)

    base = os.path.splitext(os.path.basename(SAFE))[0]
    out_v4 = os.path.join(OUT_DIR, base + "_v4.json")
    out_toc = os.path.join(OUT_DIR, base + "_toc.json")
    out_ch = os.path.join(OUT_DIR, base + "_chapters.json")
    print(f"\n输出: {os.path.basename(out_v4)} / {os.path.basename(out_toc)} / {os.path.basename(out_ch)}", flush=True)
    toc = json.load(open(out_toc, encoding="utf-8"))

    print("\n=== 章节切分结果 ===")
    for c in chapters:
        flag = "✓" if c["page_count"] > 3 else "?"
        print(f"  {flag} [{c['type']}] {c['title']}  页{c['start']}-{c['end']} ({c['page_count']}页)")
    print(f"\n=== 目录解析 {len(toc)} 条 (前20) ===")
    for e in toc[:20]:
        print(f"  {e['level']:2s} {str(e['num'] or ''):6s} {e['title'] or '(续)'}  p{e['page']}")


if __name__ == "__main__":
    main()
