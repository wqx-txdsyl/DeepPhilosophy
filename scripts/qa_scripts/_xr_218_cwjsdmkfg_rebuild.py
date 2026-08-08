# -*- coding: utf-8 -*-
"""#218 重返世界尽头的咖啡馆（747c2bf54af0）修复
病因（CHKLIST ✗D：'扉页/序+01~57 纯数字章标题，节名缺失'）:
  ① idx0 扉页章残留：书名页图片 + CIP 版权页（'图书在版编目（CIP）数据'）被建章，
     #196 范式：书级页不建章 → 剔除；
  ② 57 个数字章每章首块为空字符串 ''（epub→章节化转换残留）→ 清理；
  ③ '节名缺失'不成立：源 epub（果麦版，ncx）版式即纯编号'01'~'57'，小说本无章名
     （同 #205 结论），数字标题忠实保留。
勘察对照：旧 idx1-58（序+01~57）内容与 epub 源逐章字数完全一致（序 298 字、
01 1774 字…逐一对应），内容完好 → 重排保留，不重建。
源: F:/philosophy/西方/约翰·史崔勒基/重返世界尽头的咖啡馆.epub
   （北京联合出版公司 2022 果麦文化，万洁译；spine 65 = 扉页/CIP/果麦出品/序/01-57/版权页）
修复: 重排章节文件（1-58 → 0-57）+ toc 重建:
  0 序 ｜ 1-57 = 01~57（数字章标题忠实源）
  chapterCount 59→58；双端 meta/book_detail/books.json 同步。
用法: python _xr_218_cwjsdmkfg_rebuild.py [--dry]
"""
import json, os, re, sys, shutil

BID = "747c2bf54af0"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

def norm(s):
    return re.sub(r"\s+", "", s or "")

# 旧 idx → 新 idx 映射（旧 0 扉页剔除）
MOVE = {i: i - 1 for i in range(1, 59)}

# ---- 读旧章（内容原样保留，仅重编号 + 清首块空串） ----
files = {}
for old, new in MOVE.items():
    ch = json.load(open(os.path.join(SRC, f"{old}.json"), encoding="utf-8"))
    ch["index"] = new
    # 清首块空字符串（epub 转换残留）
    cleaned = 0
    while ch["content"] and ch["content"][0].get("type", "text") == "text" \
            and not norm(ch["content"][0].get("value", "")):
        ch["content"].pop(0)
        cleaned += 1
    files[new] = ch
    imgs = sum(1 for b in ch["content"] if b.get("type") == "image")
    nc = sum(len(norm(b.get("value", ""))) for b in ch["content"])
    first = ch["content"][0].get("value", "(图)")[:26] if ch["content"] else "(空)"
    print(f"[{new:2d}] ← 旧{old:2d} {ch['title'][:8]:<10s} {nc:6d}字 {len(ch['content']):3d}块 (清{cleaned}图{imgs}) | 首: {first!r}")
assert len(files) == 58

# ---- toc 重建（58 × chapter level1，标题原样忠实源） ----
toc = [{"type": "chapter", "title": files[i]["title"], "index": i, "level": 1} for i in range(58)]
print(f"\ntoc 项: {len(toc)}")
for t in toc[:4] + toc[-2:]:
    print(f"  {t['type']:8s} idx{t['index']} {t['title'][:36]}")

# ---- 字数对照 ----
total = 0
for i in range(58):
    total += sum(len(norm(b.get("value", ""))) for b in files[i]["content"])
print(f"\n新总净: {total}")
old_total = 0
for i in range(59):
    ch = json.load(open(os.path.join(SRC, f"{i}.json"), encoding="utf-8"))
    old_total += sum(len(norm(b.get("value", ""))) for b in ch["content"])
print(f"旧总净(含扉页): {old_total}  差: {total - old_total:+d}（= 剔扉页 609 + 清空块）")

# ---- 验证 ----
# ① 无空块
bad = [i for i in range(58) if any(b.get("type", "text") == "text" and not norm(b.get("value", "")) for b in files[i]["content"])]
print("空块清零:", "✓" if not bad else f"✗ {bad}")
# ② 无扉页章
print("扉页剔除:", "✓" if all("CIP" not in norm(b.get("value", "")) for i in range(58) for b in files[i]["content"]) else "✗")
# ③ 关键句（首章与末章）
ch0 = "".join(norm(b.get("value", "")) for b in files[0]["content"])
ch57 = "".join(norm(b.get("value", "")) for b in files[57]["content"])
print("关键句:", "✓序含'为什么咖啡馆'" if "为什么咖啡馆" in ch0 else "✗序!",
      "✓57章含'重返世界尽头的咖啡馆'" if "重返世界尽头的咖啡馆" in ch57 else "✗57章!")
# ④ 标题无乱码
print("标题乱码清零:", "✓" if not any(re.search(r"[cwww]|�", norm(t["title"])) for t in toc) else "✗!")

if "--dry" in sys.argv:
    sys.exit(0)

# ---- 写入 ----
if os.path.isdir(SRC):
    suf = "_old_bad"
    i2 = 2
    while os.path.isdir(SRC + suf):
        suf = f"_old_bad{i2}"
        i2 += 1
    os.rename(SRC, SRC + suf)
    print(f"\n备份旧数据 → {os.path.basename(SRC) + suf}")
os.makedirs(SRC)
old_meta = {}
old_bid = SRC + "_old_bad"
if os.path.isdir(old_bid) and os.path.exists(os.path.join(old_bid, "meta.json")):
    old_meta = json.load(open(os.path.join(old_bid, "meta.json"), encoding="utf-8"))
for new in range(58):
    ch = files[new]
    json.dump({"index": new, "title": ch["title"], "content": ch["content"]},
              open(os.path.join(SRC, f"{new}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
meta = {
    "bookId": old_meta.get("bookId") or BID,
    "title": old_meta.get("title") or "重返世界尽头的咖啡馆",
    "author": old_meta.get("author") or "约翰·史崔勒基",
    "toc": toc,
    "cover": old_meta.get("cover"),
    "chapterCount": 58,
    "chapterTitles": [files[i]["title"] for i in range(58)],
}
json.dump(meta, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print(f"✓ 写入 {SRC}: 58 章 + meta.json")

shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
print("✓ 同步 DP chapters")

for p in (DETAIL_SRC, DETAIL_DST):
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))
        d["toc"] = toc
        d["chapterCount"] = 58
        d["chapterTitles"] = meta["chapterTitles"]
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
        print(f"✓ book_detail 更新: {p}")

if os.path.exists(BOOKS_JSON):
    bj = json.load(open(BOOKS_JSON, encoding="utf-8"))
    bl = bj if isinstance(bj, list) else bj.get("books", [])
    hit = False
    for b in bl:
        if b.get("id") == BID:
            b["chapterCount"] = 58
            hit = True
    if hit:
        with open(BOOKS_JSON, "w", encoding="utf-8") as f:
            json.dump(bl if isinstance(bj, list) else {**bj, "books": bl}, f,
                      ensure_ascii=False, indent=None)
        print("✓ books.json chapterCount 更新")
    else:
        print("⚠ books.json 未找到该书")
