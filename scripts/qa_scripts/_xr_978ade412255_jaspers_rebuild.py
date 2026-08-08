# -*- coding: utf-8 -*-
"""#255 雅斯贝尔斯传（978ade412255，汉斯·萨内尔）重建
病因: OCR 完成的 20 本未入清单书之一。旧 1 章为 dp_pdf_import 自动切章
  （强模式标题无命中→整本粗切，toc 标题乱取）。
源: F:/philosophy/西方/卡尔·雅斯贝尔斯/雅斯贝尔斯传.pdf（195 页扫描版，
  Hans Saner 著（Rowohlt 版），商务印书馆世界名人传记丛书 2012，
  checkpoint OCR 195 页 fail 0）
结构（目录 p6-7，书内页码=PDF页-7）:
  一生活部: 1.童年/2.学习/3.最初的成就/4.通向哲学之路/5.成熟的年代/
    6.日耳曼的结局/7.错失了转机/8.逍遥的隐士生活/9.综观一生
  二思想部: 1.心灵的界限：心理病理学与心理学/2.思想家的王国：哲学史/
    3.思维的广度：逻辑/4.生存的结构：生存哲学/5.对世界的关注：世界哲学/
    6.思想的发展
  三形象部: 1.人/2.研究者、教师、教育家/3.著述家/4.同时代人/5.哲学家
  尾: 雅斯贝尔斯生平及著作年表 p189-191 / 再版后记 p192-193
  p0-4 封面/CIP/版权/内容提要（跳过）｜ p5 新版说明（保留章0）
  p6-7 目录（跳过）｜ p8 一生活部标题页（部标题+引言+节1标题+正文同页）
  p76 二思想部标题页（同构）｜ p138 三形象部标题页（同构）｜ p194 封底（跳过）
页码噪声: 书内页码在页内任意位置（'11'/'70'，无装饰线），
  正则 ^[—\-一=\s]*\d{1,4}[—\-一=\s]*$ 任意位置剥整行
页眉: 偶页=节名（'1.童年'..'5.哲学家'）、奇页=部名（'一生活'/'二思想'/'三形象'），
  页首第一行精确匹配剥离；OCR 变体 5 种（'—生活'/'6—生活'/'生活'/'国1.童年'/
  '2.思想家的王国：哲学史」'/'3.思维的广度；逻辑'）
标题: 部标题页页内节标题（p8 '1.童年'/p76 '1.心灵的界限…'/p138 '1.人'）按页精确剥离；
  节起始页页首节名由 HEADERS 统一剥（标题=页眉同字符串）
修复: 重建 23 章；段落: 每页过滤后行拼接为一段（OCR 书范式）。
用法: python _xr_978ade412255_jaspers_rebuild.py [--dry]
"""
import json, os, re, sys, shutil, time

BID = "978ade412255"
CKPT = r"f:\program\Python\PhiAgent\backend\data\dp_pdf_import_ckpt.json"
SAFE = "西方_卡尔_雅斯贝尔斯_雅斯贝尔斯传.pdf"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
# ⚠ 2026-08-08 事故修正：前端本地 dev 读 app/public/backend/data/book_chapters，必须双写
DST2 = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

def norm(s):
    return re.sub(r"\s+", "", s or "")

# 23 章: (idx, 标题, 起始页, 结束页) — PDF 页
CH = [
    (0, "新版说明", 5, 5),
    (1, "1.童年", 8, 17),
    (2, "2.学习", 18, 23),
    (3, "3.最初的成就", 24, 29),
    (4, "4.通向哲学之路", 30, 37),
    (5, "5.成熟的年代", 38, 45),
    (6, "6.日耳曼的结局", 46, 55),
    (7, "7.错失了转机", 56, 63),
    (8, "8.逍遥的隐士生活", 64, 73),
    (9, "9.综观一生", 74, 75),
    (10, "1.心灵的界限：心理病理学与心理学", 76, 87),
    (11, "2.思想家的王国：哲学史", 88, 95),
    (12, "3.思维的广度：逻辑", 96, 111),
    (13, "4.生存的结构：生存哲学", 112, 123),
    (14, "5.对世界的关注：世界哲学", 124, 131),
    (15, "6.思想的发展", 132, 137),
    (16, "1.人", 138, 147),
    (17, "2.研究者、教师、教育家", 148, 155),
    (18, "3.著述家", 156, 161),
    (19, "4.同时代人", 162, 179),
    (20, "5.哲学家", 180, 188),
    (21, "雅斯贝尔斯生平及著作年表", 189, 191),
    (22, "再版后记", 192, 193),
]
N = len(CH)
SKIP_PAGES = set(range(0, 5)) | {6, 7, 194}   # 封面/CIP/版权/提要 + 目录 + 封底
# 页眉（页首第一行精确匹配，含 OCR 变体）
HEADERS = {
    "新版说明",
    "一生活", "二思想", "三形象",
    "—生活", "6—生活", "生活",                 # 部名 OCR 变体
    "1.童年", "2.学习", "3.最初的成就", "4.通向哲学之路", "5.成熟的年代",
    "6.日耳曼的结局", "7.错失了转机", "8.逍遥的隐士生活", "9.综观一生",
    "1.心灵的界限：心理病理学与心理学", "2.思想家的王国：哲学史",
    "3.思维的广度：逻辑", "4.生存的结构：生存哲学", "5.对世界的关注：世界哲学",
    "6.思想的发展",
    "1.人", "2.研究者、教师、教育家", "3.著述家", "4.同时代人", "5.哲学家",
    "国1.童年",                                 # p14 变体（'1.童年' 前粘字）
    "2.思想家的王国：哲学史」", "3.思维的广度；逻辑",  # OCR 变体（p92/p106）
    "雅斯贝尔斯生平及著作年表", "再版后记",
}
# 页内标题行（任意行精确匹配剔除；部标题页=部名+引言+节标题+正文同页）
STRIP_PAGES = {
    5: ["世界名人传记丛书", "新版说明"],       # p5 系列名+标题双行
    8: ["1.童年"],
    74: ["9.综观一生", "嘉9.综观一生"],        # p74 页首标题+引言+页内节标题（'嘉'OCR残）
    76: ["1.心灵的界限：心理病理学与心理学"],
    138: ["1.人"],
}
# 页码行（书内页码，'11'/'70'，无装饰线）
PAGE_RE = re.compile(r"^[—\-一=\s]*\d{1,4}[—\-一=\s]*$")

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
    """页 → 行（剥页眉/标题/页码噪声后）"""
    t = npages.get(i, "")
    if not t:
        return []
    ls = [ln.strip() for ln in t.split("\n") if ln.strip()]
    if ls and ls[0] in HEADERS:
        ls = ls[1:]                        # 页眉
    if i in STRIP_PAGES:
        ls = [l for l in ls if l not in STRIP_PAGES[i]]   # 页内标题行任意位置剔除
    ls = [l for l in ls if not PAGE_RE.match(l)]   # 页码行任意位置剥
    return ls

# ---- 逐章解析（页级段落范式） ----
files = {}
for idx, title, p0, p1 in CH:
    paras = []
    for i in range(p0, p1 + 1):
        if i in SKIP_PAGES:
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
assert len(files) == N

# ---- 验证 ----
total = sum(sum(len(norm(b["value"])) for b in files[idx]["content"]) for idx in range(N))
print(f"\n新总净: {total}")
all_text = "".join(norm(b["value"]) for idx in range(N) for b in files[idx]["content"])
# 页码粘连清零: 段首不得以'汉字+2-3数字'粘连开头（学术注释中的书目页码保留段中/段尾）
bad_page = [norm(b["value"])[:8] for idx in range(N) for b in files[idx]["content"]
            if re.match(r"[一-鿿]\d{2,3}", norm(b["value"]))
            and not re.match(r"图\d{2,3}", norm(b["value"]))
            and not re.search(r"\d{2,3}岁", norm(b["value"]))]   # '60岁寿辰' 为年龄正文
print("页码粘连清零:", "✓" if not bad_page else f"✗ {bad_page[:6]}")
# 独立页码行清零: 段不得整体为纯数字
bad_s = [norm(b["value"]) for idx in range(N) for b in files[idx]["content"]
         if re.match(r"^[—\-一=\s]*\d{1,4}[—\-一=\s]*$", norm(b["value"]))]
print("独立页码清零:", "✓" if not bad_s else f"✗ {bad_s[:5]}")
# 页眉/标题清零
bad_h = [norm(b["value"])[:14] for idx in range(N) for b in files[idx]["content"]
         if norm(b["value"]) in {norm(h) for h in HEADERS} | {norm(x) for v in STRIP_PAGES.values() for x in v}]
print("标题清零:", "✓" if not bad_h else f"✗ {bad_h[:5]}")
# 关键内容验证
ch = {idx: "".join(norm(b["value"]) for b in files[idx]["content"]) for idx in range(N)}
checks = [
    (0, "新版说明", "传记"),
    (1, "童年", "奥尔登堡"),
    (2, "学习", "叔本华"),
    (3, "最初的成就", "成就"),
    (4, "通向哲学之路", "海德堡"),
    (5, "成熟的年代", "成熟"),
    (6, "日耳曼的结局", "纳粹"),
    (7, "错失了转机", "转机"),
    (8, "隐士生活", "隐士"),
    (9, "综观一生", "综观"),
    (10, "心灵的界限", "心理病理学"),
    (11, "思想家的王国", "哲学史"),
    (12, "思维的广度", "逻辑"),
    (13, "生存的结构", "生存哲学"),
    (14, "对世界的关注", "世界哲学"),
    (15, "思想的发展", "发展"),
    (16, "人", "形象"),
    (17, "研究者", "教师"),
    (18, "著述家", "著述"),
    (19, "同时代人", "同时代"),
    (20, "哲学家", "哲学家"),
    (21, "年表", "1969年"),
    (22, "再版后记", "杭州"),
]
print("验证:", "  ".join(f"{'✓'+t if kw in ch[i] else '✗'+t+'!'}" for i, t, kw in checks))

# ---- toc ----
toc = [{"type": "chapter", "title": files[i]["title"], "index": i, "level": 1} for i in range(N)]
print(f"\ntoc 项: {len(toc)}")

if "--dry" in sys.argv:
    sys.exit(0)

# ---- 写入（旧 1 章自动数据 → 备份 _old_bad） ----
if os.path.isdir(SRC):
    suf = "_old_bad"
    i2 = 2
    while os.path.isdir(SRC + suf):
        suf = f"_old_bad{i2}"
        i2 += 1
    os.rename(SRC, SRC + suf)
    print(f"\n备份旧数据 → {os.path.basename(SRC) + suf}")
os.makedirs(SRC)
for idx in range(N):
    f = files[idx]
    json.dump({"index": idx, "title": f["title"], "content": f["content"]},
              open(os.path.join(SRC, f"{idx}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
meta = {
    "bookId": BID, "title": "雅斯贝尔斯传", "author": "汉斯·萨内尔",
    "toc": toc, "cover": None, "chapterCount": N,
    "chapterTitles": [files[i]["title"] for i in range(N)],
}
json.dump(meta, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print(f"✓ 写入 {SRC}: {N} 章 + meta.json")

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
        d["chapterCount"] = N
        d["chapterTitles"] = meta["chapterTitles"]
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
        print(f"✓ book_detail 更新: {p}")

if os.path.exists(BOOKS_JSON):
    bj = json.load(open(BOOKS_JSON, encoding="utf-8"))
    bl = bj if isinstance(bj, list) else bj.get("books", [])
    hit = False
    for b in bl:
        if b.get("id") == BID:
            b["chapterCount"] = N
            hit = True
    if hit:
        with open(BOOKS_JSON, "w", encoding="utf-8") as f:
            json.dump(bl if isinstance(bj, list) else {**bj, "books": bl}, f,
                      ensure_ascii=False, indent=None)
        print("✓ books.json chapterCount 更新")
    else:
        print("⚠ books.json 未找到该书")
