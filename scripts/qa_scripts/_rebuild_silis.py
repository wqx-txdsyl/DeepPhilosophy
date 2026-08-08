# -*- coding: utf-8 -*-
"""西利斯 全本重导 (2026-08-08) — 目录串章/注释串章/正文缺失修复
源: 293 页 OCR 缓存 (dp_pdf_import_ckpt.json), p232 已重 OCR 补全
结构: 译者导言(p11-39) + 作者导言(p40) + 正文 15 章(§1-368) + 附录 5 篇 → 22 章 + 1 part
边界: § 起始行行级硬编码 (OCR 中 § 号变形: 81=§1 / S2=§2 / 59=§9 / 86=§6 已逐页核对)
  正文各章起止 = 下一章 § 起始行之前 (半开区间, 行级切分)
  附录: 第一封信 p233-245 / 第二封 p246-256 / 第三封 p257-269 / 黑尔斯 p270-272 / 进一步思考 p273-291
页眉过滤: 书名整行 / 纯页码 / 作者导言标题行(并入导言章不滤)
段落: 每页过滤后拼接为一段 (OCR 无空行, 页级段落最稳, 同尼各马可)
用法: python _rebuild_silis.py [--write]
"""
import sys, os, re, json, shutil
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"f:\program\Python\PhiAgent\backend\tools")
import rebuild_auto as ra

WRITE = "--write" in sys.argv
CKPT = r"f:\program\Python\PhiAgent\backend\data\dp_pdf_import_ckpt.json"
ckpt = json.load(open(CKPT, encoding="utf-8"))
pages = ckpt["ocr"]["西方_乔治_贝克莱_西利斯.pdf"]
npages = {int(k): v for k, v in pages.items() if v and v != "__FAILED__"}
print(f"OCR 页: {min(npages)}-{max(npages)} 共{len(npages)}")

BOOKS = json.load(open(r"f:\program\Python\PhiAgent\app\public\books.json", encoding="utf-8"))
BID = next(b["id"] for b in BOOKS if b["title"] == "西利斯")
CH = ra.CH
D = os.path.join(CH, BID)
print("bid:", BID)

# ── 章节边界 (page, line_idx) 半开区间; 行级精确切分 (已逐页核对 § 变形) ──
APPENDIX = ("附录", None)
CHS = [
    ("译者导言",                                 11,   0,  40,  0),
    ("作者导言",                                 40,   0,  40, 16),   # §1 在 p40 line16
    ("第一章（§1—§9）焦油水及其制作与疗效",        40,  16,  44, 18),   # §10 在 p44 line18
    ("第二章（§10—§28）焦油、松脂与精气",         44,  18,  53,  1),   # §29 在 p53 line1
    ("第三章（§29—§45）化学与物体分析",           53,   1,  60,  2),   # §46 在 p60 line2
    ("第四章（§46—§119）精气、空气与植物",        60,   2,  93, 17),   # §120 在 p93 line17
    ("第五章（§120—§136）酸、盐与精气",           93,  17, 100, 11),   # §137 在 p100 line11
    ("第六章（§137—§151）空气与天然精气",        100,  11, 106, 13),   # §152 在 p106 line13
    ("第七章（§152—§219）以太、火与微粒",        106,  13, 140,  9),   # §220 在 p140 line9
    ("第八章（§220—§250）动力、吸引与力学",      140,   9, 159, 11),   # §251 在 p159 line11
    ("第九章（§251—§264）机械论与现象",          159,  11, 168,  8),   # §265 在 p168 line8
    ("第十章（§265—§286）古人的智慧",            168,   8, 183,  0),   # §287 在 p183 line0
    ("第十一章（§287—§297）万物一体",             183,   0, 189, 17),   # §298 在 p189 line17
    ("第十二章（§298—§302）心灵及其活动",        189,  17, 193,  0),   # §303 在 p193 line0
    ("第十三章（§303—§319）感觉与和谐",          193,   0, 205,  4),   # §320 在 p205 line4
    ("第十四章（§320—§332）上帝与第一因",        205,   4, 212,  8),   # §333 在 p212 line8
    ("第十五章（§333—§368）柏拉图学派与灵魂",    212,   8, 233,  0),   # 附录在 p233
    ("致T.普赖尔先生的第一封信",                 233,   0, 246,  0),
    ("致T.普赖尔先生的第二封信",                 246,   0, 257,  0),
    ("致T.普赖尔先生的第三封信",                 257,   0, 270,  0),
    ("致黑尔斯博士的信",                         270,   0, 273,  0),
    ("对焦油水的进一步思考",                     273,   0, 292,  0),   # p292 版权页不入库
]

# ── 页眉过滤 ──
PAGE_RE = re.compile(r"^\d{1,4}$")
BOOK_HEAD = "西利斯：哲学反思和探讨之链"   # 书名页眉 (仅 p40 序言页出现)

def clean_lines(i, lo_line, hi_line):
    """p i 的 [lo_line, hi_line) 行, 过滤页眉后返回"""
    t = npages.get(i, "")
    if not t:
        return []
    lines = t.split("\n")
    out = []
    for ln in lines[lo_line:hi_line]:
        s = ln.strip()
        if not s:
            continue
        if s == BOOK_HEAD:
            continue
        if PAGE_RE.match(s):
            continue
        out.append(s)
    return out

# ── 提取各章 (页级段落: 每页过滤后拼接为一段) ──
chapters = []
for title, lo_p, lo_l, hi_p, hi_l in CHS:
    paras = []
    for p in range(lo_p, hi_p + 1):
        lo = lo_l if p == lo_p else 0
        hi = hi_l if p == hi_p else 10 ** 9
        lines = clean_lines(p, lo, hi)
        if lines:
            paras.append("".join(lines))
    chapters.append({"title": title, "paras": paras, "page": lo_p})
    n = sum(len(x) for x in paras)
    flag = "  !!空" if not paras else ""
    print(f"  {title[:32]:<34} p{lo_p}-{hi_p} 段{len(paras):<3} 字{n}{flag}")

# ── 校验 ──
print("\n=== 校验 ===")
for c in chapters:
    if not c["paras"]:
        print(f"  空章: {c['title']}")
        continue
    first, last = c["paras"][0], c["paras"][-1]
    if not re.match(r"^[\u4e00-\u9fff（§0-9《\"“]", first[:1]):
        print(f"  首段异常开头: [{c['title'][:18]}] {first[:30]}")
    if last and last[-1] not in "。！？；…\"”)]·":
        print(f"  尾段无句末标点: [{c['title'][:18]}] …{last[-40:]}")

# ── 写入 ──
if WRITE:
    BAK = os.path.join(CH, "_rebuild_bak", f"{BID}_v1")
    os.makedirs(BAK, exist_ok=True)
    if not os.listdir(BAK):  # 仅首次备份, 防止覆盖已备份的原库
        for f in sorted(os.listdir(D)):
            shutil.copy2(os.path.join(D, f), os.path.join(BAK, f))
    # 清理旧文件 (教训: 尼各马可残留 12-27.json 导致链不连续)
    for f in os.listdir(D):
        if f.endswith(".json") and f != "meta.json":
            os.remove(os.path.join(D, f))
    meta = {"bookId": BID, "title": "西利斯", "author": "乔治·贝克莱",
            "toc": [], "cover": None, "chapterCount": len(chapters), "chapterTitles": []}
    for i, c in enumerate(chapters):
        fp = os.path.join(D, f"{i}.json")
        content = [{"type": "text", "value": x} for x in c["paras"]]
        json.dump({"title": c["title"], "content": content, "index": i},
                  open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        meta["toc"].append({"type": "chapter", "title": c["title"], "index": i, "level": 1})
        meta["chapterTitles"].append(c["title"])
    # 附录 part 插在附录第一封信前 (index=17)
    meta["toc"].insert(17, {"type": "part", "title": "附录", "index": 17, "level": 0})
    json.dump(meta, open(os.path.join(D, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n写入完成: {len(chapters)} 章, toc {len(meta['toc'])} 条")
    ra.sync_three(BID)
    print("sync_three 完成")
