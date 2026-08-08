# -*- coding: utf-8 -*-
"""#259 奥古斯丁忏悔录（a2931a891bf9，奥古斯丁）重建
病因: 已OCR未入清单补录书（CHKLIST 无此条）。旧 5 章为 dp_pdf_import 自动切章
  （'章15节。'/'章22节。'/'章32节。' 等正文碎片乱取，books.json cc=5）。
源: F:/philosophy/西方/奥古斯丁/奥古斯丁忏悔录.pdf（407 页扫描版，
  华文出版社 2003 世界三大忏悔录丛书，向云常译，checkpoint OCR 407 页 fail 2: p391/395）
结构（目录 p5；书内页码=PDF页-5）:
  p0-1 封面/内封（跳过）｜ p2 CIP 版权（跳过）｜ p3-4 序言《忏悔与文明》
    （p3 标题+正文同页，无页眉页码；p4 续页）｜ p5 目录（跳过）
  13 卷: 卷一 p6（书内1）/卷二 p32（27）/卷三 p46（41）/卷四 p64（59）/
    卷五 p90（85）/卷六 p112（107）/卷七 p138（133）/卷八 p166（161）/
    卷九 p192（187）/卷十 p220（215）/卷十一 p276（271）/卷十二 p312（307）/
    卷十三 p350（345）-394（389）｜ 年谱: 圣奥古斯丁年谱 p396（391）-406（401）
  插图页 20 处（图题单行，跳过）: 45/88/89/137/165/191/219/238/239/260/261/
    282/303/304/325/326/345/346/368/369；p31 单字'中'（疑卷首插页，跳过）
⚠ fail 2: p391（书内386，卷十三内）/p395（书内390，卷十三尾）→ 待补 OCR
页眉: 偶页=书名'奥古斯丁忏悔录'、奇页=丛书名'世界三大忏悔录'（各 20+ OCR 变体:
  杆悔录/轩悔录/軒悔录/轩梅录/轩录/杆将景…阡梅录/怀梅录/籽悔录/轩悔景…），
  正则 ^(奥古斯丁|世界三大)[\u4e00-\u9fff]{1,4}$ 页首循环剥
页码: 独立行（'2'/'59'/'401'，纯数字，无装饰线；偶有页码在页眉前一行）
节号: 卷内节号独立行（'一'~'三十五'，'三十' 等页首/页中任意位置），
  正则 ^[一二三四五六七八九十]{1,4}$ 任意位置剥（卷八标题 p166 '八' 兼被剥，无损失）
标题: 卷起始页页首标题行按页精确剥（'卷二' 单行；p64/p220 跨两行 '卷'+'四'/'卷'+'+'；
  p192 '卷.九' OCR 变体；p166 卷八标题 '八' 被节号正则剥）
修复: 重建 15 章（序言+13 卷+年谱）；段落: 每页过滤行拼接为一段（OCR 书范式）。
用法: python _xr_a2931a891bf9_confessions_rebuild.py [--dry]
"""
import json, os, re, sys, shutil, time

BID = "a2931a891bf9"
CKPT = r"f:\program\Python\PhiAgent\backend\data\dp_pdf_import_ckpt.json"
SAFE = "西方_奥古斯丁_奥古斯丁忏悔录.pdf"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
# ⚠ 2026-08-08 事故修正：前端本地 dev 读 app/public/backend/data/book_chapters，必须双写
DST2 = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

def norm(s):
    return re.sub(r"\s+", "", s or "")

# 15 章
CH_TITLES = [
    "忏悔与文明",
    "卷一", "卷二", "卷三", "卷四", "卷五", "卷六", "卷七",
    "卷八", "卷九", "卷十", "卷十一", "卷十二", "卷十三",
    "圣奥古斯丁年谱",
]
N = len(CH_TITLES)
# 跳过: 封面/CIP/目录/插页/插页单字页/fail 页
SKIP_PAGES = {0, 1, 2, 5, 31, 391, 395, 407} | {
    45, 88, 89, 137, 165, 191, 219, 238, 239, 260, 261,
    282, 303, 304, 325, 326, 345, 346, 368, 369}
# 卷起始页（标题行剥后该页正文归新章）
PAGE_START = {6: 1, 32: 2, 46: 3, 64: 4, 90: 5, 112: 6, 138: 7, 166: 8,
              192: 9, 220: 10, 276: 11, 312: 12, 350: 13, 396: 14}
# 卷标题行（按页精确剔除；p64/p220 跨两行；p192 '卷.九' 变体；p166 '八' 由节号正则剥）
STRIP_PAGES = {
    3: ["忏悔与文明"], 6: ["卷"], 32: ["卷二"], 46: ["卷三"], 64: ["卷", "四"],
    90: ["卷五"], 112: ["卷六"], 138: ["卷七"], 192: ["卷.九"],
    220: ["卷", "+"], 276: ["卷十一"], 312: ["卷十二"], 350: ["卷十三"],
    396: ["圣奥古斯丁年谱"],
}
# 页眉（页首第一行循环剥）: 偶页书名/奇页丛书名，OCR 变体几十种 → 前缀+长度正则
HEAD_RE = re.compile(r"^(奥古斯丁|世界三大)[\u4e00-\u9fff]{1,4}$")
# 页码行（独立纯数字，任意位置）
PAGE_RE = re.compile(r"^\d{1,4}$")
# 卷内节号（独立行，'一'~'三十五'，任意位置；兼剥 p166 卷八标题'八'）
NU_RE = re.compile(r"^[一二三四五六七八九十]{1,4}$")

# checkpoint 读重试（OCR 队列并发写 → 瞬时截断）
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
print(f"⚠ 待补 OCR 页（p391=书内386 卷十三内/p395=书内390 卷十三尾，重建后提醒用户）: {fails}")

def clean(i):
    """页 → 净化行（页码/节号任意位置剥 + 页眉页首循环剥 + 标题行精确剔）"""
    t = npages.get(i, "")
    if not t:
        return []
    ls = [ln.strip() for ln in t.split("\n") if ln.strip()]
    ls = [l for l in ls if not PAGE_RE.match(l)]       # 页码行（含页眉前的行）
    while ls and HEAD_RE.match(ls[0]):
        ls = ls[1:]                                    # 页眉（页首循环剥）
    if i in STRIP_PAGES:
        ls = [l for l in ls if l not in STRIP_PAGES[i]]  # 卷/序言标题行
    ls = [l for l in ls if not NU_RE.match(l)]         # 节号行任意位置剥
    return ls

# ---- 逐章解析（页级段落范式 + 固定切章页） ----
files = {}
cur = 0
paras = [[] for _ in range(N)]
for i in sorted(npages):
    if i in SKIP_PAGES:
        continue
    if i in PAGE_START:
        cur = PAGE_START[i]
    ls = clean(i)
    if not ls:
        continue
    paras[cur].append("".join(ls))
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
# 页码粘连清零（段首不得汉字+2-3位数字粘连）
bad_page = [norm(b["value"])[:8] for idx in range(N) for b in files[idx]["content"]
            if re.match(r"[一-鿿]\d{2,3}", norm(b["value"]))
            and not re.match(r"图\d{2,3}", norm(b["value"]))
            and not re.search(r"\d{2,3}岁", norm(b["value"]))
            and not re.search(r"\d{2,4}年", norm(b["value"])[:12])]
print("页码粘连清零:", "✓" if not bad_page else f"✗ {bad_page[:6]}")
# 独立页码行/节号清零
bad_s = [norm(b["value"]) for idx in range(N) for b in files[idx]["content"]
         if re.match(r"^\d{1,4}$", norm(b["value"]))]
print("独立页码清零:", "✓" if not bad_s else f"✗ {bad_s[:5]}")
# 页眉/标题清零
bad_h = [f"章{idx}:{norm(b['value'])[:14]}" for idx in range(N) for b in files[idx]["content"]
         if HEAD_RE.match(norm(b["value"]))
         or norm(b["value"]) in {norm(x) for v in STRIP_PAGES.values() for x in v}]
print("标题清零:", "✓" if not bad_h else f"✗ {bad_h[:6]}")
# 英文残留（脚注/正文均中文；年谱含书名《…》中文；全书检查）
bad_en = [f"章{idx}段{n}" for idx in range(N) for n, b in enumerate(files[idx]["content"])
          if len(re.findall(r"[A-Za-z]", b["value"])) > len(b["value"]) * 0.4]
print("英文残留:", "✓" if not bad_en else f"✗ {bad_en[:5]}")
# 关键内容验证（各卷起始页首段词）
ch = {idx: "".join(norm(b["value"]) for b in files[idx]["content"]) for idx in range(N)}
checks = [
    (0, "忏悔与文明", "托尔斯泰"), (1, "卷一", "耶和华"), (2, "卷二", "污秽"),
    (3, "卷三", "迦太基"), (4, "卷四", "自由学术"), (5, "卷五", "唇舌"),
    (6, "卷六", "仰望"), (7, "卷七", "壮年"), (8, "卷八", "束缚"),
    (9, "卷九", "谢恩"), (10, "卷十", "渗透"), (11, "卷十一", "永恒"),
    (12, "卷十二", "心惊"), (13, "卷十三", "呼求"), (14, "年谱", "公元"),
]
print("验证:", "  ".join(f"{'✓'+t if kw in ch[i] else '✗'+t+'!'}" for i, t, kw in checks))

# ---- toc ----
toc = [{"type": "chapter", "title": files[i]["title"], "index": i, "level": 1} for i in range(N)]
print(f"\ntoc 项: {len(toc)}")

if "--dry" in sys.argv:
    sys.exit(0)

# ---- 写入（旧 5 章自动数据 → 备份 _old_bad） ----
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
    "bookId": BID, "title": "奥古斯丁忏悔录", "author": "奥古斯丁",
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
