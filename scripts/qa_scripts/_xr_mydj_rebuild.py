# -*- coding: utf-8 -*-
"""#138 梦的解析（五书合订）4fc33e4af5fb 重建
病因（CHKLIST ✗B 书级缺失）:
  旧数据 115 文件平铺五书合订（总目录证实，CHKLIST 记"三书"实为五书）：
  ① 梦的解析（弗洛伊德/殷世钞译，江西人民出版社 2014）0-8（总目录/CIP/前言/第一~七章）
  ② 荣格自传：梦、记忆和思考（荣格/高鸣译）9-30（序言+一~十三；中学岁月被拆成 4 个
    伪章"Ⅰ/Ⅱ/Ⅲ/Ⅳ"、后期思想拆成"Ⅰ/Ⅱ"——源无子标题，导入管线编造）
  ③ 自卑与超越（阿德勒/马晓娜译，吉林出版集团 2015）31-80（12 个章标题全丢失，
    节当章平铺 1~49）
  ④ 弗洛伊德，性学与爱情心理学 81-99（结构完好，缺书级）
  ⑤ 乌合之众：群体时代的大众心理（勒庞）100-114（结构完好，缺书级+卷级）
源 EPUB（F:/philosophy/西方/西格蒙德·弗洛伊德/梦的解析.epub）验证:
  spine 248（spine[i]=index_split_{i-1}），CIP 与旧数据一致（同源）。
  结构: 书1 si0-45 / 书2 si46-72 / 书3 si73-139 / 书4 si140-176 / 书5 si177-247。
  标题体系: 无 h 标签，标题=正文流首块（p.calibre_31），节标题=独立文件首块。
  图片: 187 张（cover+images/00001-186.jpg）= book_images 187 张（md5 前 10 映射全部命中）；
  书1 照片插页 si5(20图) 并入前言章首，书2 si49(22图) 并入序言章首，书4 附录 si176(1图)。
重建:
  [part l0] 五书书级 ×5（乌合之众书内 3 卷再分卷级 l0 part）
    [ch] 各章（标题块剥离：完整匹配 / 拆两行"第一章"+"名目繁多的…"）
    [sec] 节（梦的解析 27 节 + 游途 5 节 + 自卑与超越 48 节 + 性学三论 11 节）
  内容 = spine 块流（BLOCK_TAGS 切分 + img→webp 映射，w/h 用 PIL 读取）。
  cc 115 → 69（8+15+13+18+15）+ 8 part + 91 section。
用法: python _xr_mydj_rebuild.py [--dry]
"""
import hashlib, json, os, re, sys, shutil, zipfile
from bs4 import BeautifulSoup, NavigableString
from PIL import Image

BID = "4fc33e4af5fb"
EPUB = "F:/philosophy/西方/西格蒙德·弗洛伊德/梦的解析.epub"
IMG_DIR = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_images"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

def norm(s):
    return re.sub(r"\s+", "", s or "")

# ---- EPUB 读取 ----
z = zipfile.ZipFile(EPUB)
names = z.namelist()
opf_path = [n for n in names if n.endswith(".opf")][0]
opf_txt = z.read(opf_path).decode("utf-8", "ignore")
manif = {}
for m in re.finditer(r"<item[^>]*?/?>", opf_txt):
    tag = m.group(0)
    mid = re.search(r'id="([^"]+)"', tag)
    mhref = re.search(r'href="([^"]+)"', tag)
    if mid and mhref:
        manif[mid.group(1)] = mhref.group(1)
spine = [manif[rid] for rid in re.findall(r'<itemref[^>]*?idref="([^"]+)"', opf_txt) if rid in manif]
assert len(spine) == 248, len(spine)

def read_file(si):
    href = spine[si]
    cand = [n for n in names if n.split("/")[-1] == href.split("/")[-1]]
    assert cand, (si, href)
    return z.read(cand[0]).decode("utf-8", "ignore")

def img_md5(si, src):
    """EPUB 内图 src → book_images webp 文件名（md5 前 10 映射, 已验证 187/187 命中）"""
    m = re.search(r"images/(\d+)", src)
    if not m:
        return None
    data = z.read(f"images/{m.group(1)}.jpg")
    h = hashlib.md5(data).hexdigest()[:10]
    fname = f"{BID}_{h}.webp"
    if not os.path.exists(os.path.join(IMG_DIR, fname)):
        print(f"  ⚠ 图缺失: {src} -> {fname}")
        return None
    return fname

BLOCK_TAGS = {'p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
              'li', 'blockquote', 'pre', 'section', 'article', 'br', 'hr'}

def blocks_from_desc(si, desc):
    blocks = []
    pending = ""
    def flush():
        nonlocal pending
        if pending:
            blocks.append({"type": "text", "value": pending.strip()})
            pending = ""
    for el in desc:
        name = getattr(el, "name", None)
        if name in ("script", "style", "nav", "head", "title"):
            continue
        if name == "img":
            flush()
            fname = img_md5(si, el.get("src", ""))
            if fname:
                try:
                    im = Image.open(os.path.join(IMG_DIR, fname))
                    w, h = im.size
                except Exception:
                    w, h = 0, 0
                blocks.append({"type": "image", "src": f"/api/books/{BID}/image/{fname}",
                               "alt": el.get("alt", ""), "w": w, "h": h})
            continue
        if name in BLOCK_TAGS:
            flush()
            continue
        if isinstance(el, NavigableString):
            text = el.strip()
            if text:
                if pending:
                    pending += text if text in "，。；：！？、「」『』“”‘’（）" else " " + text
                else:
                    pending = text
    flush()
    return blocks

file_blocks = {}
for si in range(248):
    raw = read_file(si)
    soup = BeautifulSoup(raw, "html.parser")
    for t in soup(["script", "style", "nav", "head", "title"]):
        t.decompose()
    body = soup.body or soup
    file_blocks[si] = blocks_from_desc(si, body.descendants)

# ---- 结构表（spine 顺序 si）----
# 每章: (标题, [(起,止)], [节标题si列表], 前置图页si或None, 标题两行剥离norm或None)
# 跳页: 0-4(书1 元数据) 46-49(书2 元数据+照片页49 并入序言) 73-77(书3 元数据+广告)
#       140-142(书4 元数据) 145/163/166/171/175(空) 177-180(书5 元数据+插图页)
#       182(导论标题页) 184/208/225(卷标题页) 186/188/192/194/196/201/206/210/
#       215/220/229/233/237/241(空分隔) 247(英文 TOC)
BOOKS = [
    ("梦的解析", [
        ("前言", [[6, 11]], [], 5, None),
        ("第一章 关于梦的问题的科学文献", [[12, 12], [13, 20]], [(13,0), (14,0), (15,0), (16,0), (17,0), (18,0), (19,0), (20,0)], None, None),
        ("第二章 梦的解析方法：对一个梦例的分析", [[21, 21]], [], None, None),
        ("第三章 梦是欲望的满足", [[22, 22]], [], None, None),
        ("第四章 梦的伪装", [[23, 23]], [], None, None),
        ("第五章 梦的材料和来源", [[24, 24], [25, 28]], [(25,0), (26,0), (27,0), (28,0)], None, None),
        ("第六章 梦的运作", [[29, 29], [30, 38]], [(30,0), (31,0), (32,0), (33,0), (34,0), (35,0), (36,0), (37,0), (38,0)], None, None),
        ("第七章 关于做梦过程的心理学理论", [[39, 39], [40, 45]], [(40,0), (41,0), (42,0), (43,0), (44,0), (45,0)], None, None),
    ]),
    ("荣格自传：梦、记忆和思考", [
        ("序言", [[50, 50]], [], 49, None),
        ("一、童年时光", [[51, 51]], [], None, None),
        ("二、中学岁月", [[52, 55]], [], None, None),
        ("三、大学年代", [[56, 56]], [], None, None),
        ("四、精神病治疗活动", [[57, 57]], [], None, None),
        ("五、西格蒙德·弗洛伊德", [[58, 58]], [], None, None),
        ("六、直面潜意识", [[59, 59]], [], None, None),
        ("七、著作", [[60, 60]], [], None, None),
        ("八、塔楼生活", [[61, 61]], [], None, None),
        ("九、游途", [[62, 66]], [(62,1), (63,0), (64,0), (65,0), (66,0)], None, None),   # 62 首块=章题, 次块"Ⅰ 北非"=节
        ("十、幻象", [[67, 67]], [], None, None),
        ("十一、死后生活", [[68, 68]], [], None, None),
        ("十二、后期思想", [[69, 71]], [], None, None),
        ("十三、我的一生", [[72, 72]], [], None, None),
    ]),
    ("自卑与超越", [
        ("前言　阿德勒：超越自卑，找到生命的真正意义", [[78, 78]], [], None,
         ("前言", "阿德勒：超越自卑，找到生命的真正意义")),
        ("第一章 我们对于意义的追寻", [[79, 79], [80, 85]], [(80,0), (81,0), (82,0), (83,0), (84,0), (85,0)], None, None),
        ("第二章 心灵和身体", [[86, 86], [87, 89]], [(87,0), (88,0), (89,0)], None, None),
        ("第三章 自卑与超越", [[90, 90], [91, 93]], [(91,0), (92,0), (93,0)], None, None),
        ("第四章 童年记忆", [[94, 94], [95, 97]], [(95,0), (96,0), (97,0)], None, None),
        ("第五章 梦", [[98, 98], [99, 103]], [(99,0), (100,0), (101,0), (102,0), (103,0)], None, None),
        ("第六章 家庭的影响", [[104, 104], [105, 107]], [(105,0), (106,0), (107,0)], None, None),
        ("第七章 学校的影响", [[108, 108], [109, 113]], [(109,0), (110,0), (111,0), (112,0), (113,0)], None, None),
        ("第八章 青春期", [[114, 114], [115, 118]], [(115,0), (116,0), (117,0), (118,0)], None, None),
        ("第九章 犯罪及预防", [[119, 119], [120, 123]], [(120,0), (121,0), (122,0), (123,0)], None, None),
        ("第十章 职业问题", [[124, 124], [125, 128]], [(125,0), (126,0), (127,0), (128,0)], None, None),
        ("第十一章 个体与社会", [[129, 129], [130, 134]], [(130,0), (131,0), (132,0), (133,0), (134,0)], None, None),
        ("第十二章 爱与婚姻", [[135, 135], [136, 139]], [(136,0), (137,0), (138,0), (139,0)], None, None),
    ]),
    ("弗洛伊德，性学与爱情心理学", [
        ("作品导读", [[143, 143]], [], None, None),
        ("前言：常谈常新的性与爱", [[144, 144]], [], None,
         ("前言", "常谈常新的性与爱")),
        ("第二版序", [[146, 146]], [], None, None),
        ("第三版序", [[147, 147]], [], None, None),
        ("第四版序", [[148, 148]], [], None, None),
        ("第一章 名目繁多的“性变态”", [[149, 149], [150, 152]], [(150,0), (151,0), (152,0)], None,
         ("第一章", "名目繁多的“性变态”")),
        ("第二章 为幼儿的性欲正名", [[153, 153], [154, 157]], [(154,0), (155,0), (156,0), (157,0)], None,
         ("第二章", "为幼儿的性欲正名")),
        ("第三章 青春期的变化", [[158, 158], [159, 162]], [(159,0), (160,0), (161,0), (162,0)], None,
         ("第三章", "青春期的变化")),
        ("第一章 儿童的性启蒙——写给福斯特的公开信", [[164, 164]], [], None, ("第一章", None)),
        ("第二章 儿童的性理论", [[165, 165]], [], None, ("第二章", None)),
        ("第一章 放荡的女人有人爱", [[167, 167]], [], None, ("第一章", None)),
        ("第二章 情爱与性爱的分离——论广泛存在的心理性阳痿", [[168, 168]], [], None, ("第二章", None)),
        ("第三章 处女是怎样一种妖孽", [[169, 169]], [], None, ("第三章", None)),
        ("第四章 文明的性道德与现代人的神经症", [[170, 170]], [], None, ("第四章", None)),
        ("第一章 自恋的描述及争议", [[172, 172]], [], None, ("第一章", None)),
        ("第二章 自恋的病理学研究", [[173, 173]], [], None, ("第二章", None)),
        ("第三章 自恋与对象选择", [[174, 174]], [], None, ("第三章", None)),
        ("附录：弗洛伊德生平及主要学说理论", [[176, 176]], [], None, ("一、生平经历", None)),
    ]),
    ("乌合之众：群体时代的大众心理", [
        ("前言", [[181, 181]], [], None, None),
        ("导论 群体的时代", [[183, 183]], [], None, None),
    ]),
]
VOLS = [
    ("第一卷 群体心理", [
        ("第一章 群体的心理特征——心理同一律", [[185, 187]], [], None, None),
        ("第二章 群体的感情和道德观", [[189, 197]], [], None, None),
        ("第三章 群体的思想观念、推理能力和想象力", [[198, 202]], [], None, None),
        ("第四章 群体信仰所采取的宗教形式", [[203, 207]], [], None, None),
    ]),
    ("第二卷 群体的观点与信念", [
        ("第一章 群体观点与信念的间接影响因素", [[209, 211]], [], None, None),
        ("第二章 群体观点的直接因素", [[212, 216]], [], None, None),
        ("第三章 集体领袖及其说服手法", [[217, 221]], [], None, None),
        ("第四章 群体信念与观点的变化局限性", [[222, 224]], [], None, None),
    ]),
    ("第三卷 群体的分类与特点", [
        ("第一章 群体分类", [[226, 228]], [], None, None),
        ("第二章 被称为犯罪群体的群体", [[230, 232]], [], None, None),
        ("第三章 刑事法庭的陪审团", [[234, 236]], [], None, None),
        ("第四章 选民群体", [[238, 240]], [], None, None),
        ("第五章 议会", [[242, 246]], [], None, None),
    ]),
]

toc = []
files = {}
idx = 0
sec_total = 0

def push_ch(title, blocks, strip2):
    global idx
    tn = norm(title)
    # 1) 完整标题块：剥第一个 norm==title 的 text 块（章首可能是 pre_si 照片说明文字）
    for k, b in enumerate(blocks):
        if b.get("type") == "text" and norm(b["value"]) == tn:
            # 标题后紧跟的英文副标块（"Preface"/"Forword"，br 拆行所致）一并剥离
            if k + 1 < len(blocks) and blocks[k + 1].get("type") == "text":
                nxt = blocks[k + 1]["value"].strip()
                if re.fullmatch(r"[A-Za-z\s]{1,12}", nxt):
                    blocks = blocks[:k] + blocks[k + 2:]
                else:
                    blocks = blocks[:k] + blocks[k + 1:]
            else:
                blocks = blocks[:k] + blocks[k + 1:]
            break
    else:
        # 2) 标题拆两行（"第一章"+"名目繁多的…" / "前言"+"常谈常新的…"）
        if strip2 and blocks and blocks[0].get("type") == "text":
            t0 = norm(blocks[0]["value"])
            if t0 == norm(strip2[0]):
                if strip2[1] is not None and len(blocks) > 1 and blocks[1].get("type") == "text":
                    if norm(blocks[1]["value"]) == norm(strip2[1]):
                        blocks = blocks[2:]
                elif len(blocks) > 1 and blocks[1].get("type") == "text":
                    # 未知第二行 → 仅剥首块（附录"一、生平经历"后即正文）
                    blocks = blocks[1:]
    files[idx] = {"index": idx, "title": title, "content": blocks}
    toc.append({"type": "chapter", "title": title, "index": idx, "level": 1})
    idx += 1

def add_secs(si_list):
    """节标题块保留为正文 + section 锚点；元素 = (si, 文件内块序号)"""
    global sec_total
    for si, blk_idx in si_list:
        bl = file_blocks[si]
        if bl and bl[blk_idx].get("type") == "text":
            sec_title = bl[blk_idx]["value"]
            cur = files[idx - 1]["content"]
            try:
                k = cur.index(bl[blk_idx])
            except ValueError:
                k = -1
            if k >= 0:
                sec_total += 1
                toc.append({"type": "section", "title": sec_title,
                            "index": idx - 1, "sec": k, "level": 2})
            else:
                print(f"  ⚠ 节锚点未找到 [{si}]: {sec_title[:20]}")

def build(book_title, chs):
    global idx
    toc.append({"type": "part", "title": book_title, "index": idx, "level": 0})
    for title, ranges, secs, pre_si, strip2 in chs:
        blocks = []
        if pre_si is not None:
            blocks += file_blocks[pre_si]      # 照片插页图块并入章首
        for a, b in ranges:
            for si in range(a, b + 1):
                blocks += file_blocks[si]
        push_ch(title, blocks, strip2)
        add_secs(secs)

for bt, chs in BOOKS:
    build(bt, chs)
for vt, chs in VOLS:
    build(vt, chs)

assert sum(1 for t in toc if t["type"] == "part") == 8, sum(1 for t in toc if t["type"] == "part")
assert idx == 8 + 14 + 13 + 18 + 15 == 68, idx   # 书1 8 + 书2 15 + 书3 13 + 书4 18 + 书5 15
print(f"章节总数: {idx}, section: {sec_total}")

# ---- 校验 ----
total_chars = 0
n_img = 0
for i in sorted(files):
    nc = sum(len(b.get("value", "")) for b in files[i]["content"] if b.get("type") == "text")
    ni = sum(1 for b in files[i]["content"] if b.get("type") == "image")
    n_img += ni
    total_chars += nc
    n_sec = sum(1 for t in toc if t["type"] == "section" and t["index"] == i)
    print(f"  {i:2d} {files[i]['title'][:40]:42s} {nc:7d} 字 img:{ni:2d} sec:{n_sec}")
assert len(files) == 68, len(files)
print(f"总: {len(files)} 章 + {sec_total} section, {total_chars} 字, {n_img} 图（EPUB 全量）")
old_total = 0
old_img = 0
if os.path.isdir(SRC):
    for fn in os.listdir(SRC):
        if fn.endswith(".json") and fn != "meta.json":
            ch = json.load(open(os.path.join(SRC, fn), encoding="utf-8"))
            old_total += sum(len(b.get("value", "")) for b in ch["content"] if b.get("type") == "text")
            old_img += sum(1 for b in ch["content"] if b.get("type") == "image")
print(f"旧数据: {old_total} 字, {old_img} 图（115 章）")
for t in toc:
    ind = "  " * t.get("level", 1)
    print(f"{ind}[{t['type']}] {t['title'][:44]}" + (f" sec:{t.get('sec')}" if t["type"] == "section" else ""))
print("首:", files[0]["title"], "| 末:", files[67]["title"])

if "--dry" in sys.argv:
    title_norms = {norm(t["title"]) for t in toc if t["type"] == "chapter"}
    # 合法正文块排除：第七章引言小节标题"前言"（源 si39 第二块，正文预期）
    EXCLUDE = {(7, "前言")}
    n_res = 0
    for i, ch in files.items():
        for k, b in enumerate(ch["content"]):
            if b.get("type") != "text" or not b["value"]:
                continue
            nv = norm(b["value"])
            prev = ch["content"][k - 1] if k > 0 else {}
            if len(nv) <= 14 and nv in title_norms and prev.get("type") != "image":
                if (i, nv) in EXCLUDE:
                    continue
                print(f"⚠ 疑似章题残留 [{i} {ch['title'][:12]}]: {b['value'][:34]!r}")
                n_res += 1
    print(f"残留: {n_res}")
    sys.exit(0)

# ---- 写入 ----
if os.path.isdir(SRC):
    suf = "_old_bad"
    i2 = 2
    while os.path.isdir(SRC + suf):
        suf = f"_old_bad{i2}"
        i2 += 1
    os.rename(SRC, SRC + suf)
    print(f"备份旧数据 → {os.path.basename(SRC) + suf}")
os.makedirs(SRC)
old_meta = {}
old_bid = SRC + "_old_bad"
if os.path.isdir(old_bid) and os.path.exists(os.path.join(old_bid, "meta.json")):
    old_meta = json.load(open(os.path.join(old_bid, "meta.json"), encoding="utf-8"))
for i, ch in files.items():
    json.dump(ch, open(os.path.join(SRC, f"{i}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
meta = {
    "bookId": old_meta.get("bookId") or BID,
    "title": old_meta.get("title") or "梦的解析",
    "author": old_meta.get("author") or "西格蒙德·弗洛伊德",
    "toc": toc,
    "cover": old_meta.get("cover"),
    "chapterCount": len(files),
    "chapterTitles": [ch["title"] for ch in files.values()],
}
json.dump(meta, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print(f"✓ 写入 {SRC}: {len(files)} 章 + meta.json")

shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
print("✓ 同步 DP chapters")

for p in (DETAIL_SRC, DETAIL_DST):
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))
        d["toc"] = toc
        d["chapterCount"] = len(files)
        d["chapterTitles"] = [ch["title"] for ch in files.values()]
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
        print(f"✓ book_detail 更新: {p}")

if os.path.exists(BOOKS_JSON):
    bj = json.load(open(BOOKS_JSON, encoding="utf-8"))
    bl = bj if isinstance(bj, list) else bj.get("books", [])
    hit = False
    for b in bl:
        if b.get("id") == BID:
            b["chapterCount"] = len(files)
            hit = True
    if hit:
        with open(BOOKS_JSON, "w", encoding="utf-8") as f:
            json.dump(bl if isinstance(bj, list) else {**bj, "books": bl}, f, ensure_ascii=False, indent=None)
        print("✓ books.json chapterCount 更新")
    else:
        print("⚠ books.json 未找到该书")
