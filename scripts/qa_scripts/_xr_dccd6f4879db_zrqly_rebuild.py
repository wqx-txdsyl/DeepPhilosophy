# -*- coding: utf-8 -*-
"""#未入清单 自然权利与历史（dccd6f4879db，列奥·施特劳斯）重建
病因: OCR 完成的 20 本未入清单书之一。旧 26 章为 dp_pdf_import 自动切章
  （强模式标题无命中→整本粗切），无页码清理。
源: F:/philosophy/西方/列奥·施特劳斯/自然权利与历史.pdf（429 页扫描版，
  彭刚译（生活·读书·新知三联书店 2003），checkpoint OCR 429 页 fail 0）
结构（目录 p92 双页码体系: 甘阳导言独立编页 1-82，正文重新编页）:
  p0-3 封面/CIP ｜ p4-85 甘阳导言'政治哲人施特劳斯：古典保守主义政治哲学的复兴'
  （书内 1-82；p4 标题块 4 行: 标题2行+副题+甘阳）
  p86 前言（杰罗姆·克尔文，书内 83） ｜ p87-88 序言（书内 84-85）
  p89-90 第七次重印本序言（1971年，书内 86-87）
  p91 圣经引文页（跳过） ｜ p92 目录（跳过）
  p93-101 导论（查尔斯·瓦尔格伦讲演，书内 1-9；p93 标题+正文同页）
  p102-128 第一章 自然权利论与历史方法（书内 16-42）
  p129-173 第二章 自然权利论与事实和价值的分野（书内 37-81；p129 标题跨 2 行）
  p174-212 第三章 自然权利观念的起源（书内 82-120）
  p213-259 第四章 古典自然权利论（书内 121-167）
  p260-348 第五章 现代自然权利论（书内 168-256；p261 'A.霍布斯'/p298 'B.洛克' 小节）
  p349-422 第六章 现代自然权利论的危机（书内 257-330；p349 标题+'A.卢梭'+
    页码行'2.52'/p393 'B.柏克' 小节；p422 尾'330'）
  p423-427 索引（人名索引，OCR 质量差，原样保留） ｜ p428 译后记（书内 336）
页码噪声: ① 独立页码行（'328'/'330'/'2.52'，页首或页尾）
  ② 行内粘连页码（书内页码粘在页首正文行行尾: p131'接37'/p201'本108'，
  剥离首个正文行行尾 2-3 位数字；正文误伤'国60'仅 p11 行中，不在首行，安全）
页眉: 无页眉系统（正文直排）
修复: 重建 13 章:
  标题行剥离（章前标题/小节标题/甘阳标题块精确匹配）；独立页码行剥整行；
  首个正文行行尾页码粘连剥数字后缀；索引页原样不清理；
  段落: 每页过滤后行拼接为一段（OCR 书范式）。
用法: python _xr_dccd6f4879db_zrqly_rebuild.py [--dry]
"""
import json, os, re, sys, shutil, time

BID = "dccd6f4879db"
CKPT = r"f:\program\Python\PhiAgent\backend\data\dp_pdf_import_ckpt.json"
SAFE = "西方_列奥_施特劳斯_自然权利与历史.pdf"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
# ⚠ 2026-08-08 事故修正：前端本地 dev 读 app/public/backend/data/book_chapters，必须双写
DST2 = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

def norm(s):
    return re.sub(r"\s+", "", s or "")

# 13 章: (idx, 标题, 起始页, 结束页) — PDF 页
CH = [
    (0, "甘阳导言：政治哲人施特劳斯——古典保守主义政治哲学的复兴", 4, 85),
    (1, "前言", 86, 86),
    (2, "序言", 87, 88),
    (3, "第七次重印本序言（1971年）", 89, 90),
    (4, "导论", 93, 101),
    (5, "第一章 自然权利论与历史方法", 102, 128),
    (6, "第二章 自然权利论与事实和价值的分野", 129, 173),
    (7, "第三章 自然权利观念的起源", 174, 212),
    (8, "第四章 古典自然权利论", 213, 259),
    (9, "第五章 现代自然权利论", 260, 348),
    (10, "第六章 现代自然权利论的危机", 349, 422),
    (11, "索引", 423, 427),
    (12, "译后记", 428, 428),
]
TOC_PAGES = {92}          # 目录页
SKIP_PAGES = {91}         # 圣经引文页
# 独立页码行（'328'/'330'/'2.52'/'33f'?——索引页不清理，'33f'不进正则）
PURE_NUM_RE = re.compile(r"^\d{1,4}$")
PURE_NUM_RE2 = re.compile(r"^\d{1,4}[.·]?\d{0,3}$")
# 首个正文行行尾页码粘连（2-3 位数字后缀）
TRAIL_NUM_RE = re.compile(r"\d{2,3}$")
# 章前/小节标题行（页内任意位置精确匹配剔除）
STRIP_TITLES = {
    "政治哲人施特劳斯：", "古典保守主义政治哲学的复兴",
    "（“列奥·施特劳斯政治哲学选刊”导言）", "甘阳",
    "前言", "第七次重印本序言（1971年）", "导论",
    "第一章自然权利论与历史方法", "第二章自然权利论与事实", "和价值的分野",
    "第三章自然权利观念的起源", "第四章古典自然权利论", "第五章现代自然权利论",
    "第六章现代自然权利论的危机",
    "A.霍布斯", "B.洛克", "A.卢梭", "B.柏克",
    "译后记",
}
# 序言带星号（p87 '序言*'）
TITLE_RE = re.compile(r"^序言\*?$")

# checkpoint 读重试（OCR 队列并发写 → 瞬时截断）
ckpt = None
for _try in range(5):
    try:
        ckpt = json.load(open(CKPT, encoding="utf-8"))
        break
    except json.JSONDecodeError:
        time.sleep(2)
if ckpt is None:
    sys.exit("checkpoint 连续 5 次读失败，OCR 队列可能正在写入，稍后重试")
pages = ckpt["ocr"][SAFE]
npages = {int(k): v for k, v in pages.items() if v and v != "__FAILED__"}
fails = sorted([int(k) for k, v in pages.items() if v == "__FAILED__"])
print(f"OCR 页: {min(npages)}-{max(npages)} 共 {len(npages)} 页, fail {len(fails)} 页: {fails}")

def page_lines(i):
    """页 → 行（剥页码噪声/标题后）; 索引页原样"""
    t = npages.get(i, "")
    if not t:
        return []
    ls = [ln.strip() for ln in t.split("\n") if ln.strip()]
    if 423 <= i <= 427:
        return ls                       # 索引页不清理
    ls = [l for l in ls if not PURE_NUM_RE.fullmatch(l) and not PURE_NUM_RE2.fullmatch(l)]
    ls = [l for l in ls if l not in STRIP_TITLES and not TITLE_RE.fullmatch(l)]
    if ls:
        ls[0] = TRAIL_NUM_RE.sub("", ls[0])   # 首个正文行行尾页码粘连
    return ls

# ---- 逐章解析（页级段落范式） ----
files = {}
for idx, title, p0, p1 in CH:
    paras = []
    for i in range(p0, p1 + 1):
        if i in TOC_PAGES or i in SKIP_PAGES:
            continue
        lss = page_lines(i)
        if lss:
            paras.append("".join(lss))
    if not paras:
        print(f"⚠ 章{idx} {title!r}: 无内容")
    files[idx] = {"index": idx, "title": title,
                  "content": [{"type": "text", "value": p} for p in paras]}
    nc = sum(len(norm(p)) for p in paras)
    first = paras[0][:36] if paras else "(空)"
    last = paras[-1][:22] if paras else ""
    print(f"[{idx}] {title:<30s} {nc:6d}字 {len(paras):3d}段 | {first!r} … {last!r}")
assert len(files) == 13

# ---- 验证 ----
total = sum(sum(len(norm(b["value"])) for b in files[idx]["content"]) for idx in range(13))
print(f"\n新总净: {total}")
all_text = "".join(norm(b["value"]) for idx in range(13) for b in files[idx]["content"])
# 页码噪声清零: 页首正文行行尾页码已剥 → 段首不得以'汉字+2-3数字'粘连开头
# （学术注释中的书目页码/引文编号如'第13，'/'1134'在段中/段尾，保留）
bad_page = [norm(b["value"])[:8] for idx in range(13) for b in files[idx]["content"]
            if re.match(r"[一-鿿]\d{2,3}", norm(b["value"]))]
print("页码粘连清零:", "✓" if not bad_page else f"✗ {bad_page[:6]}")
# 独立页码行清零: 段不得以 1-4 位数字开头或结尾
bad_s = [norm(b["value"]) for idx in range(13) for b in files[idx]["content"]
         if PURE_NUM_RE.fullmatch(norm(b["value"]))]
print("独立页码清零:", "✓" if not bad_s else f"✗ {bad_s[:5]}")
# 标题行清零
pure_titles = [norm(b["value"]) for idx in range(13) for b in files[idx]["content"]
               if norm(b["value"]) in {norm(t) for t in STRIP_TITLES}]
print("标题清零:", "✓" if not pure_titles else f"✗ {pure_titles[:5]}")
# 关键内容验证
ch = {idx: "".join(norm(b["value"]) for b in files[idx]["content"]) for idx in range(13)}
checks = [
    (0, "甘阳导言", "施特劳斯学派"),
    (1, "前言", "责任政府的政治哲学"),
    (2, "序言", "瓦尔格伦基金会"),
    (3, "重印序", "维柯"),
    (4, "导论", "独立宣言"),
    (5, "第一章", "以厉史的名义"),
    (6, "第二章", "历史主义的立场"),
    (7, "第三章", "起源"),
    (8, "第四章", "古典"),
    (9, "第五章", "现代"),
    (10, "第六章", "现代性的第一次危机"),
    (11, "索引", "卡尼亚德"),
    (12, "译后记", "何兆武"),
]
print("验证:", "  ".join(f"{'✓'+t if kw in ch[i] else '✗'+t+'!'}" for i, t, kw in checks))
# 目录页清零
print("目录页清零:", "✓" if "目" not in all_text or not re.search(r"目\s*录", all_text) else "✗")

# ---- toc ----
toc = [{"type": "chapter", "title": files[i]["title"], "index": i, "level": 1} for i in range(13)]
print(f"\ntoc 项: {len(toc)}")

if "--dry" in sys.argv:
    sys.exit(0)

# ---- 写入（旧 26 章自动数据 → 备份 _old_bad） ----
if os.path.isdir(SRC):
    suf = "_old_bad"
    i2 = 2
    while os.path.isdir(SRC + suf):
        suf = f"_old_bad{i2}"
        i2 += 1
    os.rename(SRC, SRC + suf)
    print(f"\n备份旧数据 → {os.path.basename(SRC) + suf}")
os.makedirs(SRC)
for idx in range(13):
    f = files[idx]
    json.dump({"index": idx, "title": f["title"], "content": f["content"]},
              open(os.path.join(SRC, f"{idx}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
meta = {
    "bookId": BID, "title": "自然权利与历史", "author": "列奥·施特劳斯",
    "toc": toc, "cover": None, "chapterCount": 13,
    "chapterTitles": [files[i]["title"] for i in range(13)],
}
json.dump(meta, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print(f"✓ 写入 {SRC}: 13 章 + meta.json")

shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
print("✓ 同步 DP backend chapters")
shutil.rmtree(DST2, ignore_errors=True)
shutil.copytree(SRC, DST2)
print("✓ 同步 DP app/public chapters（前端 dev 实际读取路径）")

for p in (DETAIL_SRC, DETAIL_DST):
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))
        d["toc"] = toc
        d["chapterCount"] = 13
        d["chapterTitles"] = meta["chapterTitles"]
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
        print(f"✓ book_detail 更新: {p}")

if os.path.exists(BOOKS_JSON):
    bj = json.load(open(BOOKS_JSON, encoding="utf-8"))
    bl = bj if isinstance(bj, list) else bj.get("books", [])
    hit = False
    for b in bl:
        if b.get("id") == BID:
            b["chapterCount"] = 13
            hit = True
    if hit:
        with open(BOOKS_JSON, "w", encoding="utf-8") as f:
            json.dump(bl if isinstance(bj, list) else {**bj, "books": bl}, f,
                      ensure_ascii=False, indent=None)
        print("✓ books.json chapterCount 更新")
    else:
        print("⚠ books.json 未找到该书")
