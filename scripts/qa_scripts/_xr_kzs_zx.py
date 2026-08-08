# -*- coding: utf-8 -*-
"""#158 看，这是哲学（唐纳德·帕尔默）a6d6def88c3b 修复
病因（CHKLIST ✗B "本章主要哲学思想/思考题"节与章平铺且顺序乱）:
  旧 83 章：① 哲学家小节全部当章平铺（泰勒斯~纳斯鲍姆）；② "本章主要哲学思想/
  思考题"被切为独立章且顺序严重错乱（旧 0/1 竟是第二章的柏拉图/亚里士多德，
  旧 2-6 为 思想/思考题/思想/思考题/思考题 重复错位）；③ 章标题页全部缺失
  （序言/导言/第一章~第八章/哲学术语表/出版后记）；④ 合并小节被切散（普罗泰戈拉
  ~卡里克勒斯和克里提亚从"智者"文件切出、阿威罗伊/迈蒙尼德从"伊斯兰和犹太教
  哲学"切出、边沁/密尔从"功利主义"切出、胡塞尔~萨特从"现象学和存在主义"切出、
  索绪尔~德里达从"结构主义和后结构主义"切出、詹姆士/杜威从"实用主义"切出、
  弗雷格~蒯因从"分析传统"切出、纳斯鲍姆从"告别二十世纪哲学"切出）。
源（F:/philosophy/西方/唐纳德·帕尔默/看，这是哲学.epub，79 spine 文件）：
  无 h1-h3，标题是特定 class 的 p（calibre_13=章标题×12、calibre_152/33/69/30=
  小节标题×89，均 <45 字）；每章 = 章标题页（第一~四、六章独立文件；第五/七/八章
  标题页与首小节合并，如 [48]=第五章标题页+笛卡尔）+ 哲学家小节文件 + 独立的
  "本章主要哲学思想"文件 + "思考题"文件；[3] 目录页（条目即权威章/节命名）、
  [0] 封面/[1] 书名页/[2] 空目录/[78] 英文 TOC 不建章；正文 p=calibre_15/20/31/14，
  img×376（jpeg→webp 重新转换入库），空 blockquote 仅为样式容器。
旧数据 83 章内容错乱（不止思想/思考题平铺）：标题与内容张冠李戴（旧 0"柏拉图"内容
  实为思考题、旧 3"思考题"内容实为智者~亚里士多德整节 27295 字）、章标题残片
  （旧 2"本章主要哲学思想"仅 63 字）、图块 825 vs 源 376（跨章重复膨胀）——
  旧 43 万净字是错位+重复的产物，源 19.2 万为完整书稿。
修复:
  基于源全量重建 12 章 + 89 section（#151 模式：标题类 p 为 section 锚点块）：
  0 序言｜1 导言（+section 思考题）｜2 第一章 前苏格拉底哲学家（公元前6世纪至
  前5世纪，13 section）｜3 第二章 雅典时期（10 section）｜4 第三章 希腊化时期和
  罗马时期（6）｜5 第四章 中世纪和文艺复兴时期哲学（14）｜6 第五章 大陆理性主义
  和英国经验主义（10）｜7 第六章 康德之后的英国和大陆哲学（10）｜8 第七章 现象学
  传统及其余续（11）｜9 第八章 实用主义及分析传统（14）｜10 哲学术语表｜
  11 出版后记；cc 83→12；
  章内小节（哲学家/思想/思考题/人像子节）全部按源顺序归位为 section 锚点；
  图片全部 jpeg→webp（PIL quality 85，md5[:10] 命名写双端 book_images）；
  blockquote/广告 div/空 p 不进入正文；逐块 diff 与源 0 处不匹配。
用法: python _xr_kzs_zx.py [--dry]
"""
import hashlib, io, json, os, posixpath, re, sys, shutil, zipfile
from bs4 import BeautifulSoup
from PIL import Image

BID = "a6d6def88c3b"
EPUB = "F:/philosophy/西方/唐纳德·帕尔默/看，这是哲学.epub"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"
IMG_SRC = f"f:/program/Python/PhiAgent/backend/data/book_images"
IMG_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_images"

# 章 → 源 spine 文件组（[0]封面/[1]书名页/[2]空目录/[3]目录页/[78]英文TOC 不建章）
FILE_PLAN = {
    0: [4],                       # 序言
    1: [5, 6],                    # 导言 + 思考题
    2: [7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],   # 第一章 13 section
    3: [21, 22, 23, 24, 25, 26, 27],                            # 第二章 10 section
    4: [28, 29, 30, 31, 32, 33, 34],                            # 第三章 6 section
    5: [35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47],    # 第四章 14 section
    6: [48, 49, 50, 51, 52, 53, 54, 55, 56, 57],                # 第五章 10 section
    7: [58, 59, 60, 61, 62, 63, 64, 65, 66],                    # 第六章 10 section
    8: [67, 68, 69, 70],                                        # 第七章 11 section
    9: [71, 72, 73, 74, 75],                                    # 第八章 14 section
    10: [76],                     # 哲学术语表
    11: [77],                     # 出版后记
}
# 章标题（源首文件首标题块，dry run 校验一致）
CHAPTER_TITLES = {
    0: "序言", 1: "导言",
    2: "第一章前苏格拉底哲学家（公元前6世纪至前5世纪）",
    3: "第二章雅典时期（公元前5世纪至前4世纪）",
    4: "第三章希腊化时期和罗马时期（公元前4世纪至公元5世纪）",
    5: "第四章中世纪和文艺复兴时期哲学（公元5世纪至15世纪）",
    6: "第五章大陆理性主义和英国经验主义（公元17世纪至18世纪）",
    7: "第六章康德之后的英国和大陆哲学（公元19世纪）",
    8: "第七章现象学传统及其余续（公元19世纪晚期和20世纪，及其在21世纪的余续）",
    9: "第八章实用主义及分析传统（从19世纪晚期及20世纪进入21世纪）",
    10: "哲学术语表", 11: "出版后记",
}
# 标题类 p（源无 h 标签，标题是特定 class 的短 p；101 个已人工核对与目录一致）
TITLE_CLS = {"calibre_13", "calibre_152", "calibre_33", "calibre_69", "calibre_30"}

def norm(s):
    return re.sub(r"\s+", "", s or "")

def is_title_p(p):
    t = p.get_text("", strip=True)
    if not set(p.get("class", [])) & TITLE_CLS:
        return False
    if not t or len(t) >= 45 or "ePUBw" in t:
        return False
    return True

z = zipfile.ZipFile(EPUB)
names = z.namelist()
def soup_of(i):
    """spine[i] 的真实文件名：i=0 → titlepage.xhtml；i≥1 → text/part{i-1}.html"""
    fn = "titlepage.xhtml" if i == 0 else f"part{i - 1:04d}.html"
    cand = [n for n in names if n.split("/")[-1] == fn]
    if not cand:
        raise SystemExit(f"找不到 spine 文件 {fn}")
    return BeautifulSoup(z.read(cand[0]).decode("utf-8", "ignore"), "html.parser"), cand[0]

# ---- 图片转换（jpeg → webp，md5[:10] 命名，双端写入；src 相对 text/ 目录）----
os.makedirs(IMG_SRC, exist_ok=True)
os.makedirs(IMG_DST, exist_ok=True)
img_cache = {}

def image_block(img, zf):
    src = img.get("src", "")
    key = (zf, src)
    if key in img_cache:
        return dict(img_cache[key])
    if not src:
        raise SystemExit(f"无 src 的 img: {zf}")
    abs_p = posixpath.normpath(posixpath.join(posixpath.dirname(zf), src))
    raw = z.read(abs_p)
    im = Image.open(io.BytesIO(raw))
    if im.mode != "RGB":
        im = im.convert("RGB")
    out = io.BytesIO()
    im.save(out, "WEBP", quality=85)
    data = out.getvalue()
    h = hashlib.md5(data).hexdigest()[:10]
    fname = f"{BID}_{h}.webp"
    for base in (IMG_SRC, IMG_DST):
        p = os.path.join(base, fname)
        if not os.path.exists(p):
            open(p, "wb").write(data)
    w, ht = im.size
    b = {"type": "image", "src": f"/api/books/{BID}/image/{fname}",
         "alt": img.get("alt", ""), "w": w, "h": ht}
    img_cache[key] = b
    return dict(b)

# ---- 逐章解析（标题类 p → section 锚点块；正文 p 文本段与 img 交错）----
files = {}
for idx, group in FILE_PLAN.items():
    content, sections = [], {}
    title = None  # 章标题：章首文件第一个标题 p（不入块）
    for gi in group:
        soup, zf = soup_of(gi)
        for el in soup.find_all(["p", "img"]):
            if el.name == "img":
                if el.find_parent("p") is not None:
                    continue  # p 内 img 已由 p 分支处理
                content.append(image_block(el, zf))
            else:
                if is_title_p(el):
                    t = el.get_text("", strip=True)
                    if title is None:
                        title = t  # 章标题（仅入 toc）
                    else:
                        content.append({"type": "text", "value": t})
                        sections[t] = len(content) - 1
                    continue
                # 正文 p：文本段与 img 交错 → text 块 / image 块
                buf, n_img = [], 0
                for child in el.children:
                    if child.name is None:
                        if str(child).strip():
                            buf.append(str(child).strip())
                    elif child.name == "img":
                        n_img += 1
                        if buf:
                            t = "".join(buf).strip()
                            if t and "ePUBw" not in t:
                                content.append({"type": "text", "value": t})
                            buf = []
                        content.append(image_block(child, zf))
                    else:
                        s = child.get_text("", strip=True)
                        if s:
                            buf.append(s)
                t = "".join(buf).strip()
                if t:
                    if "ePUBw" not in t:
                        content.append({"type": "text", "value": t})
                elif n_img == 0:
                    continue  # 空段（含空 blockquote）
    if title is None:
        raise SystemExit(f"章{idx} 无标题")
    if norm(title) != norm(CHAPTER_TITLES[idx]):
        print(f"⚠ 章{idx} 标题={title!r} ≠ 计划 {CHAPTER_TITLES[idx]!r}")
    files[idx] = {"index": idx, "title": title, "content": content, "sections": sections}

assert len(files) == 12, len(files)

def p_texts_split(el):
    """p 的文本段序列（img 处断开）"""
    out, buf = [], []
    for child in el.children:
        if child.name is None:
            if str(child).strip():
                buf.append(str(child).strip())
        elif child.name == "img":
            if buf:
                out.append("".join(buf))
                buf = []
        else:
            s = child.get_text("", strip=True)
            if s:
                buf.append(s)
    if buf:
        out.append("".join(buf))
    return out

# ---- 逐块 diff（剔除 section 锚点块后，重建 p 块 vs 源 p 逐对对比）----
bad = 0
for idx, group in FILE_PLAN.items():
    f = files[idx]
    # 用锚点块位置过滤（不用值：思想总结文件的哲学家名行与锚点同名，值过滤会误杀）
    sec_pos = set(f["sections"].values())
    ps = [b["value"] for k, b in enumerate(f["content"])
          if b.get("type") == "text" and k not in sec_pos]
    sps = []
    for gi in group:
        soup, zf = soup_of(gi)
        for p in soup.find_all("p"):
            if is_title_p(p):
                continue
            for t in p_texts_split(p):  # 与重建端同一拆分规则（含图 p 的文字段）
                if t and "ePUBw" not in t:
                    sps.append(t)
    if len(ps) != len(sps):
        print(f"[{idx}] {f['title'][:20]}: 重建 {len(ps)} p vs 源 {len(sps)} p *** 块数不同 ***")
        bad += 1
    for k, (b, s) in enumerate(zip(ps, sps)):
        if b != s:
            print(f"[{idx}] 块{k} 不匹配:\n  重建({len(b)}): {b[:60]}\n  源  ({len(s)}): {s[:60]}")
            bad += 1
            if bad > 12:
                raise SystemExit("差异过多，终止")
print(f"逐块 diff: {0 if bad == 0 else bad} 处不匹配")
if bad:
    raise SystemExit("块级验证失败")

# ---- 字数对照 ----
print("=== 12 章重建（源净字数对照）===")
total = 0
for idx in range(12):
    f = files[idx]
    nc = sum(len(norm(b.get("value", ""))) for b in f["content"] if b.get("type") == "text")
    total += nc
    src_txt = sum(len(norm(soup_of(gi)[0].get_text("", strip=True))) for gi in FILE_PLAN[idx])
    imgs = sum(1 for b in f["content"] if b.get("type") == "image")
    secs = len(f["sections"])
    print(f"[{idx:2d}] {f['title'][:30]:<32s} {nc:6d}字净 {imgs:3d}图 "
          f"{len(f['content']):4d}块  源{src_txt:6d}  差{nc-src_txt:+6d}  section×{secs}")
print(f"新总净(文本): {total}  新图块: {sum(1 for f in files.values() for b in f['content'] if b.get('type') == 'image')}（源 376）")
old_total = 0
for i in range(83):
    p = os.path.join(SRC, f"{i}.json")
    if os.path.exists(p):
        ch = json.load(open(p, encoding="utf-8"))
        old_total += sum(len(norm(b.get("value", ""))) for b in ch["content"])
print(f"旧总净: {old_total}  差: {total-old_total:+d}")
def first_text(f):
    return next(b["value"] for b in f["content"] if b.get("type") == "text")
def last_text(f):
    return next(b["value"] for b in reversed(f["content"]) if b.get("type") == "text")
print("新0首块:", first_text(files[0])[:30])
print("新1首块:", first_text(files[1])[:30], "| 新1末块:", last_text(files[1])[:30])
print("新2首块:", first_text(files[2])[:40])
print("新6末块:", last_text(files[6])[:30])
print("新9末块:", last_text(files[9])[:30])
print("新11首块:", first_text(files[11])[:30])

if "--dry" in sys.argv:
    sys.exit(0)

# ---- toc ----
toc = []
for idx in range(12):
    f = files[idx]
    toc.append({"type": "chapter", "title": f["title"], "index": idx, "level": 1})
    for t, sec in f["sections"].items():
        toc.append({"type": "section", "title": t, "index": idx, "sec": sec, "level": 2})
meta_new = {"chapterCount": 12, "chapterTitles": [files[i]["title"] for i in range(12)], "toc": toc}
print("\n=== toc ===")
for t in toc:
    print(f"  {t['type']:8s} idx{t['index']:2d} lv{t.get('level')} sec={t.get('sec')!r} {t['title'][:36]}")

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
for idx in range(12):
    f = files[idx]
    json.dump({"index": idx, "title": f["title"], "content": f["content"]},
              open(os.path.join(SRC, f"{idx}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
meta = {
    "bookId": old_meta.get("bookId") or BID,
    "title": old_meta.get("title") or "看，这是哲学",
    "author": old_meta.get("author") or "唐纳德·帕尔默",
    "toc": toc,
    "cover": old_meta.get("cover"),
    "chapterCount": 12,
    "chapterTitles": meta_new["chapterTitles"],
}
json.dump(meta, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print(f"✓ 写入 {SRC}: 12 章 + meta.json（图 {IMG_SRC}）")

shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
print("✓ 同步 DP chapters")

for p in (DETAIL_SRC, DETAIL_DST):
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))
        d["toc"] = toc
        d["chapterCount"] = 12
        d["chapterTitles"] = meta_new["chapterTitles"]
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
        print(f"✓ book_detail 更新: {p}")

if os.path.exists(BOOKS_JSON):
    bj = json.load(open(BOOKS_JSON, encoding="utf-8"))
    bl = bj if isinstance(bj, list) else bj.get("books", [])
    hit = False
    for b in bl:
        if b.get("id") == BID:
            b["chapterCount"] = 12
            hit = True
    if hit:
        with open(BOOKS_JSON, "w", encoding="utf-8") as f:
            json.dump(bl if isinstance(bj, list) else {**bj, "books": bl}, f,
                      ensure_ascii=False, indent=None)
        print("✓ books.json chapterCount 更新")
    else:
        print("⚠ books.json 未找到该书")
