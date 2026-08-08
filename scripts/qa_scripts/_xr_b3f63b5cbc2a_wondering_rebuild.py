# -*- coding: utf-8 -*-
"""#262 像哲学家一样思考（b3f63b5cbc2a，[美]詹姆斯·克里斯蒂安）重建
病因: 已OCR未入清单补录书。旧 12 章为 dp_pdf_import 自动切章——0-7 章是目录页碎片
  （每章百来字），8-9 章半碎片，10/11 章吞掉全部正文（66K+176K）。
源: F:/philosophy/西方/合集&概述/像哲学家一样思考.pdf（357 页简体横排扫描版，
  北京大学出版社 2015 第11版，赫忠慧译，checkpoint OCR 357 页 fail 0）
结构（书内页码=PDF页-13）:
  p0-2 封面/CIP（跳过）｜ p3 卷首引文（柏拉图《泰阿泰德篇》，跳过）
  p4-8 前言：你说的哲学是什么意思（书内8-12）
  p9-13 简明目录/下册目录/上册目录（跳过）
  第一部分 完美的惊疑艺术（扉页 p14）: 1-1世界之谜 p15-38 / 1-2探究精神 p39-58 /
    1-3批判分析 p59-87 / 1-4全景整合 p88-107
  第二部分 处境与奥德赛（扉页 p108）: 2-1困境 p109-127 / 2-2自我 p128-148 /
    2-3成长 p149-171 / 2-4生命/时间 p172-201
  第三部分 真实的世界：已知的和未知的（扉页 p202）: 3-1知识 p203-218 /
    3-2感官 p219-237 / 3-3心灵 p238-256 / 3-4真理 p257-271
  第四部分 精神世界的奇幻历程（扉页 p272）: 4-1精神 p273-291 / 4-2时间 p292-317 /
    4-3自由 p318-335 / 4-4符号 p336-355
  p356 封底广告（跳过）｜ PDF 只含上册（第五-八部分在下册，源缺失）
页眉: 尾行 'N像哲学家一样思考'（页码+书名粘连，'334像哲学家一样思考'/'8像哲学家一样思考'）；
  p172 尾行 '2-4生命/时间'+'159'（节名页眉+页码）
页码: 独立数字行任意位置剥（'4'/'7'/'13'/'20'/'159' 等）；正文序号'1每一个单独的生命'不剥
节标题页: 首行节号（'1-1'/'3-1知识'粘连）+ 次行节名（∈CH_TITLES）剥
部分扉页: 4 页整页剥（节列表+部分名 OCR 乱）
小节标题: 页首纯汉字短行（≤8字 无句读，含引号/省略号）独立成段
  （'苏格拉底'/'人生拼图'/'自我'/'世界是一个舞台…···' 等；'1-1'/'THE'/'2请…。'不切）
修复: 重建 17 章 + toc 4 part（level 0，index=首章）两级结构；段落: 页级拼接 +
  页首短标题独立段。作者修正: '合集&概述'占位 → 詹姆斯·克里斯蒂安（封面页实名）。
用法: python _xr_b3f63b5cbc2a_wondering_rebuild.py [--dry]
"""
import json, os, re, sys, shutil, time

BID = "b3f63b5cbc2a"
CKPT = r"f:\program\Python\PhiAgent\backend\data\dp_pdf_import_ckpt.json"
SAFE = "西方_合集_概述_像哲学家一样思考.pdf"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
# ⚠ 2026-08-08 事故修正：前端本地 dev 读 app/public/backend/data/book_chapters，必须双写
DST2 = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"
AUTHOR = "詹姆斯·克里斯蒂安"

def norm(s):
    return re.sub(r"\s+", "", s or "")

# 17 章
CH_TITLES = [
    "前言 你说的哲学是什么意思",
    "1-1 世界之谜", "1-2 探究精神", "1-3 批判分析", "1-4 全景整合",
    "2-1 困境", "2-2 自我", "2-3 成长", "2-4 生命/时间",
    "3-1 知识", "3-2 感官", "3-3 心灵", "3-4 真理",
    "4-1 精神", "4-2 时间", "4-3 自由", "4-4 符号",
]
N = len(CH_TITLES)
SEC_NAMES = {t.split(" ", 1)[1] for t in CH_TITLES[1:]}  # 节名集合（剥节名行用）
# 4 部分（toc 的 part 项; index=部分首章）
PARTS = [
    ("第一部分 完美的惊疑艺术", 1), ("第二部分 处境与奥德赛", 5),
    ("第三部分 真实的世界：已知的和未知的", 9), ("第四部分 精神世界的奇幻历程", 13),
]
# 跳过: 封面/CIP/卷首引文/目录/封底广告
SKIP_PAGES = {0, 1, 2, 3, 9, 10, 11, 12, 13, 356}
# 部分扉页整页空（纯标题+节列表页，无正文，OCR 行序乱不可逐行剥）
EMPTY_PAGES = {14, 108, 202, 272}
# 章起始页（节标题页/前言标题页/部分扉页后一页）
PAGE_START = {4: 0, 15: 1, 39: 2, 59: 3, 88: 4, 109: 5, 128: 6, 149: 7,
              172: 8, 203: 9, 219: 10, 238: 11, 257: 12, 273: 13, 292: 14,
              318: 15, 336: 16}
# 前言标题行 + p203 粘连节号（部分扉页由 EMPTY_PAGES 整页空）
STRIP_PAGES = {
    4: ["前言：你说的哲学是什么意思？"],
    203: ["3-1知识"],  # OCR 节号+节名粘连
}
# 页眉: 尾行 'N像哲学家一样思考'（页码+书名粘连）；p172 尾行 '2-4生命/时间'
HEAD_RE = re.compile(r"^\d{1,3}像哲学家一样思考$")
# 页码: 独立数字行任意位置剥
PAGE_RE = re.compile(r"^\d{1,3}$")
# 节标题页节号行（首行）: '1-1' 等
SECNO_RE = re.compile(r"^\d-\d$")
# 页首小节标题独立段: 纯汉字（含引号/省略号）≤8字 无句读
TITLE_RE = re.compile(r"^[\u4e00-\u9fff“”『』「」…]{1,8}$")

ckpt = None
for _try in range(5):
    try:
        ckpt = json.load(open(CKPT, encoding="utf-8"))
        break
    except json.JSONDecodeError:
        time.sleep(2)
    except MemoryError:
        time.sleep(5)
if ckpt is None:
    sys.exit("checkpoint 连续 5 次读失败，OCR 队列可能正在写入，稍后重试")
pages = ckpt["ocr"][SAFE]
npages = {int(k): v for k, v in pages.items() if v and v != "__FAILED__"}
fails = sorted([int(k) for k, v in pages.items() if v == "__FAILED__"])
print(f"OCR 页: {min(npages)}-{max(npages)} 共 {len(npages)} 页, fail {len(fails)} 页: {fails}")

def page_paras(i, secno_seen):
    """页 → 段列表。secno_seen: 本页是否节标题页（剥节号+节名行）"""
    if i in EMPTY_PAGES:
        return []
    ls = [ln.strip() for ln in npages[i].split("\n") if ln.strip()]
    if secno_seen:
        # 节标题页: 剥首行节号 + 次行节名
        if ls and SECNO_RE.match(ls[0]):
            ls = ls[1:]
            if ls and ls[0] in SEC_NAMES:
                ls = ls[1:]
    if i in STRIP_PAGES:
        ls = [l for l in ls if l not in STRIP_PAGES[i]]
    while ls and HEAD_RE.match(ls[-1]):
        ls = ls[:-1]                       # 尾行页眉剥
    ls = [l for l in ls if not PAGE_RE.match(l)]  # 独立页码任意位置剥
    out, buf = [], []
    for j, l in enumerate(ls):
        if j == 0 and TITLE_RE.match(l):
            if buf:
                out.append("".join(buf)); buf = []
            out.append(l)                  # 页首小节标题独立段
        else:
            buf.append(l)
    if buf:
        out.append("".join(buf))
    return out

paras = [[] for _ in range(N)]
cur = 0
for i in sorted(npages):
    if i in SKIP_PAGES:
        continue
    if i in PAGE_START:
        cur = PAGE_START[i]
    ps = page_paras(i, i in PAGE_START and i != 4)  # p4 前言标题页非节号格式
    if not ps:
        print(f"⚠ p{i}: 净化后为空")
    paras[cur].extend(ps)

files = {}
for idx in range(N):
    if not paras[idx]:
        print(f"⚠ 章{idx} {CH_TITLES[idx]!r}: 无内容")
    files[idx] = {"index": idx, "title": CH_TITLES[idx],
                  "content": [{"type": "text", "value": p} for p in paras[idx]]}
    nc = sum(len(norm(p)) for p in paras[idx])
    first = paras[idx][0][:32] if paras[idx] else "(空)"
    last = paras[idx][-1][:22] if paras[idx] else ""
    print(f"[{idx}] {CH_TITLES[idx]:<26s} {nc:6d}字 {len(paras[idx]):3d}段 | {first!r} … {last!r}")
assert len(files) == N

# ---- 验证 ----
total = sum(sum(len(norm(b["value"])) for b in files[idx]["content"]) for idx in range(N))
print(f"\n新总净: {total}")
all_text = "".join(norm(b["value"]) for idx in range(N) for b in files[idx]["content"])
# 页码粘连清零
bad_page = [norm(b["value"])[:8] for idx in range(N) for b in files[idx]["content"]
            if re.match(r"[一-鿿]\d{2,3}", norm(b["value"]))
            and not re.search(r"\d{2,4}年", norm(b["value"])[:12])
            and not re.search(r"\d{1,2}[:：]\d{1,2}", norm(b["value"]))]
print("页码粘连清零:", "✓" if not bad_page else f"✗ {bad_page[:6]}")
# 页眉残留
bad_h = [f"章{idx}:{norm(b['value'])[:16]}" for idx in range(N) for b in files[idx]["content"]
         if re.search(r"\d{1,3}像哲学家一样思考", norm(b["value"]))]
print("页眉清零:", "✓" if not bad_h else f"✗ {bad_h[:6]}")
# 节标题页节号残留
bad_n = [f"章{idx}:{b['value'][:10]}" for idx in range(N) for b in files[idx]["content"]
         if SECNO_RE.match(b["value"])]
print("节号清零:", "✓" if not bad_n else f"✗ {bad_n[:6]}")
# 目录内容泄漏（'ENTIA' 在语词和对象里，这里用上册目录特有行）
print("目录泄漏:", "✓" if "简明目录" not in all_text else "✗ 目录混入!")
# 关键内容验证
ch = {idx: "".join(norm(b["value"]) for b in files[idx]["content"]) for idx in range(N)}
checks = [
    (0, "前言", "书店"), (1, "1-1", "日食"), (1, "1-1", "奥勒留"),
    (2, "1-2", "爱智慧"), (3, "1-3", "亚里士多德曾经写道"),
    (4, "1-4", "泰格"), (5, "2-1", "自我中心困境"), (5, "2-1", "加缪"),
    (6, "2-2", "梭罗"), (7, "2-3", "弗洛伊德"), (8, "2-4", "伊万·伊里奇"),
    (9, "3-1", "认识论"), (9, "3-1", "洛克"), (10, "3-2", "贝克莱"),
    (11, "3-3", "柏格森"), (12, "3-4", "詹姆斯"), (13, "4-1", "佛陀"),
    (14, "4-2", "绵延"), (15, "4-3", "萨特"), (16, "4-4", "维特根斯坦"),
]
print("验证:", "  ".join(f"{'✓'+t if kw in ch[i] else '✗'+t+'!'}" for i, t, kw in checks))

# ---- toc（4 part + 17 chapter 两级） ----
toc = [{"type": "part", "title": t, "level": 0, "index": idx} for t, idx in PARTS]
toc += [{"type": "chapter", "title": files[i]["title"], "index": i, "level": 1}
        for i in range(N)]
print(f"\ntoc 项: {len(toc)}（{len(PARTS)} part + {N} chapter）")

if "--dry" in sys.argv:
    sys.exit(0)

# ---- 写入（旧 12 章自动数据 → 备份 _old_bad） ----
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
    "bookId": BID, "title": "像哲学家一样思考", "author": AUTHOR,
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
        d["author"] = AUTHOR
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
        print(f"✓ book_detail 更新: {p}")

if os.path.exists(BOOKS_JSON):
    bj = json.load(open(BOOKS_JSON, encoding="utf-8"))
    bl = bj if isinstance(bj, list) else bj.get("books", [])
    hit = False
    for b in bl:
        if b.get("id") == BID:
            b["chapterCount"] = N
            if "author" in b:
                b["author"] = AUTHOR
            hit = True
    if hit:
        with open(BOOKS_JSON, "w", encoding="utf-8") as f:
            json.dump(bl if isinstance(bj, list) else {**bj, "books": bl}, f,
                      ensure_ascii=False, indent=None)
        print("✓ books.json chapterCount/author 更新")
    else:
        print("⚠ books.json 未找到该书")
