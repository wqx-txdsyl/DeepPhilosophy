# -*- coding: utf-8 -*-
"""S/Z 全本导入 (2026-08-08) — 空壳(books.json chapterCount=0)全量重建
源: 413 页 OCR 缓存 (dp_pdf_import_ckpt_sz.json, 独立 ckpt)
结构: 中译本导言(p4-43) + 写下阅读(p44-47) + 正文 93 章(p53-351) + 附录Ⅰ萨拉辛(p352-383)
      + 附录Ⅱ情节序列(p384-388) + 附录Ⅲ所思内容综览(p389-412) → 98 章 + 1 part
边界: 93 章起始页行级硬编码 (每章起始页 L0 为章标题, 已逐页核对, 目录 OCR 丢的五十一/七十八已补)
标题: 硬编码清单 (OCR 噪声已修: 意义的絮/杰作/洞见奥赜，精骛八极/遭打断的摹写)
页眉过滤: 纯页码 / 章名+页码粘连行(无标点+数字结尾) / 起始页标题行及其短续行
段落: 每页过滤后拼接为一段 (OCR 无空行, 页级段落最稳)
用法: python _rebuild_sz.py [--write]
"""
import sys, os, re, json, shutil
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"f:\program\Python\PhiAgent\backend\tools")
import rebuild_auto as ra

WRITE = "--write" in sys.argv
CKPT = r"f:\program\Python\PhiAgent\backend\data\dp_pdf_import_ckpt_sz.json"
ckpt = json.load(open(CKPT, encoding="utf-8"))
pages = ckpt["ocr"]["西方_罗兰_巴特_SZ.pdf"]
npages = {int(k): v for k, v in pages.items() if v and v != "__FAILED__"}
print(f"OCR 页: {min(npages)}-{max(npages)} 共{len(npages)}")

BOOKS = json.load(open(r"f:\program\Python\PhiAgent\app\public\books.json", encoding="utf-8"))
BID = next(b["id"] for b in BOOKS if b["title"] == "S/Z")
CH = ra.CH
D = os.path.join(CH, BID)
print("bid:", BID)

# ── 正文 93 章起始页 (已逐页核对) ──
STARTS = [53, 58, 61, 63, 66, 70, 72, 74, 75, 77, 82, 84, 87, 93, 96, 102, 105,
          108, 111, 114, 118, 126, 130, 134, 137, 139, 143, 146, 148, 151, 154,
          157, 159, 162, 164, 167, 171, 175, 177, 181, 184, 188, 192, 194, 198,
          200, 202, 203, 205, 208, 210, 213, 218, 222, 228, 231, 234, 238, 244,
          247, 250, 252, 256, 260, 263, 265, 267, 270, 274, 276, 279, 281, 287,
          289, 294, 297, 301, 305, 307, 310, 314, 321, 323, 325, 328, 331, 333,
          336, 339, 341, 344, 347, 350]
assert len(STARTS) == 93, f"起始页 {len(STARTS)} 个 != 93"

BODY = [
    "一、评估", "二、解释", "三、含蓄意指：反对意见", "四、虽如此，还是赞成含蓄意指",
    "五、阅读，遗忘", "六、步步渐进", "七、星形裂开的文", "八、碎散的文",
    "九、阅读多少遍？", "十、萨拉辛", "十一、五种符码", "十二、声音的编织",
    "十三、引逗", "十四、对照Ⅰ：增补", "十五、完美的乐谱", "十六、美",
    "十七、阉割阵营", "十八、阉歌手的后代", "十九、标志，符号，钱财",
    "二十、声音的叠化过程", "二十一、反讽，戏拟", "二十二、自然之极的情节",
    "二十三、模型源自绘画", "二十四、转换当游戏玩", "二十五、肖像描绘",
    "二十六、所指与真相", "二十七、对照Ⅱ：婚礼", "二十八、人物与形象",
    "二十九、雪花石膏灯", "三十、过与不及", "三十一、受扰的摹写", "三十二、拖延",
    "三十三、和/或", "三十四、意义的絮", "三十五、真实，可实行", "三十六、折叠，展开",
    "三十七、阐释句子", "三十八、契约—叙事", "三十九、这不是“文的解析”",
    "四十、主题学的诞生", "四十一、专有名称", "四十二、分类的符码", "四十三、文体转换",
    "四十四、历史人物", "四十五、贬低", "四十六、面面俱到", "四十七、S/Z",
    "四十八、尚未正式表述的谜", "四十九、噪音", "五十、重装的身体", "五十一、夸示",
    "五十二、杰作", "五十三、委婉说法", "五十四、洞见奥赜，精骛八极",
    "五十五、语言作自然力用", "五十六、树状结构", "五十七、趋向目标的线路",
    "五十八、故事的利益", "五十九、三类相纠合的符码", "六十、话语的决疑法",
    "六十一、自我陶醉的证据", "六十二、含混Ⅰ：双重理解", "六十三、心理学的证据",
    "六十四、读者的声音", "六十五、“争吵”", "六十六、能引人阅读者Ⅰ：“万殊一辙”",
    "六十七、狂欢如何创造出来", "六十八、编织物", "六十九、含混Ⅱ：换喻的假象",
    "七十、受阉割和阉割", "七十一、再追溯回去的吻", "七十二、审美的证据",
    "七十三、所指作结论用", "七十四、意义的控制", "七十五、爱的表白",
    "七十六、人物和话语", "七十七、能引人阅读者Ⅱ：被决定物/决定物", "七十八、死手无知",
    "七十九、阉割之前", "八十、结局和揭露过程", "八十一、个人的声音", "八十二、级进滑奏",
    "八十三、广泛流播的传染病", "八十四、文学的充满", "八十五、遭打断的摹写",
    "八十六、经验的声音", "八十七、科学的声音", "八十八、自雕塑至油画",
    "八十九、真相的声音", "九十、巴尔扎克式的文", "九十一、变更", "九十二、三处入口",
    "九十三、沉思的文",
]
assert len(BODY) == 93

# ── 章节清单: (title, start_page, end_page, extra_heads) 半开区间 ──
CHS = [("《S/Z》、《恩底弥翁的永睡》及倾听", 4, 44, ("—一《S/Z》中译本导言",)),
       ("写下阅读", 44, 48, ())]
CHS += [(t, STARTS[i], STARTS[i + 1] if i + 1 < 93 else 352, ()) for i, t in enumerate(BODY)]
CHS += [("附录Ⅰ 萨拉辛", 352, 384, ()),
        ("附录Ⅱ 情节序列", 384, 389, ()),
        ("附录Ⅲ 所思内容综览", 389, 413, ())]

# ── 页眉过滤 ──
PAGE_RE = re.compile(r"^\d{1,4}$")
HEAD_RE = re.compile(r"^[^。！？，；：、（）“”‘’【】《》·]{2,24}\d{1,4}$")  # 无标点文字+数字(章名+页码)
# S/Z 书眉粘连变体:
BOOKHEAD_RE = re.compile(r"^\d{1,4}[：:\s]*[0-9sS/\sIl|]*[zZ]?[\s]*$")   # 52S/Z / 90IS/Z / 226:S/ Z / 4 1 s/Z / 228|S/Z
ORD_RE = re.compile(r"^[一二三四五六七八九十]+、[^。！？]{1,24}\d{1,3}$")   # 五、阅读，遗岩17
BANG_RE = re.compile(r"^.{2,18}[！!：:]\d{1,4}$")                          # 叙事文渐进分析！81
APPX_RE = re.compile(r"^附录[ⅠI一二三]?[^。！？]{0,12}\d{0,4}$")           # 附录I萨拉辛1309 / 附录I萨拉辛

def clean_lines(i, title, extra=()):
    """p i 全部行, 过滤页眉/页码/章标题行及其短续行"""
    t = npages.get(i, "")
    if not t:
        return []
    lines = [ln.strip() for ln in t.split("\n")]
    out, prev_filtered = [], False
    for s in lines:
        if not s:
            prev_filtered = False
            continue
        if (PAGE_RE.match(s) or HEAD_RE.match(s) or BOOKHEAD_RE.match(s)
                or ORD_RE.match(s) or BANG_RE.match(s) or APPX_RE.match(s)
                or (extra and s in extra)):
            prev_filtered = True
            continue
        # 章标题行(起始页首行)及其短续行
        if (s == title or title.startswith(s + "、") or s.startswith(title)
                or (s and title.startswith(s) and len(s) >= 4)):
            prev_filtered = True
            continue
        if prev_filtered and len(s) < 5 and not re.search(r"[。！？，；]", s):
            prev_filtered = True   # 标题跨行续行(如 五十二、杰/作)
            continue
        prev_filtered = False
        out.append(s)
    return out

# ── 提取各章 (页级段落) ──
chapters = []
for title, lo, hi, extra in CHS:
    paras = []
    for p in range(lo, hi):
        lines = clean_lines(p, title, extra)
        if lines:
            paras.append("".join(lines))
    chapters.append({"title": title, "paras": paras, "page": lo})
    n = sum(len(x) for x in paras)
    flag = "  !!空" if not paras else ""
    print(f"  {title[:30]:<32} p{lo}-{hi - 1} 段{len(paras):<3} 字{n}{flag}")

# ── 校验 ──
print("\n=== 校验 ===")
for c in chapters:
    if not c["paras"]:
        print(f"  空章: {c['title']}")
        continue
    first, last = c["paras"][0], c["paras"][-1]
    if not re.match(r"^[\u4e00-\u9fff（§0-9《\"“一]", first[:1]):
        print(f"  首段异常开头: [{c['title'][:16]}] {first[:30]}")
    if last and last[-1] not in "。！？；…\"”)]）】·}":
        print(f"  尾段无句末标点: [{c['title'][:16]}] …{last[-40:]}")

# ── 写入 ──
if WRITE:
    BAK = os.path.join(CH, "_rebuild_bak", f"{BID}_v1")
    os.makedirs(BAK, exist_ok=True)
    if not os.listdir(BAK):
        if os.path.isdir(D):
            for f in sorted(os.listdir(D)):
                shutil.copy2(os.path.join(D, f), os.path.join(BAK, f))
    if os.path.isdir(D):
        for f in os.listdir(D):
            if f.endswith(".json") and f != "meta.json":
                os.remove(os.path.join(D, f))
    os.makedirs(D, exist_ok=True)
    meta = {"bookId": BID, "title": "S/Z", "author": "罗兰·巴特",
            "toc": [], "cover": None, "chapterCount": len(chapters), "chapterTitles": []}
    for i, c in enumerate(chapters):
        fp = os.path.join(D, f"{i}.json")
        content = [{"type": "text", "value": x} for x in c["paras"]]
        json.dump({"title": c["title"], "content": content, "index": i},
                  open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        meta["toc"].append({"type": "chapter", "title": c["title"], "index": i, "level": 1})
        meta["chapterTitles"].append(c["title"])
    # 附录 part 插在附录Ⅰ前 (index=95)
    meta["toc"].insert(95, {"type": "part", "title": "附录", "index": 95, "level": 0})
    json.dump(meta, open(os.path.join(D, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n写入完成: {len(chapters)} 章, toc {len(meta['toc'])} 条")
    ra.sync_three(BID)
    print("sync_three 完成")
