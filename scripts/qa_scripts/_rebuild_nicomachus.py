# -*- coding: utf-8 -*-
"""尼各马可伦理学[注释导读本] 全本重导 (2026-08-08) — 目录串章/正文缺失修复
源: 417 页 OCR 缓存 (dp_pdf_import_ckpt.json)
结构: 导读(p13-48) + 十卷正文(p49-368) + 附录(p369-416) → 12 章
边界: 卷标题页硬编码 (p49/87/111/145/175/217/249/281/313/339); 附录 p369
页眉过滤: 尼各马可伦理学 / 正文注释 / 注释正文 / 纯页码 / 卷名整行 / 导读名整行
段落: 每页过滤后拼接为一段 (OCR 无空行, 正文注释行交错, 页级段落最稳)
用法: python _rebuild_nicomachus.py [--write]
"""
import sys, os, re, json, shutil
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"f:\program\Python\PhiAgent\backend\tools")
import rebuild_auto as ra

WRITE = "--write" in sys.argv
CKPT = r"f:\program\Python\PhiAgent\backend\data\dp_pdf_import_ckpt.json"
ckpt = json.load(open(CKPT, encoding="utf-8"))
pages = ckpt["ocr"]["西方_亚里士多德_尼各马可伦理学_注释导读本_.pdf"]
npages = {int(k): v for k, v in pages.items() if v and v != "__FAILED__"}
print(f"OCR 页: {min(npages)}-{max(npages)} 共{len(npages)}")

BOOKS = json.load(open(r"f:\program\Python\PhiAgent\app\public\books.json", encoding="utf-8"))
BID = next(b["id"] for b in BOOKS if b["title"] == "尼各马可伦理学[注释导读本]")
CH = ra.CH
D = os.path.join(CH, BID)
print("bid:", BID)

# ── 章节边界 (硬编码页, 卷标题页精确) ──
VOLS = [
    ("导读：从《尼各马可伦理学》找回对德性力量的确信", 13, 48),
    ("第一卷 伦理学和政治学：善、幸福与灵魂活动", 49, 86),
    ("第二卷 伦理德性与中庸", 87, 110),
    ("第三卷 德行特征与具体德性", 111, 144),
    ("第四卷 具体德性续论", 145, 174),
    ("第五卷 公正论", 175, 216),
    ("第六卷 理智德性论", 217, 248),
    ("第七卷 自制和快乐", 249, 280),
    ("第八卷 友爱论", 281, 312),
    ("第九卷 友爱续论", 313, 338),
    ("第十卷 论快乐、幸福和立法", 339, 368),   # 含 p367-368 注释正文
    ("附录", 369, 416),
]

# 卷名页眉整行 (标题页是分行的, 不会误伤)
VOL_HEADS = {v[1]: v[0] for v in VOLS[1:]}   # start_page -> 卷标题
VOL_TITLES = {v[0] for v in VOLS[1:]}
GUIDE_TITLE = "导读：从《尼各马可伦理学》找回对德性力量的确信"

# ── 页眉过滤 ──
PAGE_RE = re.compile(r"^\d{1,4}$")
FOOT_RE = re.compile(r"^第[一二三四五六七八九十]+[卷章]\s*\d{1,4}$")  # 卷名+页码粘连

def clean_page_lines(i):
    """返回该页过滤页眉后的文本行"""
    t = npages.get(i, "")
    if not t:
        return []
    out = []
    for ln in t.split("\n"):
        s = ln.strip()
        if not s:
            continue
        if s == "尼各马可伦理学" or s in ("正文注释", "注释正文"):
            continue
        if PAGE_RE.match(s) or FOOT_RE.match(s):
            continue
        if s in VOL_TITLES or s == GUIDE_TITLE:
            continue  # 卷名/导读名页眉 (整行)
        out.append(s)
    return out

# 提取各章
chapters = []
for title, lo, hi in VOLS:
    paras = []
    for i in range(lo, hi + 1):
        lines = clean_page_lines(i)
        if lines:
            paras.append("".join(lines))
    chapters.append({"title": title, "paras": paras, "page": lo})
    n = sum(len(x) for x in paras)
    print(f"  {title[:26]:<28} p{lo}-{hi} 段{len(paras)} 字{n}")

# ── 校验 ──
print("\n=== 校验 ===")
for c in chapters:
    if not c["paras"]:
        print(f"  空章: {c['title']}")
    first, last = c["paras"][0], c["paras"][-1]
    m = re.match(r"^[\d\W]{1,4}$", first[:6])
    if not first[:1].isalpha() and not re.match(r"^[\u4e00-\u9fff]", first[:1]):
        print(f"  首段异常开头: [{c['title'][:14]}] {first[:30]}")
    if last and last[-1] not in "。！？；…\"”)]":
        print(f"  尾段无句末标点: [{c['title'][:14]}] …{last[-35:]}")

if WRITE:
    BAK = os.path.join(CH, "_rebuild_bak", f"{BID}_v1")
    os.makedirs(BAK, exist_ok=True)
    if not os.listdir(BAK):
        for f in sorted(os.listdir(D)):
            shutil.copy2(os.path.join(D, f), os.path.join(BAK, f))
    meta = {"bookId": BID, "title": "尼各马可伦理学[注释导读本]",
            "author": "亚里士多德", "toc": [], "cover": None,
            "chapterCount": len(chapters), "chapterTitles": []}
    for i, c in enumerate(chapters):
        fp = os.path.join(D, f"{i}.json")
        content = [{"type": "text", "value": x} for x in c["paras"]]
        json.dump({"title": c["title"], "content": content, "index": i},
                  open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        meta["toc"].append({"type": "chapter", "title": c["title"], "index": i, "level": 1})
        meta["chapterTitles"].append(c["title"])
    json.dump(meta, open(os.path.join(D, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n写入完成: {len(chapters)} 章")
    ra.sync_three(BID)
    print("sync_three 完成")
