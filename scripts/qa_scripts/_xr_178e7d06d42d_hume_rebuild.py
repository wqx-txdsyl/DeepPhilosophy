# -*- coding: utf-8 -*-
"""#253 人性论（178e7d06d42d，大卫·休谟）重建
病因: OCR 完成的 20 本未入清单书之一。旧 136 章为 dp_pdf_import 自动切章
  （目录级过细，双语混合，后半章节空）。
源: F:/philosophy/西方/大卫·休谟/人性论_全4册_.pdf（395 页扫描版，英汉对照
  （西方学术经典文库·第一册（一）），石碧球译（九州出版社 2007），checkpoint OCR 395 页 fail 0）
结构（英汉对照版: 中文页/英文页交替——奇数页=中文译文，偶数页=英文原文;
  导论等前言部分同构; 重建只保留中文译文）:
  p0-1 封面/CIP（跳过） ｜ p2 出版说明（中文）
  p3 英文书名页（跳过） ｜ p4 英文公告（跳过） ｜ p5 一、二卷的公告（中文）
  p6 英文导论（跳过） ｜ p7-17 导论中文（奇数页）
  p19-28 全书总目录（英文标题+中文标题+页码交替，跳过）
  p29 扉页（跳过） ｜ p30 英文 BOOK I（跳过）
  p31-79 第一卷第一章论观念（书内 3-51；p31 卷+章+节标题跨行 4 行）
  p81-167 第一卷第二章论空间和时间观念（书内 53-139；p81 标题跨行 2 行）
  p169-393 第一卷第三章论知识和或然性（书内 141-365；p169 标题跨行 2 行）
  p394 封底（跳过）
页码噪声: 书内页码在页尾带装饰线（'一3一'/'—140—'/'=121 —'/'一4='/'2一'），
  正则 ^[—\-一=\s]*\d{1,4}[—\-一=\s]*$ 剥整行
页眉: 奇数页页眉=章名（'导论'/'第一卷第一章'/'第一卷第二章'/'第一卷第三章'）
  页首第一行精确匹配剥离；英文页页眉'人性论'随英文页剥除
标题: 章起始页标题跨行按页精确剥离；节标题（'第X节论…'，27 处独立行）正则剥整行
   （正文引用'①第一章，第五节。'在行中，正则^第[一二三四五六七八九十]+节 不误伤）
英文页兜底: 页剥剩内容无中文字符 → 整页跳过（防奇偶例外页）
修复: 重建 6 章（只含中文译文）；段落: 每页过滤后行拼接为一段（OCR 书范式）。
用法: python _xr_178e7d06d42d_hume_rebuild.py [--dry]
"""
import json, os, re, sys, shutil, time

BID = "178e7d06d42d"
CKPT = r"f:\program\Python\PhiAgent\backend\data\dp_pdf_import_ckpt.json"
SAFE = "西方_大卫_休谟_人性论_全4册_.pdf"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
# ⚠ 2026-08-08 事故修正：前端本地 dev 读 app/public/backend/data/book_chapters，必须双写
DST2 = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

def norm(s):
    return re.sub(r"\s+", "", s or "")

def odd(a, b):
    return [i for i in range(a, b + 1) if i % 2 == 1]

# 6 章: (idx, 标题, 页列表) — PDF 页（只含中文页）
CH = [
    (0, "出版说明", [2]),
    (1, "一、二卷的公告", [5]),
    (2, "导论", odd(7, 17)),
    (3, "第一卷 第一章 论观念，它们的起源、组合、联系、抽象等", odd(31, 79)),
    (4, "第一卷 第二章 论空间和时间观念", odd(81, 167)),
    (5, "第一卷 第三章 论知识和或然性", odd(169, 393)),
]
# 页眉（奇数页页首第一行精确匹配）
HEADERS = {"导论", "第一卷第一章", "第一卷第二章", "第一卷第三章"}
# 章起始页标题跨行（按页顺序剥离）
STRIP_PAGES = {
    2: ["出版说明"],
    5: ["一、二卷的公告"],          # 注: p7 '导论' 由 HEADERS 剥（页眉/标题同名）
    31: ["第一卷论知性", "第一章论观念，它们的起源、", "组合、联系、抽象等", "第一节论我们观念的起源"],
    81: ["第二章论空间和时间观念", "第一节论空间和时间观念的无限可分性"],
    169: ["第三章论知识和或然性", "第一节论知识"],
}
# 节标题独立行（页内任意位置）
SEC_RE = re.compile(r"^第[一二三四五六七八九十]+节")
# 页码行（书内页码带装饰线，'一3一'/'=121 —'/'一4='）
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
    """页 → 行（剥页眉/标题/节标题/页码噪声后）; 无中文即英文页返回空"""
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
    ls = [l for l in ls if not SEC_RE.match(l)]    # 节标题独立行
    ls = [l for l in ls if not PAGE_RE.match(l)]   # 页码行
    if ls and not re.search(r"[\u4e00-\u9fff]", "".join(ls)):
        return []                          # 英文页兜底
    return ls

# ---- 逐章解析（页级段落范式） ----
files = {}
for idx, title, plist in CH:
    paras = []
    for i in plist:
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
    print(f"[{idx}] {title:<36s} {nc:6d}字 {len(paras):3d}段 | {first!r} … {last!r}")
assert len(files) == 6

# ---- 验证 ----
total = sum(sum(len(norm(b["value"])) for b in files[idx]["content"]) for idx in range(6))
print(f"\n新总净: {total}")
all_text = "".join(norm(b["value"]) for idx in range(6) for b in files[idx]["content"])
# 页码粘连清零: 段首不得以'汉字+2-3数字'粘连开头（学术注释中的书目页码保留段中/段尾）
bad_page = [norm(b["value"])[:8] for idx in range(6) for b in files[idx]["content"]
            if re.match(r"[\u4e00-\u9fff]\d{2,3}", norm(b["value"]))
            and not re.match(r"图\d{2,3}", norm(b["value"]))]
print("页码粘连清零:", "✓" if not bad_page else f"✗ {bad_page[:6]}")
# 独立页码行清零: 段不得整体为装饰线数字/纯数字
bad_s = [norm(b["value"]) for idx in range(6) for b in files[idx]["content"]
         if re.match(r"^[—\-一=\s]*\d{1,4}[—\-一=\s]*$", norm(b["value"]))]
print("独立页码清零:", "✓" if not bad_s else f"✗ {bad_s[:5]}")
# 页眉/标题清零
bad_h = [norm(b["value"])[:14] for idx in range(6) for b in files[idx]["content"]
         if norm(b["value"]) in {norm(h) for h in HEADERS} | {norm(x) for v in STRIP_PAGES.values() for x in v}]
print("标题清零:", "✓" if not bad_h else f"✗ {bad_h[:5]}")
# 节标题清零: 段首不得为'第X节'（正文引用'第一章，第五节。'在段中）
bad_sec = [norm(b["value"])[:12] for idx in range(6) for b in files[idx]["content"]
           if re.match(r"^第[一二三四五六七八九十]+节", norm(b["value"]))]
print("节标题清零:", "✓" if not bad_sec else f"✗ {bad_sec[:5]}")
# 英文残留: 段内英文字符占比过高（英文页误入）
bad_en = [f"章{idx}段{n}" for idx in range(6) for n, b in enumerate(files[idx]["content"])
          if len(re.findall(r"[A-Za-z]", b["value"])) > len(b["value"]) * 0.4]
print("英文残留:", "✓" if not bad_en else f"✗ {bad_en[:5]}")
# 关键内容验证
ch = {idx: "".join(norm(b["value"]) for b in files[idx]["content"]) for idx in range(6)}
checks = [
    (0, "出版说明", "西方学术经典文库"),
    (1, "公告", "公众的认可"),
    (2, "导论", "辩论术"),
    (3, "第一章", "印象和观念"),
    (4, "第二章", "无限可分"),
    (5, "第三章", "或然性"),
]
print("验证:", "  ".join(f"{'✓'+t if kw in ch[i] else '✗'+t+'!'}" for i, t, kw in checks))
# 目录页清零
print("目录页清零:", "✓" if "目" not in all_text or not re.search(r"目\s*录", all_text) else "✗")

# ---- toc ----
toc = [{"type": "chapter", "title": files[i]["title"], "index": i, "level": 1} for i in range(6)]
print(f"\ntoc 项: {len(toc)}")

if "--dry" in sys.argv:
    sys.exit(0)

# ---- 写入（旧 136 章自动数据 → 备份 _old_bad） ----
if os.path.isdir(SRC):
    suf = "_old_bad"
    i2 = 2
    while os.path.isdir(SRC + suf):
        suf = f"_old_bad{i2}"
        i2 += 1
    os.rename(SRC, SRC + suf)
    print(f"\n备份旧数据 → {os.path.basename(SRC) + suf}")
os.makedirs(SRC)
for idx in range(6):
    f = files[idx]
    json.dump({"index": idx, "title": f["title"], "content": f["content"]},
              open(os.path.join(SRC, f"{idx}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
meta = {
    "bookId": BID, "title": "人性论", "author": "大卫·休谟",
    "toc": toc, "cover": None, "chapterCount": 6,
    "chapterTitles": [files[i]["title"] for i in range(6)],
}
json.dump(meta, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print(f"✓ 写入 {SRC}: 6 章 + meta.json")

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
        d["chapterCount"] = 6
        d["chapterTitles"] = meta["chapterTitles"]
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
        print(f"✓ book_detail 更新: {p}")

if os.path.exists(BOOKS_JSON):
    bj = json.load(open(BOOKS_JSON, encoding="utf-8"))
    bl = bj if isinstance(bj, list) else bj.get("books", [])
    hit = False
    for b in bl:
        if b.get("id") == BID:
            b["chapterCount"] = 6
            hit = True
    if hit:
        with open(BOOKS_JSON, "w", encoding="utf-8") as f:
            json.dump(bl if isinstance(bj, list) else {**bj, "books": bl}, f,
                      ensure_ascii=False, indent=None)
        print("✓ books.json chapterCount 更新")
    else:
        print("⚠ books.json 未找到该书")
