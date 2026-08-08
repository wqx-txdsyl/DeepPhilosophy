# -*- coding: utf-8 -*-
"""#254 自然宗教对话录（9c9e77918c07，大卫·休谟）重建
病因: OCR 完成的 20 本未入清单书之一。旧 3 章为 dp_pdf_import 自动切章
  （出版说明/第十二篇/第一篇——切章错乱，无页码清理）。
源: F:/philosophy/西方/大卫·休谟/自然宗教对话录.pdf（130 页扫描版，
  陈修斋/曹棉之译（商务印书馆 2017 汉译世界学术名著丛书 120 年纪念版），
  checkpoint OCR 130 页 fail 0）
结构（目录 p18；正文书内页码=PDF页-19；序言独立编页）:
  p0-3 封面/CIP/英文书名页（跳过）
  p4-5 出版说明（p4 标题块 3 行；p5 页首'出版说明'页眉）
  p6-17 中译本序言（p6 标题+正文同页；p17 尾署名'郑之骤曾文经 1961年6月'）
  p18 目录（跳过）
  p19-20 + p21 上半 潘斐留斯对赫米柏斯（书信；p19 页首标题行）
  p21 下半-32 第一篇 ｜ p33-46 第二篇 ｜ p46-52 第三篇
  p53-60 第四篇（p53 页首'第四篇'页眉+标题双行） ｜ p60-64 第五篇 ｜ p65-70 第六篇
  p71-76 第七篇 ｜ p77-82 第八篇 ｜ p83-88 第九篇
  p88-100 第十篇（p95 页眉'第干篇'OCR 变体） ｜ p100-112 第十一篇
  p112-128 第十二篇 ｜ p129 封底（跳过）
⚠ 篇标题嵌在正文流中（非独立标题页）: 每篇标题行出现在前篇结尾页页内
  （p21/p33/p46/p53/p60/p65/p71/p77/p83/p88/p100/p112），正文从标题行下一行
  续到下一页——章节边界必须行级切分（前段归前篇，后段归新篇）。
页码噪声: 书内页码在版心侧边，OCR 按列读成独立行（'1'/'12'/'128'，无装饰线），
  正则 ^[—\-一=\s]*\d{1,4}[—\-一=\s]*$ 任意位置剥整行
页眉: 序言奇页=书名'自然宗教对话录'、偶页='中译本序言'；正文奇页=篇名
  （'第一篇'..'第十二篇'）、偶页=书名；出版说明续页='出版说明'，
  页首第一行精确匹配剥离；OCR 变体 '第干篇'（p95）
标题: 章起始页标题（p4 三行标题块/p6 页首/p19 页首）精确剥离；
  篇标题行（'第X篇'/'第-五篇'）正则剥离并作为行级章边界
修复: 重建 15 章；段落: 每页过滤后行拼接为一段（OCR 书范式），
  跨篇页按标题行拆为前后两段。
用法: python _xr_9c9e77918c07_dialogues_rebuild.py [--dry]
"""
import json, os, re, sys, shutil, time

BID = "9c9e77918c07"
CKPT = r"f:\program\Python\PhiAgent\backend\data\dp_pdf_import_ckpt.json"
SAFE = "西方_大卫_休谟_自然宗教对话录.pdf"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
# ⚠ 2026-08-08 事故修正：前端本地 dev 读 app/public/backend/data/book_chapters，必须双写
DST2 = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

def norm(s):
    return re.sub(r"\s+", "", s or "")

# 15 章: (idx, 标题)
CH_TITLES = [
    "出版说明", "中译本序言", "潘斐留斯对赫米柏斯",
    "第一篇", "第二篇", "第三篇", "第四篇", "第五篇", "第六篇",
    "第七篇", "第八篇", "第九篇", "第十篇", "第十一篇", "第十二篇",
]
N = len(CH_TITLES)
SKIP_PAGES = set(range(0, 4)) | {18, 129}   # 封面/CIP + 目录 + 封底
# 页眉（页首第一行精确匹配，含 OCR 变体）
HEADERS = {
    "自然宗教对话录", "中译本序言", "出版说明",
    "第一篇", "第二篇", "第三篇", "第四篇", "第五篇", "第六篇",
    "第七篇", "第八篇", "第九篇", "第十篇", "第十一篇", "第十二篇",
    "第干篇",                                  # p95 OCR 变体（'一'→'干'）
}
# 页级章边界: 页首标题（HEADERS/STRIP 剥后）该页正文归新章
PAGE_START = {6: 1, 19: 2}       # 6 中译本序言（页首标题在 HEADERS）、19 书信（STRIP 剥）
# 章起始页标题块（按页顺序剥离；p53 页首'第四篇'页眉+标题双行——页眉由
# HEADERS 剥，标题行由篇标题正则剥）
STRIP_PAGES = {
    4: ["汉译世界学术名著丛书", "（120年纪念版·分科本）", "出版说明"],
    19: ["潘斐留斯对赫米柏斯"],   # 书信标题（非页眉）
}
# 篇标题行（页内任意位置；'第-五篇' OCR 变体）
TITLE_RE = re.compile(r"^第[-一]?[一二三四五六七八九十]{1,2}篇$")
# 页码行（书内页码，'1'/'12'/'128'，无装饰线）
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
    """页 → 净化行列表（剥页眉/页码/标题块；篇标题行保留作边界）"""
    t = npages.get(i, "")
    if not t:
        return []
    ls = [ln.strip() for ln in t.split("\n") if ln.strip()]
    if ls and ls[0] in HEADERS:
        ls = ls[1:]                        # 页眉
    if i in STRIP_PAGES:
        for h in STRIP_PAGES[i]:
            if ls and ls[0] == h:
                ls = ls[1:]
            else:
                cur = ls[0] if ls else "(空)"
                print(f"⚠ p{i} 期望标题 {h!r} 不匹配实际 {cur!r}")
                break
    ls = [l for l in ls if not PAGE_RE.match(l)]   # 页码行任意位置剥
    return ls

# ---- 行级章节切分（篇标题行 = 章边界） ----
paras = [[] for _ in range(N)]
cur = 0                                      # 当前章（0 出版说明）
for i in sorted(npages):
    if i < 4 or i in SKIP_PAGES:
        continue
    ls = page_lines(i)
    if not ls:
        continue
    if i in PAGE_START:
        cur = PAGE_START[i]                  # 页首标题章边界（标题已由 HEADERS/STRIP 剥）
    # 找篇标题行（每页至多一个；净化后 p53 只剩标题行）
    hit = [n for n, l in enumerate(ls) if TITLE_RE.match(l)]
    if hit:
        n = hit[-1]
        pre = "".join(ls[:n])
        if pre:
            paras[cur].append(pre)           # 标题行前 → 当前章
        cur += 1                             # 标题行 → 切到新章
        if cur >= N:
            print(f"⚠ p{i} 标题行超出章数: {ls[n]!r}")
            cur = N - 1
        post = "".join(ls[n + 1:])
        if post:
            paras[cur].append(post)          # 标题行后 → 新章
    else:
        paras[cur].append("".join(ls))

files = {}
for idx in range(N):
    if not paras[idx]:
        print(f"⚠ 章{idx} {CH_TITLES[idx]!r}: 无内容")
    files[idx] = {"index": idx, "title": CH_TITLES[idx],
                  "content": [{"type": "text", "value": p} for p in paras[idx]]}
    nc = sum(len(norm(p)) for p in paras[idx])
    first = paras[idx][0][:36] if paras[idx] else "(空)"
    last = paras[idx][-1][:22] if paras[idx] else ""
    print(f"[{idx}] {CH_TITLES[idx]:<22s} {nc:6d}字 {len(paras[idx]):3d}段 | {first!r} … {last!r}")
assert len(files) == N

# ---- 验证 ----
total = sum(sum(len(norm(b["value"])) for b in files[idx]["content"]) for idx in range(N))
print(f"\n新总净: {total}")
all_text = "".join(norm(b["value"]) for idx in range(N) for b in files[idx]["content"])
# 页码粘连清零: 段首不得以'汉字+2-3数字'粘连开头（学术注释中的书目页码保留段中/段尾）
bad_page = [norm(b["value"])[:8] for idx in range(N) for b in files[idx]["content"]
            if re.match(r"[一-鿿]\d{2,3}", norm(b["value"]))
            and not re.match(r"图\d{2,3}", norm(b["value"]))]
print("页码粘连清零:", "✓" if not bad_page else f"✗ {bad_page[:6]}")
# 独立页码行清零: 段不得整体为纯数字
bad_s = [norm(b["value"]) for idx in range(N) for b in files[idx]["content"]
         if re.match(r"^[—\-一=\s]*\d{1,4}[—\-一=\s]*$", norm(b["value"]))]
print("独立页码清零:", "✓" if not bad_s else f"✗ {bad_s[:5]}")
# 页眉/标题清零（篇标题行不得残留为段）
bad_h = [norm(b["value"])[:14] for idx in range(N) for b in files[idx]["content"]
         if TITLE_RE.match(norm(b["value"]))
         or norm(b["value"]) in {norm(h) for h in HEADERS}
         or norm(b["value"]) in {norm(x) for v in STRIP_PAGES.values() for x in v}]
print("标题清零:", "✓" if not bad_h else f"✗ {bad_h[:5]}")
# 关键内容验证
ch = {idx: "".join(norm(b["value"]) for b in files[idx]["content"]) for idx in range(N)}
checks = [
    (0, "出版说明", "商务印书馆"),
    (1, "序言", "柏克莱"),
    (2, "书信", "赫米柏斯"),
    (3, "第一篇", "克里安提斯"),
    (4, "第二篇", "造物主"),
    (5, "第三篇", "自明"),
    (6, "第四篇", "神秘"),
    (7, "第五篇", "杠杆"),
    (8, "第六篇", "世界的灵魂"),
    (9, "第七篇", "驼鸟"),
    (10, "第八篇", "物质"),
    (11, "第九篇", "必然"),
    (12, "第十篇", "痛苦"),
    (13, "第十一篇", "图拉真"),
    (14, "第十二篇", "宗教"),
]
print("验证:", "  ".join(f"{'✓'+t if kw in ch[i] else '✗'+t+'!'}" for i, t, kw in checks))
# 目录页清零（p18 已跳过；正文'灾祸的目录'等为正常用词，不做全文检查）

# ---- toc ----
toc = [{"type": "chapter", "title": files[i]["title"], "index": i, "level": 1} for i in range(N)]
print(f"\ntoc 项: {len(toc)}")

if "--dry" in sys.argv:
    sys.exit(0)

# ---- 写入（旧 3 章自动数据 → 备份 _old_bad） ----
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
    "bookId": BID, "title": "自然宗教对话录", "author": "大卫·休谟",
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
