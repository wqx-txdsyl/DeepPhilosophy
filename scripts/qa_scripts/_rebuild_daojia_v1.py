# -*- coding: utf-8 -*-
"""道家与道教思想简史 (东方_合集_概述) 重建 v1 (2026-08-08)
源: dp_pdf_import_ckpt.json 的 ocr 页级缓存 (279 页)
结构: 引言 + 一~十编 + 结束语 (13 章) + 章内小节 (section)
"""
import sys, json, os, re, shutil
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"f:\program\Python\PhiAgent\backend\tools")
import rebuild_auto as ra

CKPT_FILE = r"f:\program\Python\PhiAgent\backend\data\dp_pdf_import_ckpt.json"
ck = json.load(open(CKPT_FILE, encoding="utf-8"))
pages = ck["ocr"]["东方_合集_概述_道家与道教思想简史.pdf"]
assert len(pages) == 279, f"缓存页数异常: {len(pages)}"

# ── 13 章边界 (PDF 页序, 含起始页) ──
BOUNDS = [
    (4,   "引言", "引言 道家思想的基本问题"),
    (13,  "一", "一 老子与中国哲学的突破"),   # p13 是独立标题页(OCR 漏序号)
    (28,  "二", "二 出土文献所见道家思想"),
    (62,  "三", "三 杨朱庄周学派的人生哲学"),  # p62 OCR 误识别"二"
    (85,  "四", "四 黄老哲学及其政治实践"),
    (115, "五", "五 黄老道家学说的变化"),
    (156, "六", "六 早期道教的神学观念"),
    (174, "七", "七 隋唐道教的重玄哲学"),
    (191, "八", "八 内丹派与全真道修炼理论"),
    (214, "九", "九 道教符箓派咒术思想"),
    (234, "十", "十 走向现代的新道家"),
    (269, "结束语", "结束语 道家的真精神"),
]
TAIL = 278  # p278 图书信息尾巴并入结束语

def page_text(k):
    t = pages.get(str(k)) or ""
    if t == "__FAILED__":
        return ""
    return t

SKIP_RANGES = {4: [8, 12]}  # 引言章跳过 p8-12 目录区

def join_pages(start, end, ch_tag=None):
    """页拼接: 页末无标点 → 直拼(行内断行); 否则段落分隔"""
    full = ""
    for k in range(start, end + 1):
        if ch_tag in SKIP_RANGES and SKIP_RANGES[ch_tag][0] <= k <= SKIP_RANGES[ch_tag][1]:
            continue
        t = page_text(k).rstrip()
        if not t:
            full += "\n\n"
            continue
        if full and full[-1] in "。！？；：”』」）】…—-":
            full += "\n\n" + t
        else:
            full += t
    return full

def strip_ch_title(text, title_words):
    """章首标题剥离: 剥离 '三' + '杨朱庄周学派的人生哲学' 等标题前缀"""
    dw = re.sub(r"\s+", "", text)
    t0 = dw[:30]
    # 标题可能是 "三杨朱庄周学派的人生哲学1杨朱..." 或 "三\n杨朱...\n1..."
    for w in title_words:
        i = dw.find(w)
        if 0 <= i <= 6:
            return dw[i + len(w):], True
    return text, False

def to_blocks(full):
    """段落化: 按空行分段"""
    paras = [p.strip() for p in full.split("\n\n") if p.strip()]
    # 页内 \n 行合并（OCR 行断）
    merged = []
    for p in paras:
        merged.append(re.sub(r"\n+", "", p))
    return merged

def find_sections(blocks, start_idx=1):
    """章内小节: '1标题' / '2 标题' 独立段 → (sec_title, block_index)"""
    secs = []
    for i, p in enumerate(blocks):
        m = re.match(r"^([1-9])\s*[·、]?\s*([^。！？；]{2,24})$", p)
        if m and not re.search(r"[A-Za-z]{4,}", p):
            secs.append((m.group(2), i))
    # 去重: 连续两个小节标题中间内容 <3 段视为孤立标题
    return secs

# ── 备份 ──
BID = "219b862077e1"  # 壳子真实 id
BAK = os.path.join(ra.CH, "_rebuild_bak", f"{BID}_v1")
os.makedirs(BAK, exist_ok=True)
D = os.path.join(ra.CH, BID)
if os.path.isdir(D):
    for f in os.listdir(D):
        shutil.copy2(os.path.join(D, f), os.path.join(BAK, f))
os.makedirs(D, exist_ok=True)

# ── 逐章构建 ──
chapters = []
for idx, (ps, tag, title) in enumerate(BOUNDS):
    pe = BOUNDS[idx + 1][0] - 1 if idx + 1 < len(BOUNDS) else TAIL
    full = join_pages(ps, pe, tag)
    # 章首标题剥离
    title_words = [re.sub(r"\s+", "", title)]
    for w in title_words:
        pass
    dw_full = re.sub(r"\s+", "", full)
    i = dw_full.find(re.sub(r"\s+", "", title).split(" ", 1)[-1] if " " in title else title)
    # 更稳: 剥离 "数字/引言/结束语" 前缀 + 标题词
    m = re.match(r"^([引言一二三四五六七八九十结束语]{1,4}|[序言]+)", dw_full[:8])
    cut = None
    # key 用去序号标题（OCR 序号不可靠, 如"三"被识别为"二"）
    for key in [re.sub(r"\s+", "", title.split(" ", 1)[-1]), re.sub(r"\s+", "", title)]:
        j = dw_full.find(key)
        if j != -1 and j <= 10:
            cut = j + len(key)
            break
    if cut is None:
        # 未剥离: 标题可能在独立页(如 p13 只有标题行) → 跳过标题行
        lines = full.split("\n")
        if len(lines) <= 3 and len(dw_full) < 30:
            cut = len(dw_full)
        else:
            cut = 0
    rest = dw_full[cut:]
    # 段落化: 无空行信息, 按句读分块 (每 200 字左右)
    blocks = []
    buf = ""
    for ch in rest:
        buf += ch
        if ch in "。！？；" and len(buf) >= 60:
            blocks.append(buf)
            buf = ""
    if buf.strip():
        blocks.append(buf)
    chapters.append({"title": title, "tag": tag, "blocks": blocks, "ps": ps})

# 校验内容非空
for c in chapters:
    n = sum(len(b) for b in c["blocks"])
    print(f"  {c['tag']:<5} {c['title'][:20]:<24} 起p{c['ps']:<4} 字数{n}")
    assert n > 300, f"{c['title']} 内容过短!"

# ── section 扫描 (基于句块, 弱规则: 独立短块) ──
for c in chapters:
    secs = []
    for i, b in enumerate(c["blocks"]):
        if 2 <= len(b) <= 30 and re.match(r"^[1-9]", b) and not re.search(r"[，。！？：]", b):
            secs.append({"title": b, "block": i})
    c["secs"] = secs

# ── 写库 ──
meta = {"bookId": BID, "title": "道家与道教思想简史", "author": "王卡",
        "toc": [], "cover": None, "chapterCount": len(chapters), "chapterTitles": []}
for i, c in enumerate(chapters):
    fp = os.path.join(D, f"{i}.json")
    content = [{"type": "text", "value": b} for b in c["blocks"]]
    json.dump({"title": c["title"], "content": content, "index": i}, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    meta["toc"].append({"type": "chapter", "title": c["title"], "index": i, "level": 1})
    for s in c["secs"]:
        meta["toc"].append({"type": "section", "title": s["title"], "index": i, "sec": s["block"], "level": 2})
    meta["chapterTitles"].append(c["title"])
json.dump(meta, open(os.path.join(D, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"\n写入完成: {len(chapters)} 章, section {sum(len(c['secs']) for c in chapters)} 个")
for c in chapters:
    print(f"  {c['tag']}: section {[s['title'] for s in c['secs']]}")
ra.sync_three(BID)
print("sync_three 完成")
