# -*- coding: utf-8 -*-
"""#151 猜想与反驳（卡尔·波普尔，傅季重等译）ff783ce7c481 修复
病因（CHKLIST ✗M 跳缺第一/四/五/九/十一/十三/十四/十六章）:
  旧 20 章实际问题远超缺章：① 缺 11 个正文章（一/四/五/九/十一/十三/十四/
  十六/十八/十九/二十）；② 边界错位混章——旧 5 论知识和无知的来源 48900 字
  （源仅 26566，混入导论+卷标+第一章开头）、旧 8 三章 55418 字（源 23412，混入
  第四/五章）、旧 12 八章尾混入"十、真理…"标题、旧 15"反驳"=卷标页+第十一章
  全文（42663≈源[20]+[21]）、旧 16 十二+十三两章合并、旧 18 十七+十八合并、
  旧 1 Digital Lab简介混入技术注释目录；③ 多个附录被单独切章（科学哲学的若干
  问题/历史上的猜想…/可能错误…）；④ 章标题带脚注编号"(1)"。
源（F:/philosophy/西方/卡尔·波普尔/猜想与反驳（二十世纪西方哲学经典）.epub，
33 spine 文件）：h1=章标题（去尾 (N) 脚注编号）、h3=章内节标题（section 锚点）、
p=正文块、img×71（数学公式/插图，jpeg→webp 重新转换入库）；源[4][9][20] 为
名言页（序言前/猜想卷/反驳卷），并入 4 序言/8 一/18 十一 章首。
修复:
  基于源全量重建 29 章 + 52 section（#144/#147 模式：h3 标题块为 section 锚点）：
  0 版权信息｜1 Digital Lab简介（logo 图）｜2 目录｜3 中译本序｜4 序言（+名言页）
  ｜5 第二版序｜6 导论｜7 论知识和无知的来源（导言，4 图）｜8 一、科学：猜想和
  反驳（+爱因斯坦名言，11 图）｜9 二｜10 三（6 节）｜11 四｜12 五（附录节）
  ｜13 六｜14 七（6 节）｜15 八（2 节）｜16 九（4 图）｜17 十（6 节，含附录）
  ｜18 十一（+柏拉图名言，14 图，6 节）｜19 十二（7 节）｜20 十三｜21 十四
  ｜22 十五（14 图，3 节）｜23 十六｜24 十七（8 节）｜25 十八｜26 十九（1 图）
  ｜27 二十｜28 附录 若干技术性的注释（17 图，6 节）；cc 20→29。
  图片：全部从源 jpeg 重新转换 webp（PIL，quality 85，md5[:10] 命名写双端
  book_images）；旧 92 张 webp 保留不删（旧数据 _old_bad 曾引用）。
  旧数据仅作对照（逐块 diff + 字数差异说明），不参与重建。
用法: python _xr_cxyfb_rebuild.py [--dry]
"""
import hashlib, io, json, os, posixpath, re, sys, shutil, zipfile
from bs4 import BeautifulSoup, NavigableString
from PIL import Image

BID = "ff783ce7c481"
EPUB = "F:/philosophy/西方/卡尔·波普尔/猜想与反驳（二十世纪西方哲学经典）.epub"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"
IMG_SRC = f"f:/program/Python/PhiAgent/backend/data/book_images"
IMG_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_images"

# 章 → 源 spine 文件组（末文件提供 h1 标题）
FILE_PLAN = {
    0: [0], 1: [1], 2: [2], 3: [3], 4: [4, 5], 5: [6], 6: [7], 7: [8],
    8: [9, 10], 9: [11], 10: [12], 11: [13], 12: [14], 13: [15], 14: [16],
    15: [17], 16: [18], 17: [19], 18: [20, 21], 19: [22], 20: [23], 21: [24],
    22: [25], 23: [26], 24: [27], 25: [28], 26: [29], 27: [30], 28: [31],
}
# 章标题（源 h1 去脚注编号，人工核对）
TITLES = {
    0: "版权信息", 1: "Digital Lab简介", 2: "目录", 3: "中译本序", 4: "序言",
    5: "第二版序", 6: "导论", 7: "论知识和无知的来源",
    8: "一、科学：猜想和反驳", 9: "二、哲学问题的本质及其科学根源",
    10: "三、关于人类知识的三种观点", 11: "四、关于一种理性的传统理论",
    12: "五、回到前苏格拉底哲学家", 13: "六、谈贝克莱是马赫和爱因斯坦的先驱",
    14: "七、康德的批判和宇宙学", 15: "八、论科学和形而上学的地位",
    16: "九、逻辑演算和算术演算为什么可应用于实在",
    17: "十、真理、合理性和科学知识增长",
    18: "十一、科学与形而上学的分界",
    19: "十二、语言和身—心问题——相互作用论的重述",
    20: "十三、身—心问题的一个说明", 21: "十四、日常语言中的自我涉及和意义",
    22: "十五、辩证法是什么？", 23: "十六、社会科学中的预测和预言",
    24: "十七、公众舆论和自由主义原则", 25: "十八、乌托邦和暴力",
    26: "十九、我们时代的历史：一个乐观主义者的观点",
    27: "二十、人文主义和理性", 28: "附录 若干技术性的注释",
}

def norm(s):
    return re.sub(r"\s+", "", s or "")

def clean_title(t):
    """去脚注编号（任意位置）：'论知识和无知的来源(1)' → '论知识和无知的来源'；
    '语言和身—心问题 (1) ——相互作用论的重述' → '语言和身—心问题——相互作用论的重述'"""
    return re.sub(r"\s*\(\d+\)\s*", "", t).strip()

def p_texts(el):
    """p 的文本段序列（按文档序拆分，img 处断开；段非空才返回）"""
    out, buf = [], []
    for child in el.children:
        if child.name is None:  # NavigableString / Comment
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

z = zipfile.ZipFile(EPUB)
names = z.namelist()
def soup_of(i):
    fn = f"Text/part{i:04d}.xhtml"
    cand = [n for n in names if n.endswith(fn.split("/")[-1])]
    return BeautifulSoup(z.read(cand[0]).decode("utf-8", "ignore"), "html.parser")

# ---- 图片转换（jpeg → webp，md5[:10] 命名，双端写入）----
os.makedirs(IMG_SRC, exist_ok=True)
os.makedirs(IMG_DST, exist_ok=True)
img_cache = {}  # src 路径 → 块

def image_block(img):
    src = img.get("src", "")
    if src in img_cache:
        return dict(img_cache[src])
    raw = z.read(posixpath.normpath("OEBPS/Text/" + src))
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
    img_cache[src] = b
    return dict(b)

# ---- 逐章解析（h1=章标题；h3=section 锚点块；p=正文/图）----
files = {}
for idx, group in FILE_PLAN.items():
    content, sections = [], {}
    title = TITLES[idx]
    h1_found = None
    for gi in group:
        soup = soup_of(gi)
        for el in soup.find_all(["h1", "h3", "p", "img"]):
            if el.name == "img":
                if el.find_parent("p") is not None:
                    continue  # p 内 img 已由 p 分支处理
                content.append(image_block(el))
            elif el.name == "h1":
                t = clean_title(el.get_text(" ", strip=True))
                h1_found = t
            elif el.name == "h3":
                t = clean_title(el.get_text(" ", strip=True))
                content.append({"type": "text", "value": t})
                sections[t] = len(content) - 1
            else:
                # p：文本段与 img 按文档序交错 → text 块 / image 块
                buf = []
                n_img = 0
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
                        content.append(image_block(child))
                    else:
                        s = child.get_text("", strip=True)
                        if s:
                            buf.append(s)
                t = "".join(buf).strip()
                if t:
                    if "ePUBw" not in t:
                        content.append({"type": "text", "value": t})
                elif n_img == 0:
                    continue  # 空段
    if h1_found and norm(h1_found) != norm(title):
        print(f"⚠ 章{idx} h1={h1_found!r} ≠ 计划标题 {title!r}")
    files[idx] = {"index": idx, "title": title, "content": content, "sections": sections}

assert len(files) == 29, len(files)

# ---- 逐块 diff（剔除 section 标题块后，重建 p 块 vs 源 p 逐对对比）----
bad = 0
for idx, group in FILE_PLAN.items():
    f = files[idx]
    ps = [b["value"] for b in f["content"]
          if b.get("type") == "text" and b["value"] not in f["sections"]]
    sps = []
    for gi in group:
        soup = soup_of(gi)
        for p in soup.find_all("p"):
            for t in p_texts(p):  # 与重建端同一拆分规则（含图 p 的文字段）
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
print("=== 29 章重建（源净字数对照）===")
total = 0
for idx in range(29):
    f = files[idx]
    nc = sum(len(norm(b.get("value", ""))) for b in f["content"] if b.get("type") == "text")
    total += nc
    src_txt = sum(len(norm(soup_of(gi).get_text("", strip=True))) for gi in FILE_PLAN[idx])
    imgs = sum(1 for b in f["content"] if b.get("type") == "image")
    secs = ", ".join(t for t in f["sections"]) if f["sections"] else ""
    print(f"[{idx:2d}] {f['title'][:30]:<32s} {nc:6d}字净 {imgs:2d}图 "
          f"{len(f['content'])}块  源{src_txt:6d}  差{nc-src_txt:+6d}" + (f"  section×{len(f['sections'])}" if secs else ""))
print(f"新总净(文本): {total}")
# 旧数据对照
old_total = 0
for i in range(20):
    p = os.path.join(SRC, f"{i}.json")
    if os.path.exists(p):
        ch = json.load(open(p, encoding="utf-8"))
        old_total += sum(len(norm(b.get("value", ""))) for b in ch["content"])
print(f"旧总净: {old_total}  差: {total-old_total:+d}")
print(f"新图片块: {sum(1 for f in files.values() for b in f['content'] if b.get('type')=='image')}（源 98）")
print("新0首块:", files[0]["content"][0]["value"][:30])
print("新4首块:", files[4]["content"][0]["value"][:40], "| 新4末块:", files[4]["content"][-1]["value"][:30])
print("新8首块:", files[8]["content"][0]["value"][:40], "| 新8末块:", files[8]["content"][-1]["value"][:30])
print("新18首块:", files[18]["content"][0]["value"][:40], "| 新18末块:", files[18]["content"][-1]["value"][:30])
print("新28末块:", files[28]["content"][-1]["value"][:40])

if "--dry" in sys.argv:
    sys.exit(0)

# ---- toc ----
toc = []
for idx in range(29):
    f = files[idx]
    toc.append({"type": "chapter", "title": f["title"], "index": idx, "level": 1})
    for t, sec in f["sections"].items():
        toc.append({"type": "section", "title": t, "index": idx, "sec": sec, "level": 2})
meta_new = {"chapterCount": 29, "chapterTitles": [files[i]["title"] for i in range(29)], "toc": toc}
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
for idx in range(29):
    f = files[idx]
    json.dump({"index": idx, "title": f["title"], "content": f["content"]},
              open(os.path.join(SRC, f"{idx}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
meta = {
    "bookId": old_meta.get("bookId") or BID,
    "title": old_meta.get("title") or "猜想与反驳（二十世纪西方哲学经典）",
    "author": old_meta.get("author") or "卡尔·波普尔",
    "toc": toc,
    "cover": old_meta.get("cover"),
    "chapterCount": 29,
    "chapterTitles": meta_new["chapterTitles"],
}
json.dump(meta, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print(f"✓ 写入 {SRC}: 29 章 + meta.json（图 {IMG_SRC}）")

shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
print("✓ 同步 DP chapters")

for p in (DETAIL_SRC, DETAIL_DST):
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))
        d["toc"] = toc
        d["chapterCount"] = 29
        d["chapterTitles"] = meta_new["chapterTitles"]
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
        print(f"✓ book_detail 更新: {p}")

if os.path.exists(BOOKS_JSON):
    bj = json.load(open(BOOKS_JSON, encoding="utf-8"))
    bl = bj if isinstance(bj, list) else bj.get("books", [])
    hit = False
    for b in bl:
        if b.get("id") == BID:
            b["chapterCount"] = 29
            hit = True
    if hit:
        with open(BOOKS_JSON, "w", encoding="utf-8") as f:
            json.dump(bl if isinstance(bj, list) else {**bj, "books": bl}, f,
                      ensure_ascii=False, indent=None)
        print("✓ books.json chapterCount 更新")
    else:
        print("⚠ books.json 未找到该书")
