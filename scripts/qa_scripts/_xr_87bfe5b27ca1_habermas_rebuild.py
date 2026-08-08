# -*- coding: utf-8 -*-
"""#252 交往行为理论（87bfe5b27ca1，尤尔根·哈贝马斯）重建
病因: OCR 完成的 20 本未入清单书之一。旧 13 章为 dp_pdf_import 自动切章
  （强模式标题无命中→整本粗切），重复标题/空参考文献/内容错乱。
源: F:/philosophy/西方/尤尔根·哈贝马斯/交往行为理论.pdf（442 页扫描版，
  曹卫东译（上海人民出版社 2004，哈贝马斯文集第四卷·第一卷），checkpoint OCR 442 页 fail 0）
结构（目录 p14-17，书内页码=PDF页-17）:
  p0-4 封面/CIP/作者行（跳过） ｜ p5-6 译者前言（书内 1-2）
  p7-10 第一版序言（书内 3-6；p9 页首'第-一版前言'为页眉OCR变体）
  p11-13 第三版序言（书内 7-9）
  p14-17 目录（跳过）
  p18-157 一、导论：对合理性问题的理解（书内 1-140；p18 章起始页标题跨行 2 行）
  p158-276 二、马克斯·韦伯的合理化理论（书内 141-259；p158 标题跨行 2 行）
  p277-337 三、第一卷的中间考察：社会行为，目的行为以及交往（书内 260-320；
    p277 标题跨行 3 行+概论跨行 2 行）
  p338-398 四、从卢卡奇到阿多诺：作为物化的合理化（书内 321-381；
    p338 标题跨行 2 行+导论跨行 2 行）
  p399-441 参考文献（书内 382-424；p399 标题'参考文献*'）
页码噪声: 书内页码在页尾，格式带装饰线 '—140—'/'—141'/'—260'/'321'/'——102—'
  /'—348——一'（'—'OCR变体'一'），正则 ^[—\-一]*\d{1,4}[—\-一]*$ 任意位置剥整行
页眉: 偶页页眉=书名'交往行为理论'，奇页页眉=章节名（一、导论…/二、马克斯…
  三、第一卷的中间考察…/四、从卢卡奇到阿多诺…/参考文献/译者前言/第一版序言/
  第三版序言），页首第一行精确匹配剥离；OCR变体 3 种（'、导论/p148'一一'/p242'一'）
小节起始页: 页首标题跨行（'2.神话世界观和现代世界'+'观的若干特征'等 10 处），
  按页精确剥离；小节起始页无页眉行（标题代替）
正文中段纯数字行 13 处均为图内元素/脚注碎片（p22图/p245图3），随正则剥除
修复: 重建 8 章；段落: 每页过滤后行拼接为一段（OCR 书范式）。
用法: python _xr_87bfe5b27ca1_habermas_rebuild.py [--dry]
"""
import json, os, re, sys, shutil, time

BID = "87bfe5b27ca1"
CKPT = r"f:\program\Python\PhiAgent\backend\data\dp_pdf_import_ckpt.json"
SAFE = "西方_尤尔根_哈贝马斯_交往行为理论.pdf"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
# ⚠ 2026-08-08 事故修正：前端本地 dev 读 app/public/backend/data/book_chapters，必须双写
DST2 = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

def norm(s):
    return re.sub(r"\s+", "", s or "")

# 8 章: (idx, 标题, 起始页, 结束页) — PDF 页
CH = [
    (0, "译者前言", 5, 6),
    (1, "第一版序言", 7, 10),
    (2, "第三版序言", 11, 13),
    (3, "一、导论：对合理性问题的理解", 18, 157),
    (4, "二、马克斯·韦伯的合理化理论", 158, 276),
    (5, "三、第一卷的中间考察：社会行为，目的行为以及交往", 277, 337),
    (6, "四、从卢卡奇到阿多诺：作为物化的合理化", 338, 398),
    (7, "参考文献", 399, 441),
]
SKIP_PAGES = set(range(0, 5)) | set(range(14, 18))   # 封面/CIP + 目录
# 页眉（页首第一行精确匹配，含 OCR 变体）
HEADERS = {
    "交往行为理论",                       # 书名页眉
    "一、导论：对合理性问题的理解", "二、马克斯·韦伯的合理化理论",
    "三、第一卷的中间考察：社会行为，目的行为以及交往",
    "三、第一卷的中间考察：社会行为，自的行为以及交往",   # OCR 变体
    "四、从卢卡奇到阿多诺：作为物化的合理化",
    "参考文献", "译者前言", "第一版序言", "第三版序言", "第-一版前言",
    '"、导论：对合理性问题的理解',          # p80 变体（'一'→'”、'）
    "一一、导论：对合理性问题的理解",        # p148 变体
    "一、马克斯·韦伯的合理化理论",          # p242 变体（'二'→'一'）
}
# 章起始页/小节起始页标题跨行（按页顺序剥离）
STRIP_PAGES = {
    18: ["一、导论：对合理性问题的", "理解", "概论：社会学中的合理", "性概念"],
    25: ["定义"],                             # 小节标题残段（'1。"合理性"：概念的临时'跨行尾）
    60: ["2.神话世界观和现代世界", "观的若干特征"],
    91: ["3.四种社会学行为概念中", "行为与世界的关联以及", "合理性层面"],
    119: ["4.社会科学中的意义", "理解问题"],
    158: ["马克斯·韦伯的合理", "化理论", "概论：科学史语境"],
    170: ["1.西方理性主义"],
    196: ["2.宗教一形而上学世界观", "的解神秘化与现代", "意识结构的形成"],
    226: ["3.作为社会合理化的现代化：", "新教伦理的作用"],
    250: ["4.法的合理化与对", "当代的诊断"],
    277: ["三、第一卷的中间考察：社", "会行为，目的行为以", "及交往",
          "概论：分析的意义理论和", "行为理论的前言"],
    338: ["四、从卢卡奇到阿多诺：作", "为物化的合理化",
          "导论：生活世界的合理化对行", "为系统的不断复杂化"],
    343: ["1.西方马克思主义传统", "中的马克斯·韦伯"],
    365: ["2.工具理性批判"],
    399: ["参考文献*"],
}
# 页码行（书内页码带装饰线，'—140—'/'321'/'——102—'/'一7一'/'—348——一'）
PAGE_RE = re.compile(r"^[—\-一]*\d{1,4}[—\-一]*$")

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
        for h in STRIP_PAGES[i]:
            if ls and ls[0] == h:
                ls = ls[1:]
            else:
                cur = ls[0] if ls else "(空)"
                print(f"⚠ p{i} 期望标题 {h!r} 不匹配实际 {cur!r}")
                break
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
    print(f"[{idx}] {title:<34s} {nc:6d}字 {len(paras):3d}段 | {first!r} … {last!r}")
assert len(files) == 8

# ---- 验证 ----
total = sum(sum(len(norm(b["value"])) for b in files[idx]["content"]) for idx in range(8))
print(f"\n新总净: {total}")
all_text = "".join(norm(b["value"]) for idx in range(8) for b in files[idx]["content"])
# 页码粘连清零: 段首不得以'汉字+2-3数字'粘连开头（学术注释中的书目页码保留段中/段尾）
bad_page = [norm(b["value"])[:8] for idx in range(8) for b in files[idx]["content"]
            if re.match(r"[一-鿿]\d{2,3}", norm(b["value"]))            and not re.match(r"图\d{2,3}", norm(b["value"]))]
print("页码粘连清零:", "✓" if not bad_page else f"✗ {bad_page[:6]}")
# 独立页码行清零: 段不得整体为装饰线数字/纯数字
bad_s = [norm(b["value"]) for idx in range(8) for b in files[idx]["content"]
         if re.match(r"^[—\-一]*\d{1,4}[—\-一]*$", norm(b["value"]))]
print("独立页码清零:", "✓" if not bad_s else f"✗ {bad_s[:5]}")
# 页眉/标题清零
bad_h = [norm(b["value"])[:14] for idx in range(8) for b in files[idx]["content"]
         if norm(b["value"]) in {norm(h) for h in HEADERS} | {norm(x) for v in STRIP_PAGES.values() for x in v}]
print("标题清零:", "✓" if not bad_h else f"✗ {bad_h[:5]}")
# 关键内容验证
ch = {idx: "".join(norm(b["value"]) for b in files[idx]["content"]) for idx in range(8)}
checks = [
    (0, "译者前言", "过渡性"),
    (1, "第一版序言", "社会科学的逻辑"),
    (2, "第三版序言", "范式转型"),
    (3, "导论", "意见和行为的合理性"),
    (4, "韦伯", "解神秘化"),
    (5, "中间考察", "以言行事"),
    (6, "卢卡奇", "物化"),
    (7, "参考文献", "Adorno"),
]
print("验证:", "  ".join(f"{'✓'+t if kw in ch[i] else '✗'+t+'!'}" for i, t, kw in checks))
# 目录页清零
print("目录页清零:", "✓" if "目" not in all_text or not re.search(r"目\s*录", all_text) else "✗")

# ---- toc ----
toc = [{"type": "chapter", "title": files[i]["title"], "index": i, "level": 1} for i in range(8)]
print(f"\ntoc 项: {len(toc)}")

if "--dry" in sys.argv:
    sys.exit(0)

# ---- 写入（旧 13 章自动数据 → 备份 _old_bad） ----
if os.path.isdir(SRC):
    suf = "_old_bad"
    i2 = 2
    while os.path.isdir(SRC + suf):
        suf = f"_old_bad{i2}"
        i2 += 1
    os.rename(SRC, SRC + suf)
    print(f"\n备份旧数据 → {os.path.basename(SRC) + suf}")
os.makedirs(SRC)
for idx in range(8):
    f = files[idx]
    json.dump({"index": idx, "title": f["title"], "content": f["content"]},
              open(os.path.join(SRC, f"{idx}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
meta = {
    "bookId": BID, "title": "交往行为理论", "author": "尤尔根·哈贝马斯",
    "toc": toc, "cover": None, "chapterCount": 8,
    "chapterTitles": [files[i]["title"] for i in range(8)],
}
json.dump(meta, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print(f"✓ 写入 {SRC}: 8 章 + meta.json")

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
        d["chapterCount"] = 8
        d["chapterTitles"] = meta["chapterTitles"]
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
        print(f"✓ book_detail 更新: {p}")

if os.path.exists(BOOKS_JSON):
    bj = json.load(open(BOOKS_JSON, encoding="utf-8"))
    bl = bj if isinstance(bj, list) else bj.get("books", [])
    hit = False
    for b in bl:
        if b.get("id") == BID:
            b["chapterCount"] = 8
            hit = True
    if hit:
        with open(BOOKS_JSON, "w", encoding="utf-8") as f:
            json.dump(bl if isinstance(bj, list) else {**bj, "books": bl}, f,
                      ensure_ascii=False, indent=None)
        print("✓ books.json chapterCount 更新")
    else:
        print("⚠ books.json 未找到该书")
