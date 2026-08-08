# -*- coding: utf-8 -*-
"""#8 从《理想国》到《正义论》（f15e7fd89491）修复
病因（CHKLIST ✗C：'toc 是内容摘要句非标题'）:
  旧 4 章 toc 全是内容摘要句当标题（'第二篇的主题是良知的进化…'），章节化完全错误。
  本书实为'轻松读懂 27 部西方哲学经典'：27 章，每章一部经典
  （柏拉图/亚里士多德/波爱修斯/马基雅维利/笛卡尔/霍布斯/斯宾诺莎/洛克×2/休谟×2/
   卢梭/康德×2/叔本华/密尔×2/克尔凯郭尔/马克思恩格斯/尼采×2/罗素/艾耶尔/萨特×2/
   维特根斯坦/罗尔斯）。
源: F:/philosophy/西方/合集&概述/从《理想国》到《正义论》.pdf（297 页扫描版，
   checkpoint OCR 完整 297 页无 fail；书内页码 = PDF页 - 10）
结构: p0-3 书名/CIP（书级页）｜ p4-10 目录（OCR 混排弃用）｜
  p11 起正文 27 章（奇数页章名页眉'XX：《XX》'，偶数页书名页眉'从《理想国》到《正义论》'，
  每页末行'·N·'页码）｜ p293-296 书末广告页（剔除）
修复: 全量重建 27 章（idx 连续 0-26）:
  章节边界 = 27 个章名页眉首次出现页（硬编码页区间）；
  页眉过滤: 首行匹配'作者：《书名》'模式（含 OCR 噪声变体'慰籍''暂学''纯辨'等）
   或书名页眉；页码过滤: 末行'·N·'；
  段落: 每页过滤后行拼接为一段（OCR 无空行无坐标，页级段落最稳，
   对齐 _rebuild_nicomachus.py 范式）；
  章标题 = 页眉原文（忠实源'作者：《书名》'格式）。
用法: python _xr_8_clxgdzyl_rebuild.py [--dry]
"""
import json, os, re, sys, shutil

BID = "f15e7fd89491"
CKPT = r"f:\program\Python\PhiAgent\backend\data\dp_pdf_import_ckpt.json"
SAFE = "西方_合集_概述_从_理想国_到_正义论_.pdf"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

def norm(s):
    return re.sub(r"\s+", "", s or "")

# 27 章: (idx, 标题=页眉原文, 起始页, 结束页)
CH = [
    (0, "柏拉图：《理想国》", 11, 26),
    (1, "亚里士多德：《尼各马可伦理学》", 27, 40),
    (2, "波爱修斯：《哲学的慰藉》", 41, 47),
    (3, "马基雅维利：《君主论》", 48, 56),
    (4, "笛卡尔：《第一哲学沉思集》", 57, 70),
    (5, "霍布斯：《利维坦》", 71, 81),
    (6, "斯宾诺莎：《伦理学》", 82, 88),
    (7, "洛克：《人类理解论》", 89, 101),
    (8, "洛克：《政府论（下篇）》", 102, 110),
    (9, "休谟：《人类理解研究》", 111, 121),
    (10, "休谟：《自然宗教对话录》", 122, 131),
    (11, "卢梭：《社会契约论》", 132, 139),
    (12, "康德：《纯粹理性批判》", 140, 147),
    (13, "康德：《道德形而上学基础》", 148, 156),
    (14, "叔本华：《作为意志和表象的世界》", 157, 165),
    (15, "密尔：《论自由》", 166, 177),
    (16, "密尔：《功利主义》", 178, 185),
    (17, "克尔凯郭尔：《非此即彼》", 186, 196),
    (18, "马克思和恩格斯：《德意志意识形态》的第一部分", 197, 203),
    (19, "尼采：《善恶的彼岸》", 204, 212),
    (20, "尼采：《论道德的谱系》", 213, 222),
    (21, "罗素：《哲学的问题》", 223, 231),
    (22, "艾耶尔：《语言、真理与逻辑》", 232, 246),
    (23, "萨特：《存在与虚无》", 247, 259),
    (24, "萨特：《存在主义与人道主义》", 260, 271),
    (25, "维特根斯坦：《哲学研究》", 272, 282),
    (26, "罗尔斯：《正义论》", 283, 292),
]

ckpt = json.load(open(CKPT, encoding="utf-8"))
pages = ckpt["ocr"][SAFE]
npages = {int(k): v for k, v in pages.items() if v and v != "__FAILED__"}
print(f"OCR 页: {min(npages)}-{max(npages)} 共 {len(npages)} 页")

# 页眉/页码过滤
BOOK_HEAD = "从《理想国》到《正义论》"
HEADER_RE = re.compile(r"^[^，。；：!?？\n]{1,12}[：:][《〈]")   # 作者：《书名》页眉（含 OCR 噪声变体）
PAGE_FOOT_RE = re.compile(r"^·?\d{1,4}·?[·.]?$")              # ·N· 页码

def page_text(i):
    """页 → 过滤页眉/页码后的行（页眉=首行, 页码=末行）"""
    t = npages.get(i, "")
    if not t:
        return []
    lines = [ln.strip() for ln in t.split("\n") if ln.strip()]
    if not lines:
        return []
    # 首行页眉（章名页眉 / 书名页眉 / 粘连书名页眉'L从《理想国》…'）
    if (lines[0] == BOOK_HEAD or HEADER_RE.match(lines[0])
            or (BOOK_HEAD in lines[0] and len(lines[0]) <= len(BOOK_HEAD) + 2)):
        lines.pop(0)
    # 末行页码 ·N·
    if lines and PAGE_FOOT_RE.match(lines[-1]):
        lines.pop()
    return lines

# ---- 逐章解析（页级段落范式） ----
files = {}
for idx, title, p0, p1 in CH:
    paras = []
    for i in range(p0, p1 + 1):
        lines = page_text(i)
        if lines:
            paras.append("".join(lines))
    if not paras:
        print(f"⚠ 章{idx} {title!r}: 无内容")
    files[idx] = {"index": idx, "title": title,
                  "content": [{"type": "text", "value": p} for p in paras]}
    first = paras[0][:32] if paras else "(空)"
    nc = sum(len(norm(p)) for p in paras)
    print(f"[{idx:2d}] {title[:30]:<32s} {nc:6d}字 {len(paras):3d}段 | {first!r}")
assert len(files) == 27

# ---- 验证 ----
total = 0
for idx in range(27):
    total += sum(len(norm(b["value"])) for b in files[idx]["content"])
print(f"\n新总净: {total}")
old_total = 0
for i in range(4):
    p = os.path.join(SRC, f"{i}.json")
    if os.path.exists(p):
        ch = json.load(open(p, encoding="utf-8"))
        old_total += sum(len(norm(b.get("value", ""))) for b in ch["content"])
print(f"旧总净: {old_total}  差: {total - old_total:+d}")

all_text = "".join(norm(b["value"]) for idx in range(27) for b in files[idx]["content"])
print("页眉清零:",
      "✓" if "从《理想国》到《正义论》" not in all_text else "✗书名页眉残留!",
      "✓" if not any("《理想国》" in norm(b["value"]) and len(norm(b["value"])) < 20
                    for idx in range(27) for b in files[idx]["content"]) else "✗")
# 页码清零：无独立纯数字段
pure_pages = [norm(b["value"]) for idx in range(27) for b in files[idx]["content"]
              if re.fullmatch(r"\d{1,4}", norm(b["value"]))]
print("页码清零:", "✓" if not pure_pages else f"✗ {pure_pages[:5]}")
# 关键内容验证
print("验证:",
      "✓柏拉图洞穴" if "洞穴" in norm(files[0]["content"][0]["value"]) else "✗!",
      "✓罗尔斯正义" if "正义" in "".join(norm(b["value"]) for b in files[26]["content"]) else "✗!",
      "✓维特根斯坦" if "语言游戏" in "".join(norm(b["value"]) for b in files[25]["content"]) else "✗!")

# ---- toc ----
toc = [{"type": "chapter", "title": files[i]["title"], "index": i, "level": 1} for i in range(27)]
print(f"\ntoc 项: {len(toc)}")
for t in toc[:4] + toc[-2:]:
    print(f"  {t['type']:8s} idx{t['index']} {t['title'][:40]}")

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
for idx in range(27):
    f = files[idx]
    json.dump({"index": idx, "title": f["title"], "content": f["content"]},
              open(os.path.join(SRC, f"{idx}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
meta = {
    "bookId": old_meta.get("bookId") or BID,
    "title": old_meta.get("title") or "从《理想国》到《正义论》",
    "author": old_meta.get("author") or "奈杰尔·沃伯顿",
    "toc": toc,
    "cover": old_meta.get("cover"),
    "chapterCount": 27,
    "chapterTitles": [files[i]["title"] for i in range(27)],
}
json.dump(meta, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print(f"✓ 写入 {SRC}: 27 章 + meta.json")

shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
print("✓ 同步 DP chapters")

for p in (DETAIL_SRC, DETAIL_DST):
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))
        d["toc"] = toc
        d["chapterCount"] = 27
        d["chapterTitles"] = meta["chapterTitles"]
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
        print(f"✓ book_detail 更新: {p}")

if os.path.exists(BOOKS_JSON):
    bj = json.load(open(BOOKS_JSON, encoding="utf-8"))
    bl = bj if isinstance(bj, list) else bj.get("books", [])
    hit = False
    for b in bl:
        if b.get("id") == BID:
            b["chapterCount"] = 27
            hit = True
    if hit:
        with open(BOOKS_JSON, "w", encoding="utf-8") as f:
            json.dump(bl if isinstance(bj, list) else {**bj, "books": bl}, f,
                      ensure_ascii=False, indent=None)
        print("✓ books.json chapterCount 更新")
    else:
        print("⚠ books.json 未找到该书")
