# -*- coding: utf-8 -*-
"""道家与道教思想简史 重建 v2 (2026-08-08): v1 的 section 扫描失败修复
方案: 行级节标题识别（原始页文本）→ 独立块; 句块按页+标点切分
"""
import sys, json, os, re, shutil
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"f:\program\Python\PhiAgent\backend\tools")
import rebuild_auto as ra

CKPT_FILE = r"f:\program\Python\PhiAgent\backend\data\dp_pdf_import_ckpt.json"
ck = json.load(open(CKPT_FILE, encoding="utf-8"))
pages = ck["ocr"]["东方_合集_概述_道家与道教思想简史.pdf"]
assert len(pages) == 279

BOUNDS = [
    (4,   "引言", "引言 道家思想的基本问题"),
    (13,  "一", "一 老子与中国哲学的突破"),
    (28,  "二", "二 出土文献所见道家思想"),
    (62,  "三", "三 杨朱庄周学派的人生哲学"),
    (85,  "四", "四 黄老哲学及其政治实践"),
    (115, "五", "五 黄老道家学说的变化"),
    (156, "六", "六 早期道教的神学观念"),
    (174, "七", "七 隋唐道教的重玄哲学"),
    (191, "八", "八 内丹派与全真道修炼理论"),
    (214, "九", "九 道教符箓派咒术思想"),
    (234, "十", "十 走向现代的新道家"),
    (269, "结束语", "结束语 道家的真精神"),
]
TAIL = 278
SKIP_RANGES = {4: [8, 12]}

# ── 节标题行匹配: "1杨朱学派的贵已重生说" / "2 庄子逍遥自由的人生观" / "3道教神学的中国特色" ──
SEC_RE = re.compile(r"^([1-4])\s*[·、]?\s*([^0-9。！？；：、\s][^。！？；：]{1,26})$")

def page_lines(k):
    t = pages.get(str(k)) or ""
    if t == "__FAILED__":
        return []
    return t.split("\n")

# ── 构建: 每章按页序处理, 页内行合并成段; 节标题行独立成块 ──
chapters = []
for idx, (ps, tag, title) in enumerate(BOUNDS):
    pe = BOUNDS[idx + 1][0] - 1 if idx + 1 < len(BOUNDS) else TAIL
    blocks = []       # (text, is_sec_title)
    buf = ""          # 行累积
    for k in range(ps, pe + 1):
        if tag in SKIP_RANGES and SKIP_RANGES[tag][0] <= k <= SKIP_RANGES[tag][1]:
            continue
        for line in page_lines(k):
            ls = line.strip()
            if not ls:
                continue
            m = SEC_RE.match(ls)
            if m:
                # 节标题: flush 累积 + 标题独立块
                if buf.strip():
                    blocks.append((buf.strip(), False))
                    buf = ""
                blocks.append((ls, True))
                continue
            # 普通行: 行末标点 → 段结束
            if ls[-1] in "。！？；：”』」）】…—-":
                if buf:
                    buf += ls
                    blocks.append((buf, False))
                    buf = ""
                else:
                    blocks.append((ls, False))
            else:
                buf += ls
    if buf.strip():
        blocks.append((buf.strip(), False))

    # 章首标题剥离: 首块若是章标题(如 p13 独立标题页) → 去掉
    title_key = re.sub(r"\s+", "", title.split(" ", 1)[-1])
    dw_first = re.sub(r"\s+", "", blocks[0][0]) if blocks else ""
    if dw_first.startswith(title_key):
        blocks = blocks[1:]
    elif blocks and re.sub(r"\s+", "", blocks[0][0]).startswith(re.sub(r"\s+", "", title)):
        blocks = blocks[1:]

    # 校验: 首块不应再是标题
    n = sum(len(b[0]) for b in blocks)
    chapters.append({"title": title, "tag": tag, "blocks": blocks, "ps": ps, "chars": n})

for c in chapters:
    print(f"  {c['tag']:<5} {c['title'][:20]:<24} 起p{c['ps']:<4} 字数{c['chars']:<7} 块{len(c['blocks'])}")
    assert c["chars"] > 300, f"{c['title']} 内容过短!"

# ── 写库 ──
BID = "219b862077e1"
BAK = os.path.join(ra.CH, "_rebuild_bak", f"{BID}_v1")
os.makedirs(BAK, exist_ok=True)
D = os.path.join(ra.CH, BID)
if os.path.isdir(D):
    for f in os.listdir(D):
        shutil.copy2(os.path.join(D, f), os.path.join(BAK, f))
os.makedirs(D, exist_ok=True)

meta = {"bookId": BID, "title": "道家与道教思想简史", "author": "王卡",
        "toc": [], "cover": None, "chapterCount": len(chapters), "chapterTitles": []}
for i, c in enumerate(chapters):
    fp = os.path.join(D, f"{i}.json")
    content = [{"type": "text", "value": b[0]} for b in c["blocks"]]
    json.dump({"title": c["title"], "content": content, "index": i}, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    meta["toc"].append({"type": "chapter", "title": c["title"], "index": i, "level": 1})
    for bi, (txt, is_sec) in enumerate(c["blocks"]):
        if is_sec:
            meta["toc"].append({"type": "section", "title": txt, "index": i, "sec": bi, "level": 2})
    meta["chapterTitles"].append(c["title"])
json.dump(meta, open(os.path.join(D, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"\n写入完成: {len(chapters)} 章")
for c in chapters:
    secs = [b[0] for b in c["blocks"] if b[1]]
    print(f"  {c['tag']}: {secs}")
ra.sync_three(BID)
print("sync_three 完成")
