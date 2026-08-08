# -*- coding: utf-8 -*-
"""悲剧的诞生 (尼采) 整本重导 (2026-08-08) — 整本单章(出版说明/66726字) 拆为 31 章
源: 85 页 OCR 缓存 (dp_pdf_import_ckpt.json, 已逐页核对)
结构: 出版说明(p2) + 中文版凡例(p2-3) + 一种自我批评的尝试(p4-9) + 序言(p9-10)
      + 正文 25 节(p10-71) + 科利版编后记(p71-73) + 译后记(p74-84) → 31 章
边界: 页+行级硬编码 (节标题 OCR 变形已逐页核对: 二='一/一' 十一='+一' 十七='++'
      十九='+九(1）' 二十='一十' 二十一='二+一(1)' 二十二='-+-')
      二十三/二十五标题 OCR 丢失, 以目录页码-1 起始 (p66/p70)
段落: 每页过滤后拼接为一段 (OCR 无空行, 页级段落最稳)
用法: python _rebuild_tragedy.py [--write]
"""
import sys, os, re, json, shutil
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"f:\program\Python\PhiAgent\backend\tools")
import rebuild_auto as ra

WRITE = "--write" in sys.argv
CKPT = r"f:\program\Python\PhiAgent\backend\data\dp_pdf_import_ckpt.json"
ckpt = json.load(open(CKPT, encoding="utf-8"))
pages = ckpt["ocr"]["西方_弗里德里希_尼采_悲剧的诞生.pdf"]
npages = {int(k): v for k, v in pages.items() if v and v != "__FAILED__"}
print(f"OCR 页: {min(npages)}-{max(npages)} 共{len(npages)}")

BOOKS = json.load(open(r"f:\program\Python\PhiAgent\app\public\books.json", encoding="utf-8"))
BID = next(b["id"] for b in BOOKS if b["title"] == "悲剧的诞生")
CH = ra.CH
D = os.path.join(CH, BID)
print("bid:", BID)

# ── 章节边界 (page, start_line, end_page, end_line) 半开区间, 行级精确 ──
# start_line = 正文起始行(跳过标题行); 标题行已核对
CHS = [
    ("汉译世界学术名著丛书 出版说明",       2, 10, 2, 20),
    ("中文版凡例",                         2, 21, 3, 6),
    ("一种自我批评的尝试",                 4,  9, 9, 36),   # p4 L7标题+L8编号跳过; p9 L36序言标题
    ("序言：致理查德·瓦格纳",              9, 38, 10, 17),  # p9 L36-37 标题残行跳过; p10 L17 一节标题
    ("一",                                10, 18, 13, 35),  # 标题 p10 L17 '一(1)'; p13 L33-34 二标题
    ("二",                                13, 35, 15, 14),  # 标题 p13 L33-34 '一/一'; p15 L14 三标题
    ("三",                                15, 15, 17, 18),  # 标题 p15 L14 '三'; p17 L18 四标题
    ("四",                                17, 19, 19, 32),  # 标题 p17 L18 '四（1）'
    ("五",                                19, 33, 22, 16),  # 标题 p19 L32 '五(1)'
    ("六",                                22, 17, 23, 42),  # 标题 p22 L16 '六'
    ("七",                                23, 43, 26, 31),  # 标题 p23 L42 '七(1)'
    ("八",                                26, 32, 29, 32),  # 标题 p26 L31 '八'
    ("九",                                29, 33, 32, 23),  # 标题 p29 L32 '九'
    ("十",                                32, 24, 34, 16),  # 标题 p32 L23 '十'
    ("十一",                               34, 17, 38, 0),  # 标题 p34 L16 '+一'; p38 L0 十二标题
    ("十二",                               38, 1, 41, 12),  # 标题 p38 L0 '十二'
    ("十三",                               41, 13, 42, 39), # 标题 p41 L12 '十三'
    ("十四",                               42, 40, 45, 4),  # 标题 p42 L39 '十四'
    ("十五",                               45, 5, 47, 38),  # 标题 p45 L4 '十五'
    ("十六",                               47, 39, 50, 34), # 标题 p47 L38 '十六'; p50 L34 十七标题
    ("十七",                               50, 35, 53, 12), # 标题 p50 L34 '++'
    ("十八",                               53, 13, 55, 19), # 标题 p53 L12 '十八'
    ("十九",                               55, 21, 59, 14), # 标题 p55 L19 '+九(1）' L20 'T儿'残行跳过
    ("二十",                               59, 15, 61, 1),  # 标题 p59 L14 '一十'
    ("二十一",                              61, 2, 64, 18),  # 标题 p61 L1 '二+一(1)'
    ("二十二",                              64, 19, 66, 0),  # 标题 p64 L18 '-+-'; p66 L0 二十三正文
    ("二十三",                              66, 0, 68, 30),  # 标题丢失, 目录 p67→OCR66; p68 L30 二十四标题
    ("二十四",                              68, 31, 70, 0),  # 标题 p68 L30 '二十四'
    ("二十五",                              70, 0, 71, 23),  # 标题丢失, 目录 p71→OCR70; p71 L23 编后记标题
    ("科利版编后记",                        71, 24, 74, 0),  # 标题 p71 L23 '科利版编后记（1）'
    ("译后记",                              74, 1, 82, 10**9),  # 标题 p74 L0 '译后记'; p83-84 目录碎片页不入库
]

# ── 提取各章 (页级段落: 每页 [lo_line, hi_line) 过滤后拼接为一段) ──
chapters = []
for title, lo_p, lo_l, hi_p, hi_l in CHS:
    paras = []
    for p in range(lo_p, hi_p + 1):
        t = npages.get(p, "")
        if not t:
            continue
        lines = t.split("\n")
        lo = lo_l if p == lo_p else 0
        hi = hi_l if p == hi_p else len(lines)
        seg = [ln.strip() for ln in lines[lo:hi] if ln.strip()]
        if seg:
            paras.append("".join(seg))
    chapters.append({"title": title, "paras": paras, "page": lo_p})
    n = sum(len(x) for x in paras)
    flag = "  !!空" if not paras else ""
    print(f"  {title[:30]:<32} p{lo_p}-{hi_p} 段{len(paras):<3} 字{n}{flag}")

# ── 校验 ──
print("\n=== 校验 ===")
for c in chapters:
    if not c["paras"]:
        print(f"  空章: {c['title']}")
        continue
    first, last = c["paras"][0], c["paras"][-1]
    if not re.match(r"^[\u4e00-\u9fff（§0-9《\"“]", first[:1]):
        print(f"  首段异常开头: [{c['title'][:16]}] {first[:30]}")
    if last and last[-1] not in "。！？；…\"”)]）】·}":
        print(f"  尾段无句末标点: [{c['title'][:16]}] …{last[-40:]}")

# ── 写入 ──
if WRITE:
    BAK = os.path.join(CH, "_rebuild_bak", f"{BID}_v1")
    os.makedirs(BAK, exist_ok=True)
    if not os.listdir(BAK):
        for f in sorted(os.listdir(D)):
            shutil.copy2(os.path.join(D, f), os.path.join(BAK, f))
    for f in os.listdir(D):
        if f.endswith(".json") and f != "meta.json":
            os.remove(os.path.join(D, f))
    meta = {"bookId": BID, "title": "悲剧的诞生", "author": "弗里德里希·尼采",
            "toc": [], "cover": None, "chapterCount": len(chapters), "chapterTitles": []}
    for i, c in enumerate(chapters):
        fp = os.path.join(D, f"{i}.json")
        content = [{"type": "text", "value": x} for x in c["paras"]]
        json.dump({"title": c["title"], "content": content, "index": i},
                  open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        meta["toc"].append({"type": "chapter", "title": c["title"], "index": i, "level": 1})
        meta["chapterTitles"].append(c["title"])
    json.dump(meta, open(os.path.join(D, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n写入完成: {len(chapters)} 章, toc {len(meta['toc'])} 条")
    ra.sync_three(BID)
    print("sync_three 完成")
