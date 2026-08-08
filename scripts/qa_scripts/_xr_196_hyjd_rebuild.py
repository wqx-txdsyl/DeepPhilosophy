# -*- coding: utf-8 -*-
"""#196 西方百年学术经典著作（合集 epub）88dc7d5961df 修复
病因（CHKLIST ✗B 多书合并）:
  29 书合集 epub 仅入库 25 章，严重错乱：idx0 残缺、idx3 巨章 249 万字吞全书
  （性学三论第三篇）、idx14 巨章 83 万字（人性论第三章）、idx4 残章、
  乌合之众缺第一章、16 本书从未入库。
源（F:/philosophy/西方/合集&概述/西方百年学术经典著作.epub，33MB）:
  spine 1349 项（按 part 序号单调，spine[0]=封面 titlepage.xhtml 无 toc）、
  toc.ncx 923 条（idx0 总目录 + 28 本真书 922 条，ncx 标题权威）。
  章文件结构：h1=章标题（不入块）、p=正文段落；无 h1 文件=纯 p 续段。
  书级页/分册页（书名页）无 p；lv1 卷页绝大多数 h1-only，
  少数有卷首语（社会契约论卷一 358 字、论美3第一部分 890 字注释、人性论第一卷 16 字等）。
修复:
  全量重建 28 书 804 章 + 28 书级 part（lv0）+ 81 卷/篇级 part（lv1）：
  · 内容 = toc 区间 spine 文件 p 块（#156 范式：toc[i] spine 位置 ~ toc[i+1] spine 位置
    所有文件，split 续段自然归位）；
  · 书级/lv1/跳过条目的区间内容（若有）并入其下首章头部（卷首语不丢）；
  · 章编号连续 0..803，文件名 = 编号.json；part.index = 其下首章编号；
  · 章首标题行剔除（norm(p0)==norm(title) 删；标题 in p0 前 20 字且 ≤45 字删）。
  · 跳过项 10 个：toc[0] 总目录、性学三论[26]空分册页、爱弥儿[107][112]上下册、
    人性论[352][360]上下册、论美[815][827][841][886]四册（均无正文）。
结构（28 书，卷/篇有子章=lv1，无子章卷=章）:
  1  梦的解析（上下册）15条: 上册/下册 lv1，12 章（3 序+7 章+2 附录）
  2  性学三论与爱情心理学 72条: 9 lv1（性学三论/爱情心理学/超越唯乐原则/集体心理学
     和自我分析/自我与本我/精神分析引论+3 部分），61 章
  3  儿童的人格教育 18条: 17 章｜4 爱弥儿 9条: 卷=章，6 章（序+5 卷），跳过上下册
  5  社会契约论 54条: 卷一~四 lv1，49 章｜6 欧洲文明史 15条: 14 章
  7  政府片论 9条: 8 章｜8 菊与刀 15条: 14 章
  9  国富论 42条: 第一篇~五 lv1，36 章｜10 人生的智慧 13条: 2 lv1，10 章
  11 道德情操论 74条: 7 卷+13 篇 lv1，53 章｜12 理想国 14条: 卷=章，13 章
  13 人性论 16条: 3 卷 lv1，10 章，跳过上下册｜14 论人类不平等的起源 6条: 5 章
  15 自杀论 19条: 3 编 lv1，15 章｜16 第一哲学沉思集 17条: 16 章
  17 形而上学 15条: 卷=章，14 章｜18 政治学 112条: 8 卷 lv1，103 章
  19 乌合之众 19条: 3 卷 lv1，15 章｜20 自卑与超越 13条: 12 章
  21 荣格自传 15条: 14 章｜22 我们内心的冲突 19条: 2 部分 lv1，16 章
  23 我们时代的神经症人格 18条: 17 章｜24 回忆苏格拉底 44条: 4 卷 lv1，39 章
  25 查拉图斯特拉如是说 66条: 4 卷 lv1，61 章｜26 培根论人生 60条: 59 章
  27 权力意志 20条: 4 卷 lv1（Ⅰ~Ⅴ篇=章），15 章｜28 论美国的民主 113条:
     2 卷+6 部分 lv1，100 章，跳过 4 册
  合计 804 章 + 28 lv0 + 81 lv1 = 913 toc 项。
验证: 每书章数/首末章标题；巨章消失（原 idx3 249 万字→按书拆分）；卷首语归位
  （社会契约论首章含'我想探查的是'）；16 本缺失书入库。
用法: python _xr_196_hyjd_rebuild.py [--dry]
"""
import json, os, re, sys, shutil, zipfile
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

BID = "88dc7d5961df"
EPUB = "F:/philosophy/西方/合集&概述/西方百年学术经典著作.epub"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

# 书: (书级 toc idx, 书名, 该书 toc 区间末 idx, lv1 part toc idx 列表, 跳过 toc idx 列表)
BOOKS = [
    (1,   "梦的解析（上下册）",          15, [5, 13],                                   []),
    (16,  "性学三论与爱情心理学",        87, [17, 22, 27, 36, 49, 55, 56, 61, 73],     [26]),
    (88,  "儿童的人格教育",             105, [],                                        []),
    (106, "爱弥儿（上下册）",           114, [],                                        [107, 112]),
    (115, "社会契约论",                 168, [117, 127, 140, 159],                      []),
    (169, "欧洲文明史",                 183, [],                                        []),
    (184, "政府片论",                   192, [],                                        []),
    (193, "菊与刀",                     207, [],                                        []),
    (208, "国富论（上下册）",           249, [211, 223, 230, 235, 246],                 []),
    (250, "人生的智慧",                 262, [252, 257],                                []),
    (263, "道德情操论",                 336, [264, 282, 299, 306, 309, 312, 322,
                                              265, 271, 278, 283, 290, 294,
                                              314, 315, 320, 323, 324, 330, 335],      []),
    (337, "理想国",                     350, [],                                        []),
    (351, "人性论（上下册）",           366, [353, 358, 363],                           [352, 360]),
    (367, "论人类不平等的起源",         372, [],                                        []),
    (373, "自杀论",                     391, [376, 381, 388],                           []),
    (392, "第一哲学沉思集",             408, [],                                        []),
    (409, "形而上学",                   423, [],                                        []),
    (424, "政治学",                     535, [425, 439, 452, 471, 488, 501, 510, 528],  []),
    (536, "乌合之众",                   554, [539, 544, 549],                           []),
    (555, "自卑与超越",                 567, [],                                        []),
    (568, "荣格自传：回忆·梦·思考",    582, [],                                        []),
    (583, "我们内心的冲突",             601, [586, 595],                                []),
    (602, "我们时代的神经症人格",       619, [],                                        []),
    (620, "回忆苏格拉底",               663, [621, 629, 640, 655],                      []),
    (664, "查拉图斯特拉如是说",         729, [665, 668, 691, 708],                      []),
    (730, "培根论人生",                 789, [],                                        []),
    (790, "权力意志（上下册）",         809, [792, 795, 799, 804],                      []),
    (810, "论美国的民主（套装共4册）",  922, [816, 842, 817, 828, 843, 865, 887, 914], [815, 827, 841, 886]),
]

def norm(s):
    return re.sub(r"\s+", "", s or "")

# ---- 解析 epub ----
z = zipfile.ZipFile(EPUB)
names = z.namelist()
opf = [n for n in names if n.endswith(".opf")][0]
root = ET.fromstring(z.read(opf))
spine = [i.get("idref") for i in root.find("{*}spine")]
man = {i.get("id"): i.get("href") for i in root.find("{*}manifest")}
spine_files = [man[r].split("/")[-1] for r in spine]
ncx = [n for n in names if n.endswith("toc.ncx")][0]
nroot = ET.fromstring(z.read(ncx))
ns = {"x": "http://www.daisy.org/z3986/2005/ncx/"}
navs = nroot.findall(".//x:navPoint", ns)
assert len(navs) == 923, len(navs)

def toc_src(i):
    return navs[i].find(".//x:content", ns).get("src").split("/")[-1].split("#")[0]

def toc_title(i):
    return navs[i].find("x:navLabel/x:text", ns).text or ""

spine_pos = {}
for p, f in enumerate(spine_files):
    spine_pos.setdefault(f, p)
TOCT = [(i, toc_title(i), toc_src(i)) for i in range(923)]

# ---- 章内容: 区间 p 块 ----
soup_cache = {}
def file_paras(fname):
    """文件 → p 文本列表（h1 标题不入块）。"""
    if fname in soup_cache:
        return soup_cache[fname]
    out = []
    if fname in spine_pos:
        cand = [n for n in names if n.split("/")[-1] == fname]
        if cand:
            s = BeautifulSoup(z.read(cand[0]).decode("utf-8", "ignore"), "html.parser")
            out = [p.get_text("", strip=True) for p in s.find_all("p") if p.get_text("", strip=True)]
    soup_cache[fname] = out
    return out

def interval_paras(sp0, sp1):
    paras = []
    for pos in range(sp0, sp1):
        paras.extend(file_paras(spine_files[pos]))
    return paras

CIP_TAIL = re.compile(r"(著\s*作|责任编辑|版式设计|责任印制|出版发行|地\s*址|印\s*刷"
                       r"|开\s*本|印\s*张|字\s*数|版\s*次|印\s*次|定\s*价|书\s*号)")

def strip_cip(paras, book_title):
    """章首 CIP 版权页剔除（兜底；书级/跳过区间版权已整体丢弃，此处处理
    lv1 区间可能带入的版权）：'图书在版编目（CIP）数据' 起，删到含'CIP数据核字'
    块（含），后续出版信息行（著作/责任编辑/版式设计/…/定价/书号 关键词）与
    书名尾行（≤25 字，匹配书级标题或 CIP 块 1 书名段）一并删。
    卷首语（CIP 前）保留。"""
    for k, v in enumerate(paras[:8]):
        if "图书在版编目" in v:
            hi = next((j for j in range(k, min(k + 8, len(paras)))
                       if "CIP数据核字" in paras[j]), None)
            if hi is None:
                return paras  # 异常格式，不动
            cip1 = paras[k + 1] if k + 1 < len(paras) else ""
            rest = paras[hi + 1:]
            while rest and (CIP_TAIL.search(rest[0])
                            or (len(rest[0]) <= 25 and (
                                norm(rest[0]) == norm(book_title)
                                or norm(rest[0]) in norm(book_title)
                                or norm(book_title) in norm(rest[0])
                                or norm(rest[0]) in norm(cip1)))):
                rest = rest[1:]
            return paras[:k] + rest
    return paras

# 每条目的 spine 位置（缺失 = 用下一条目的位置）
positions = []
for i, t, f in TOCT:
    positions.append(spine_pos.get(f, None))
for i in range(922, -1, -1):
    if positions[i] is None:
        positions[i] = positions[i + 1] if i + 1 < 923 else len(spine_files)

# ---- 遍历 toc 1..922 建章（0 总目录跳过）----
LV1 = set()
SKIP = set()
for _, _, _, lv1, skip in BOOKS:
    LV1.update(lv1)
    SKIP.update(skip)
assert len(SKIP) == 9, SKIP  # 分册页 9 个（toc[0] 总目录由遍历起点跳过）

files = {}
pending = []          # 待并入下章的 part/跳过内容
empty_chapters = []
n_chapters = 0
toc_out = []
book_titles = [(b[0], b[1]) for b in BOOKS]
biter = iter(book_titles)
next_book = next(biter, None)

cur_book_title = None
for i in range(1, 923):
    title, fname = TOCT[i][1], TOCT[i][2]
    if next_book and i == next_book[0]:
        # 书级 part（lv0）；书级页区间 = 书名页(空)+完整版权页(24~29 块) → 丢弃
        cur_book_title = next_book[1]
        toc_out.append({"type": "part", "title": next_book[1], "index": None, "level": 0})
        next_book = next(biter, None)
        continue
    sp0, sp1 = positions[i], (positions[i + 1] if i + 1 < 923 else len(spine_files))
    paras = interval_paras(sp0, sp1)
    if i in SKIP:
        continue   # 分册页/版权页（part0028 CIP 等），丢弃
    if i in LV1:
        pending.extend(paras)   # 卷页：卷首语并入其下首章
        toc_out.append({"type": "part", "title": title, "index": None, "level": 1})
        continue
    # 章
    ch_paras = pending + paras
    pending = []
    ch_paras = strip_cip(ch_paras, cur_book_title)
    if not ch_paras:
        empty_chapters.append(i)
        print(f"⚠ 空章 toc{i} {title!r}（区间 {sp0}~{sp1}）")
        continue
    # 章首标题行剔除（h1 不入块，兜底 p 首块=标题）
    while ch_paras and norm(ch_paras[0]) == norm(title):
        ch_paras.pop(0)
    if ch_paras and len(norm(title)) >= 3 and norm(title) in norm(ch_paras[0])[:20] \
       and len(norm(ch_paras[0])) <= 45:
        ch_paras.pop(0)
    files[n_chapters] = {"index": n_chapters, "title": title,
                         "content": [{"type": "text", "value": p} for p in ch_paras]}
    toc_out.append({"type": "chapter", "title": title, "index": n_chapters, "level": 1})
    n_chapters += 1

# part.index 回填（其下首章编号）
for t in toc_out:
    if t["type"] == "part":
        t["index"] = None
for idx, t in enumerate(toc_out):
    if t["type"] == "part":
        t["index"] = None
# 顺序扫描：part.index = 其后第一个 chapter 的 index
for j, t in enumerate(toc_out):
    if t["type"] == "part":
        for k in range(j + 1, len(toc_out)):
            if toc_out[k]["type"] == "chapter":
                t["index"] = toc_out[k]["index"]
                break
        else:
            print(f"⚠ part 无下章: {t['title']!r}")

print(f"\n=== 重建结果: {n_chapters} 章, toc {len(toc_out)} 项（28 lv0 + 81 lv1 + {n_chapters} 章）===")

# ---- 按书核对（toc 顺序切分）----
print("=" * 66)
total_chars = 0
cur_book = None
seg = []
segments = []
for t in toc_out:
    if t["type"] == "part" and t["level"] == 0:
        if cur_book is not None:
            segments.append((cur_book, seg))
        cur_book, seg = t["title"], []
    elif t["type"] == "chapter":
        seg.append(t)
if cur_book is not None:
    segments.append((cur_book, seg))
for bno, (bname, seg) in enumerate(segments):
    cnt = len(seg)
    chars = sum(sum(len(norm(b["value"])) for b in files[s["index"]]["content"]) for s in seg)
    total_chars += chars
    first_t = seg[0]["title"] if seg else None
    last_t = seg[-1]["title"] if seg else None
    print(f"[{bno+1:2d}] {bname}  {cnt:3d}章 {chars:8d}字 | {str(first_t)[:26]!r} … {str(last_t)[:18]!r}")

print(f"\n总字数: {total_chars}")
print(f"空章数: {len(empty_chapters)}")
if empty_chapters:
    print("空章 toc idx:", empty_chapters)

# ---- 巨章检查 ----
big = sorted(files.items(), key=lambda kv: -sum(len(norm(b["value"])) for b in kv[1]["content"]))[:5]
print("\n最大 5 章:")
for k, f in big:
    nc = sum(len(norm(b["value"])) for b in f["content"])
    print(f"  [{k}] {f['title'][:30]} {nc} 字 {len(f['content'])} 块")

# ---- 卷首语归位验证 ----
ch0 = "".join(norm(b["value"]) for b in files[[t for t in toc_out if t["type"]=="chapter"][0]["index"]]["content"])
alltext = {t["title"]: "".join(norm(b["value"]) for b in files[t["index"]]["content"])
           for t in toc_out if t["type"] == "chapter"}
sc = alltext.get("本卷主旨", "")
print("\n卷首语归位:", "✓社会契约论'我想探查的是'" if "我想探查的是" in sc else "✗社会契约论卷首语缺!")
rl = alltext.get("第一章 论观念的起源、组成、联结及其抽象意义等", "")
print("人性论卷首语:", "✓'所言即所感'" if "所言即所感" in rl[:100] else "✗人性论卷首语缺!")
def book_first_chapter(book_title, ch_title):
    """书级 part 后第一个指定标题章的内容。"""
    in_book = False
    for t in toc_out:
        if t["type"] == "part" and t["level"] == 0:
            in_book = (t["title"] == book_title)
            continue
        if in_book and t["type"] == "chapter" and t["title"] == ch_title:
            return alltext.get(ch_title, "")
    return ""
md = book_first_chapter("论美国的民主（套装共4册）", "序言")
print("论美卷首语:", "✓'（1835年）'归序言章" if "（1835年）" in md[:100] else "✗论美卷首语缺!")

# ---- CIP 残留检查 ----
cip_left = [t["title"] for t in toc_out if t["type"] == "chapter"
            and "图书在版编目" in alltext.get(t["title"], "")]
print("CIP 残留章:", cip_left if cip_left else "✓ 无（30 处版权页全剔除）")
bkt = [t["title"] for t in toc_out if t["type"] == "chapter"
       and "图书在版编目" in alltext.get(t["title"], "")]
for t in toc_out:
    if t["type"] == "chapter" and t["title"] in cip_left:
        f0 = files[t["index"]]["content"][0]["value"][:30]
        print(f"  残留: idx{t['index']} {t['title'][:20]!r} 首块 {f0!r}")

if "--dry" in sys.argv:
    sys.exit(0)

# ---- 写入 ----
if os.path.isdir(SRC):
    suf = "_old_bad"
    i2 = 2
    while os.path.isdir(SRC + suf):
        suf = f"_old_bad{i2}"
        i2 += 1
    os.rename(SRC, SRC + suf)
    print(f"\n备份旧数据 → {os.path.basename(SRC) + suf}")
os.makedirs(SRC)
old_meta = {}
old_bid = SRC + "_old_bad"
if os.path.isdir(old_bid) and os.path.exists(os.path.join(old_bid, "meta.json")):
    old_meta = json.load(open(os.path.join(old_bid, "meta.json"), encoding="utf-8"))
for idx in range(n_chapters):
    f = files[idx]
    json.dump({"index": idx, "title": f["title"], "content": f["content"]},
              open(os.path.join(SRC, f"{idx}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
meta = {
    "bookId": old_meta.get("bookId") or BID,
    "title": old_meta.get("title") or "西方百年学术经典著作",
    "author": old_meta.get("author") or "",
    "toc": toc_out,
    "cover": old_meta.get("cover"),
    "chapterCount": n_chapters,
    "chapterTitles": [files[i]["title"] for i in range(n_chapters)],
}
json.dump(meta, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print(f"✓ 写入 {SRC}: {n_chapters} 章 + meta.json")

shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
print("✓ 同步 DP chapters")

for p in (DETAIL_SRC, DETAIL_DST):
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))
        d["toc"] = toc_out
        d["chapterCount"] = n_chapters
        d["chapterTitles"] = meta["chapterTitles"]
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
        print(f"✓ book_detail 更新: {p}")

if os.path.exists(BOOKS_JSON):
    bj = json.load(open(BOOKS_JSON, encoding="utf-8"))
    bl = bj if isinstance(bj, list) else bj.get("books", [])
    hit = False
    for b in bl:
        if b.get("id") == BID:
            b["chapterCount"] = n_chapters
            hit = True
    if hit:
        with open(BOOKS_JSON, "w", encoding="utf-8") as f:
            json.dump(bl if isinstance(bj, list) else {**bj, "books": bl}, f,
                      ensure_ascii=False, indent=None)
        print("✓ books.json chapterCount 更新")
    else:
        print("⚠ books.json 未找到该书")
