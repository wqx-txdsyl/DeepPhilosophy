# -*- coding: utf-8 -*-
"""#144 法哲学原理（黑格尔，范扬/张企泰译）17c85f942c78 修复
病因（CHKLIST ✗B 节当章平铺 + 边界错位）:
  ① 23 个节标题（一 取得占有/第一 婚姻/第二 司法/第三 世界历史…）当章平铺（旧 40 章）；
  ② 节标题块缺失——旧数据章 content 不含标题块（标题只在 toc），需从源补 h3 块
     作为 section 锚点；
  ③ 旧 0 出版说明章混入评述开头 1393 字（含"…一书评述"标题+贺麟署名+开头 8 段），
     旧 1 评述从"（一）"开始；
  ④ 旧 34/35 切分错位：旧 34 第一 国家法含"一 内部国家制度本身"标题块+第272-274节
     （块 53-82），旧 35 一 内部国家制度本身实为（一）王权/（二）行政权/（三）立法权
     （第275-320节）——重切为 34=260-271、35=272-320；
  ⑤ "第二 司法""第三 警察[26]和同业公会"标题块在旧 27/30 章尾（内容完整，归位即可）。
旧 40 章正文与源（商务馆版 EPUB，184 文件）逐组对照：全部差异 ≤11 字（空格/标点）
→ 内容完整，以旧数据块为主体重建。
修复:
  40 章 → 17 章 + 3 part + 26 section（#137 模式：section 内容并入父章，sec=锚点块索引）：
  0 出版说明（源[2]）｜1 评述（源[3..10]，含（一）~（七））｜2 序言｜3 导论
  part 第一篇 抽象法 → 4 第一篇 抽象法（第34-40节）
  5 第一章 所有权 + 4 section（一 取得占有/二 物的使用/三 所有权的转让/从所有权向契约的过渡）
  6 第二章 契约｜7 第三章 不法 + section（一 无犯意的不法，含二 诈欺/三 强制和犯罪）
  part 第二篇 道德 → 8 第二篇 道德（第105-114节）
  9 第一章 故意和责任｜10 第二章 意图和福利｜11 第三章 善和良心 + section（从道德向伦理的过渡）
  part 第三篇 伦理 → 12 第三篇 伦理（第142-157节）
  13 第一章 家庭 + 4 section（第一 婚姻/第二 家庭财富/第三 子女教育和家庭解体/从家庭向市民社会的过渡）
  14 第二章 市民社会 + 11 section（第一 需要的体系/一 需要及其满足的方式/二 劳动的方式/三 财富/
     第二 司法/一 作为法律的法/二 法律的定在/三 法院/第三 警察[26]和同业公会/一 警察/二 同业公会）
  15 第三章 国家 + 5 section（第一 国家法/一 内部国家制度本身/二 对外主权/第二 国际法/第三 世界历史）
  16 译后记
  22 个节标题块从源 h3 补入（35 已有块 53"一 内部国家制度本身"、旧24块27"第一 需要的体系"、
  旧27块30"第二 司法"、旧30块36"第三 警察[26]和同业公会"已存在）。
用法: python _xr_fzyx_rebuild.py [--dry]
"""
import json, os, re, sys, shutil, zipfile
from bs4 import BeautifulSoup

BID = "17c85f942c78"
EPUB = "F:/philosophy/西方/格奥尔格·威廉·弗里德里希·黑格尔/法哲学原理.epub"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

# 从源 h3 提取的节标题（打印清单核对一致）——旧章号 → 标题文本
TITLE_PATCH = {
    6: "一 取得占有", 7: "二 物的使用", 8: "三 所有权的转让", 9: "从所有权向契约的过渡",
    12: "一 无犯意的不法", 17: "从道德向伦理的过渡",
    20: "第一 婚姻", 21: "第二 家庭财富", 22: "第三 子女教育和家庭解体", 23: "从家庭向市民社会的过渡",
    25: "一 需要及其满足的方式", 26: "二 劳动的方式", 27: "三 财富",
    28: "一 作为法律的法", 29: "二 法律的定在", 30: "三 法院",
    31: "一 警察", 32: "二 同业公会",
    34: "第一 国家法", 36: "二 对外主权", 37: "第二 国际法", 38: "第三 世界历史",
}
# 各父章的 section 标题顺序（锚点须在合并 content 中按此序出现）
SECTION_PLAN = {
    5: ["一 取得占有", "二 物的使用", "三 所有权的转让", "从所有权向契约的过渡"],
    7: ["一 无犯意的不法"],
    11: ["从道德向伦理的过渡"],
    13: ["第一 婚姻", "第二 家庭财富", "第三 子女教育和家庭解体", "从家庭向市民社会的过渡"],
    14: ["第一 需要的体系", "一 需要及其满足的方式", "二 劳动的方式", "三 财富",
         "第二 司法", "一 作为法律的法", "二 法律的定在", "三 法院",
         "第三 警察 [26] 和同业公会", "一 警察", "二 同业公会"],
    15: ["第一 国家法", "一 内部国家制度本身", "二 对外主权", "第二 国际法", "第三 世界历史"],
}
NEW_TITLES = {
    0: "汉译世界学术名著丛书（分科本）出版说明",
    1: "黑格尔著《法哲学原理》一书评述",
    2: "序言", 3: "导论",
    4: "第一篇 抽象法", 5: "第一章 所有权", 6: "第二章 契约", 7: "第三章 不法",
    8: "第二篇 道德", 9: "第一章 故意和责任", 10: "第二章 意图和福利", 11: "第三章 善和良心",
    12: "第三篇 伦理", 13: "第一章 家庭", 14: "第二章 市民社会", 15: "第三章 国家",
    16: "译后记",
}
PARTS = [(4, "第一篇 抽象法"), (8, "第二篇 道德"), (12, "第三篇 伦理")]

# ---- 加载旧数据 ----
old = {}
for i in range(40):
    old[i] = json.load(open(os.path.join(SRC, f"{i}.json"), encoding="utf-8"))

def tb(t):
    return {"type": "text", "value": t}

def norm(s):
    return re.sub(r"\s+", "", s or "")

# ---- 组装 17 章 ----
# 每章: {"content": [...], "sections": {title: sec_pos}}
files = {}
def build(idx, parts):
    """parts: 列表 of ("blk", 旧章号) 或 ("blk", 旧章号, 起, 止) 或 ("title", 文本)"""
    content, anchors = [], {}
    for p in parts:
        if p[0] == "title":
            content.append(tb(p[1]))
        else:
            oid = p[1]
            seg = old[oid]["content"]
            if len(p) > 2:
                seg = seg[p[2]:p[3]] if len(p) > 3 else seg[p[2]:]
            content.extend(seg)
    # 计算 section 锚点
    sections = {}
    for title in SECTION_PLAN.get(idx, []):
        pos = next(k for k, b in enumerate(content)
                   if b.get("type") == "text" and norm(b.get("value")) == norm(title))
        sections[title] = pos
    files[idx] = {"index": idx, "title": NEW_TITLES[idx], "content": content, "sections": sections}

build(0, [("blk", 0, 0, 5)])   # 出版说明 = 旧0 块0-4
build(1, [("blk", 0, 5), ("blk", 1)])  # 评述 = 旧0 块5-14 + 旧1
build(2, [("blk", 2)])
build(3, [("blk", 3)])
build(4, [("blk", 4)])
build(5, [("blk", 5), ("title", TITLE_PATCH[6]), ("blk", 6),
          ("title", TITLE_PATCH[7]), ("blk", 7),
          ("title", TITLE_PATCH[8]), ("blk", 8),
          ("title", TITLE_PATCH[9]), ("blk", 9)])
build(6, [("blk", 10)])
build(7, [("blk", 11), ("title", TITLE_PATCH[12]), ("blk", 12)])
build(8, [("blk", 13)])
build(9, [("blk", 14)])
build(10, [("blk", 15)])
build(11, [("blk", 16), ("title", TITLE_PATCH[17]), ("blk", 17)])
build(12, [("blk", 18)])
build(13, [("blk", 19), ("title", TITLE_PATCH[20]), ("blk", 20),
           ("title", TITLE_PATCH[21]), ("blk", 21),
           ("title", TITLE_PATCH[22]), ("blk", 22),
           ("title", TITLE_PATCH[23]), ("blk", 23)])
build(14, [("blk", 24), ("title", TITLE_PATCH[25]), ("blk", 25),
           ("title", TITLE_PATCH[26]), ("blk", 26),
           ("title", TITLE_PATCH[27]), ("blk", 27),
           ("title", TITLE_PATCH[28]), ("blk", 28),
           ("title", TITLE_PATCH[29]), ("blk", 29),
           ("title", TITLE_PATCH[30]), ("blk", 30),
           ("title", TITLE_PATCH[31]), ("blk", 31),
           ("title", TITLE_PATCH[32]), ("blk", 32)])
# 15 第三章 国家：旧33 + 补"第一 国家法" + 旧34 块0-52(260-271) + 旧34 块53-82(内部制度 272-274) + 旧35 + 补二 对外主权 + 旧36 + 补第二 国际法 + 旧37 + 补第三 世界历史 + 旧38
build(15, [("blk", 33), ("title", TITLE_PATCH[34]), ("blk", 34, 0, 53),
           ("blk", 34, 53), ("blk", 35),
           ("title", TITLE_PATCH[36]), ("blk", 36),
           ("title", TITLE_PATCH[37]), ("blk", 37),
           ("title", TITLE_PATCH[38]), ("blk", 38)])
build(16, [("blk", 39)])

# ---- 源对照（字数验证）----
z = zipfile.ZipFile(EPUB)
names = z.namelist()
opf = [n for n in names if n.endswith('.opf')][0]
opf_txt = z.read(opf).decode('utf-8', 'ignore')
manif = {}
for m in re.finditer(r'<item[^>]*?/?>', opf_txt):
    tag = m.group(0)
    mid = re.search(r'id="([^"]+)"', tag)
    mhref = re.search(r'href="([^"]+)"', tag)
    if mid and mhref:
        manif[mid.group(1)] = mhref.group(1)
spine = [manif[rid] for rid in re.findall(r'<itemref[^>]*?idref="([^"]+)"', opf_txt) if rid in manif]
def txt_of(href):
    cand = [n for n in names if n.split('/')[-1] == href.split('/')[-1]]
    soup = BeautifulSoup(z.read(cand[0]).decode("utf-8", "ignore"), "html.parser")
    return re.sub(r"^\s*未知", "", soup.get_text("", strip=True))

SRC_RANGE = {
    0: (2, 3), 1: (3, 11), 2: (11, 12), 3: (12, 45),
    4: (45, 53), 5: (53, 71), 6: (71, 82), 7: (82, 86),
    8: (86, 97), 9: (97, 102), 10: (102, 113), 11: (113, 127),
    12: (127, 144), 13: (144, 152), 14: (152, 171), 15: (171, 183),
    16: (183, 184),
}

print("=== 17 章重建对照 ===")
total_new = total_old = 0
for idx in range(17):
    f = files[idx]
    nc = sum(len(b.get("value", "")) for b in f["content"])
    ncn = len(re.sub(r"\s+", "", "".join(b.get("value", "") for b in f["content"])))
    total_new += ncn
    src = "".join(txt_of(spine[i]) for i in range(*SRC_RANGE[idx]))
    src = re.sub(r"\s+", "", src)
    nb = len(f["content"])
    print(f"[{idx:2d}] {f['title'][:24]:<26s} {ncn:6d} 字(净) {nb:4d}块  源{len(src):6d}  差{ncn-len(src):+6d}")
    secs = f["sections"]
    if secs:
        print(f"      section: " + ", ".join(f"{t}@{s}" for t, s in secs.items()))
    # 旧数据对应章字数（对照总字数）
    if idx in (1,):
        pass
old_total = sum(sum(len(b.get("value", "")) for b in old[i]["content"]) for i in range(40))
print(f"新总: {total_new}  旧总: {old_total}  差: {total_new-old_total:+d}（+22 标题块 ≈ 每块 ~5-9 字）")
print("新0首块:", files[0]["content"][0]["value"][:30])
print("新0末块:", files[0]["content"][-1]["value"][:30])
print("新1首块:", files[1]["content"][0]["value"][:30])
print("新15尾块:", files[15]["content"][-1]["value"][:30])
print("新15 272节位置:", next(k for k, b in enumerate(files[15]["content"]) if norm(b.get("value","")) == "第272节"))

if "--dry" in sys.argv:
    sys.exit(0)

# ---- toc ----
toc = []
for idx in range(17):
    toc.append({"type": "chapter", "title": files[idx]["title"], "index": idx, "level": 1})
    for title, sec in files[idx]["sections"].items():
        toc.append({"type": "section", "title": title, "index": idx, "sec": sec, "level": 2})
# 插入 part（在对应篇章章前）
out = []
pit = iter(PARTS)
next_part = next(pit, None)
for t in toc:
    if next_part and t["type"] == "chapter" and t["index"] == next_part[0]:
        out.append({"type": "part", "title": next_part[1], "index": next_part[0], "level": 0})
        next_part = next(pit, None)
    out.append(t)
toc = out
meta_new = {
    "chapterCount": 17,
    "chapterTitles": [files[i]["title"] for i in range(17)],
    "toc": toc,
}
print("\n=== toc ===")
for t in toc:
    print(f"  {t['type']:8s} idx{t['index']:2d} lv{t.get('level')} sec={t.get('sec')!r} {t['title'][:34]}")

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
for idx in range(17):
    f = files[idx]
    json.dump({"index": idx, "title": f["title"], "content": f["content"]},
              open(os.path.join(SRC, f"{idx}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
meta = {
    "bookId": old_meta.get("bookId") or BID,
    "title": old_meta.get("title") or "法哲学原理",
    "author": old_meta.get("author") or "格奥尔格·威廉·弗里德里希·黑格尔",
    "toc": toc,
    "cover": old_meta.get("cover"),
    "chapterCount": 17,
    "chapterTitles": meta_new["chapterTitles"],
}
json.dump(meta, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print(f"✓ 写入 {SRC}: 17 章 + meta.json")

shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
print("✓ 同步 DP chapters")

for p in (DETAIL_SRC, DETAIL_DST):
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))
        d["toc"] = toc
        d["chapterCount"] = 17
        d["chapterTitles"] = meta_new["chapterTitles"]
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
        print(f"✓ book_detail 更新: {p}")

if os.path.exists(BOOKS_JSON):
    bj = json.load(open(BOOKS_JSON, encoding="utf-8"))
    bl = bj if isinstance(bj, list) else bj.get("books", [])
    hit = False
    for b in bl:
        if b.get("id") == BID:
            b["chapterCount"] = 17
            hit = True
    if hit:
        with open(BOOKS_JSON, "w", encoding="utf-8") as f:
            json.dump(bl if isinstance(bj, list) else {**bj, "books": bl}, f,
                      ensure_ascii=False, indent=None)
        print("✓ books.json chapterCount 更新")
    else:
        print("⚠ books.json 未找到该书")
