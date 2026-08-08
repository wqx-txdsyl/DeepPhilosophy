# -*- coding: utf-8 -*-
"""#260 新大西岛（633de4142354，弗朗西斯·培根）重建
病因: 已OCR未入清单补录书。旧 1 章自动切章（'新大西岛[英]弗·培根著BMJC0800'
  封面噪声混入正文，无噪声清理）。
源: F:/philosophy/西方/弗朗西斯·培根/新大西岛.pdf（40 页扫描版，繁体老译本，
  何新译（汉译世界学术名著丛书），checkpoint OCR 40 页 fail 0）
结构: p0 封面（'新大西岛'/'[英]弗·培根著'/书号）跳过｜ p1 版权页（英文+出版信息）跳过
  p2-38 正文（无章节，整篇）｜ p39 封底（'1452678' 书号）跳过
繁体中文原样保留（用户规则）。
修复: 重建 1 章（正文）；段落: 每页过滤行拼接为一段（OCR 书范式）。
用法: python _xr_633de4142354_atlantis_rebuild.py [--dry]
"""
import json, os, re, sys, shutil, time

BID = "633de4142354"
CKPT = r"f:\program\Python\PhiAgent\backend\data\dp_pdf_import_ckpt.json"
SAFE = "西方_弗朗西斯_培根_新大西岛.pdf"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
# ⚠ 2026-08-08 事故修正：前端本地 dev 读 app/public/backend/data/book_chapters，必须双写
DST2 = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

def norm(s):
    return re.sub(r"\s+", "", s or "")

CH_TITLES = ["正文"]
N = len(CH_TITLES)
SKIP_PAGES = {0, 1, 39}
STRIP_PAGES = {2: ["新大西岛"]}   # p2 正文标题行

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
    sys.exit("checkpoint 连续 5 次读失败，稍后重试")
pages = ckpt["ocr"][SAFE]
npages = {int(k): v for k, v in pages.items() if v and v != "__FAILED__"}
fails = sorted([int(k) for k, v in pages.items() if v == "__FAILED__"])
print(f"OCR 页: {min(npages)}-{max(npages)} 共 {len(npages)} 页, fail {len(fails)} 页: {fails}")

# ---- 单章（页级段落范式） ----
paras = []
for i in sorted(npages):
    if i in SKIP_PAGES:
        continue
    ls = [ln.strip() for ln in npages[i].split("\n") if ln.strip()]
    if i in STRIP_PAGES:
        ls = [l for l in ls if l not in STRIP_PAGES[i]]
    if ls:
        paras.append("".join(ls))
files = {}
files[0] = {"index": 0, "title": CH_TITLES[0],
            "content": [{"type": "text", "value": p} for p in paras]}
nc = sum(len(norm(p)) for p in paras)
print(f"[0] {CH_TITLES[0]} {nc}字 {len(paras)}段 | {norm(paras[0])[:36]!r} … {norm(paras[-1])[-22:]!r}")

# ---- 验证 ----
total = sum(sum(len(norm(b["value"])) for b in files[idx]["content"]) for idx in range(N))
print(f"\n新总净: {total}")
all_text = "".join(norm(b["value"]) for idx in range(N) for b in files[idx]["content"])
bad_page = [norm(b["value"])[:8] for idx in range(N) for b in files[idx]["content"]
            if re.match(r"[一-鿿]\d{2,3}", norm(b["value"]))]
print("页码粘连清零:", "✓" if not bad_page else f"✗ {bad_page[:6]}")
bad_s = [norm(b["value"]) for idx in range(N) for b in files[idx]["content"]
         if re.match(r"^\d{1,4}$", norm(b["value"]))]
print("独立页码清零:", "✓" if not bad_s else f"✗ {bad_s[:5]}")
bad_en = [f"段{n}" for n, b in enumerate(files[0]["content"])
          if len(re.findall(r"[A-Za-z]", b["value"])) > len(b["value"]) * 0.4]
print("英文残留:", "✓" if not bad_en else f"✗ {bad_en[:5]}")
ch = {idx: "".join(norm(b["value"]) for b in files[idx]["content"]) for idx in range(N)}
checks = [(0, "正文", "开航")]
print("验证:", "  ".join(f"{'✓'+t if kw in ch[i] else '✗'+t+'!'}" for i, t, kw in checks))

# ---- toc ----
toc = [{"type": "chapter", "title": files[i]["title"], "index": i, "level": 1} for i in range(N)]
print(f"\ntoc 项: {len(toc)}")

if "--dry" in sys.argv:
    sys.exit(0)

# ---- 写入（旧 1 章自动数据 → 备份 _old_bad） ----
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
    "bookId": BID, "title": "新大西岛", "author": "弗朗西斯·培根",
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
