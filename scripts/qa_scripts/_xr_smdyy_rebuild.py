# -*- coding: utf-8 -*-
"""#156 生命的意义（威尔·杜兰特）30cc02edc262 修复
病因（CHKLIST ✗B 三部分从"1"重新编号 + 部分标题缺失）:
  旧 20 章：① 缺三个部分标题页（第一章 生命的意义之问/第二章 生命的意义之答/
  第三章 给自杀者的信）——三部分节号各自从 1 起，toc 无法区分；
  ② 缺"目录"章；③ 第三章页的脚注说明（[1]1930年我收到几封信…191 字）被
  误放进旧 12"不可知论者"章尾（旧 12 816 字 vs 源 629）。
源（F:/philosophy/西方/威尔·杜兰特/生命的意义威尔.杜兰特.epub，25 spine）：
  h1=部分标题页（[4][12][17]，其中 [17] 含 191 字脚注说明）、h2=节标题（16 个，
  数字开头无空格）、p=正文；每节独立文件；正文无图。
修复:
  基于源全量重建 21 章 + 3 part（#144 part 模式）：
  0 扉页｜1 目录（新增）｜2 推荐序｜3-9 问题缘由~大结局（7 节）
  part 第一章 生命的意义之问 → 10-13 文学家的观点~不可知论者（4 节）
  part 第二章 生命的意义之答 → 14-18 自杀的流行~我的邀请（5 节，14 章含
  第三章页脚注说明 191 字）｜19 附录…｜20 版权页；
  节标题数字后补空格（"1问题缘由"→"1 问题缘由"）；
  部分标题去脚注编号（"第三章给自杀者的信[1]"→"第三章 给自杀者的信"）。
旧 20 章正文逐节与源吻合（差异 ≤19 字）→ 源为准重建。
用法: python _xr_smdyy_rebuild.py [--dry]
"""
import json, os, re, sys, shutil, zipfile
from bs4 import BeautifulSoup

BID = "30cc02edc262"
EPUB = "F:/philosophy/西方/威尔·杜兰特/生命的意义威尔.杜兰特.epub"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

# 章 → 源 spine 文件组（标题页 [4][12][17] 仅 part，[17] 的 p 并入 14 章）
FILE_PLAN = {
    0: [0, 1], 1: [2], 2: [3], 3: [5], 4: [6], 5: [7], 6: [8], 7: [9],
    8: [10], 9: [11], 10: [13], 11: [14], 12: [15], 13: [16],
    14: [17, 18], 15: [19], 16: [20], 17: [21], 18: [22], 19: [23], 20: [24],
}
TITLES = {
    0: "扉页", 1: "目录", 2: "推荐序",
    3: "1 问题缘由", 4: "2 宗教", 5: "3 科学", 6: "4 历史", 7: "5 乌托邦",
    8: "6 思想者的自我毁灭", 9: "7 大结局",
    10: "1 文学家的观点", 11: "2 从好莱坞到恒河——其他人士的回答",
    12: "3 三位女性的回答", 13: "4 不可知论者和懒于思考者的回答",
    14: "1 自杀的流行", 15: "2 看开一点儿", 16: "3 维多利亚时代中期",
    17: "4 个人自白", 18: "5 我的邀请",
    19: "附录 纽约兴格监狱编号为79206的囚犯的来信", 20: "版权页",
}
PARTS = [
    (3, "第一章 生命的意义之问"),
    (10, "第二章 生命的意义之答"),
    (14, "第三章 给自杀者的信"),
]

def norm(s):
    return re.sub(r"\s+", "", s or "")

def clean_h2(t):
    """节标题：'1问题缘由' → '1 问题缘由'"""
    return re.sub(r"^(\d+)(?=\S)", r"\1 ", t).strip()

def clean_h1(t):
    """部分标题：去 [N] 脚注 + 补空格：'第三章给自杀者的信[1]' → '第三章 给自杀者的信'"""
    t = re.sub(r"\[\d+\]", "", t).strip()
    t = re.sub(r"^(第一|第二|第三)章(?=\S)", r"\1章 ", t)
    return t.strip()

z = zipfile.ZipFile(EPUB)
names = z.namelist()
def soup_of(i):
    """spine[i] 的真实文件名：i=0 → titlepage.xhtml；i≥1 → part{i-1}.html"""
    fn = "titlepage.xhtml" if i == 0 else f"part{i - 1:04d}.html"
    cand = [n for n in names if n.split("/")[-1] == fn]
    if not cand:
        raise SystemExit(f"找不到 spine 文件 {fn}")
    return BeautifulSoup(z.read(cand[0]).decode("utf-8", "ignore"), "html.parser")

# ---- 逐章解析（h2=节标题→章标题；p=正文块；h1 仅 part 页）----
# 扉页(0)/目录(1)/版权页(20) 的内容在 div 中（仅取叶子 div 避免嵌套重复）
DIV_MODE = {0: {0, 1}, 1: {2}, 20: {24}}
files = {}
for idx, group in FILE_PLAN.items():
    content, h1_found = [], None
    for gi in group:
        soup = soup_of(gi)
        if idx in DIV_MODE and gi in DIV_MODE[idx]:
            for el in soup.find_all("div"):
                if el.find("div") is not None:
                    continue  # 跳过含子 div 的容器
                t = el.get_text("", strip=True)
                if t:
                    content.append({"type": "text", "value": t})
            continue
        for el in soup.find_all(["h1", "h2", "p"]):
            if el.name == "h1":
                h1_found = clean_h1(el.get_text(" ", strip=True))
            elif el.name == "h2":
                pass  # 节标题即章标题，不产生块
            else:
                t = el.get_text("", strip=True)
                if not t or "ePUBw" in t:
                    continue
                content.append({"type": "text", "value": t})
    files[idx] = {"index": idx, "title": TITLES[idx], "content": content}

assert len(files) == 21, len(files)

# ---- 逐块 diff（重建 p 块 vs 源 p 逐对对比）----
bad = 0
for idx, group in FILE_PLAN.items():
    f = files[idx]
    ps = [b["value"] for b in f["content"] if b.get("type") == "text"]
    sps = []
    for gi in group:
        soup = soup_of(gi)
        if idx in DIV_MODE and gi in DIV_MODE[idx]:
            for el in soup.find_all("div"):
                if el.find("div") is not None:
                    continue
                t = el.get_text("", strip=True)
                if t:
                    sps.append(t)
            continue
        for p in soup.find_all("p"):
            t = p.get_text("", strip=True)
            if t and "ePUBw" not in t:
                sps.append(t)
    if len(ps) != len(sps):
        print(f"[{idx}] {f['title'][:22]}: 重建 {len(ps)} p vs 源 {len(sps)} p *** 块数不同 ***")
        bad += 1
    for k, (b, s) in enumerate(zip(ps, sps)):
        if b != s:
            print(f"[{idx}] 块{k} 不匹配:\n  重建({len(b)}): {b[:60]}\n  源  ({len(s)}): {s[:60]}")
            bad += 1
            if bad > 12:
                raise SystemExit("差异过多，终止")
print(f"逐块 diff: {0 if bad == 0 else bad} 处不匹配")
if bad:
    raise SystemExit("块级验证失败")

# ---- 字数对照 ----
print("=== 21 章重建（源净字数对照）===")
total = 0
for idx in range(21):
    f = files[idx]
    nc = sum(len(norm(b.get("value", ""))) for b in f["content"])
    total += nc
    src_txt = sum(len(norm(soup_of(gi).get_text("", strip=True))) for gi in FILE_PLAN[idx])
    print(f"[{idx:2d}] {f['title'][:28]:<30s} {nc:6d}字净 {len(f['content']):4d}块  源{src_txt:6d}  差{nc-src_txt:+6d}")
print(f"新总净: {total}")
old_total = 0
for i in range(20):
    p = os.path.join(SRC, f"{i}.json")
    if os.path.exists(p):
        ch = json.load(open(p, encoding="utf-8"))
        old_total += sum(len(norm(b.get("value", ""))) for b in ch["content"])
print(f"旧总净: {old_total}  差: {total-old_total:+d}（+目录章+第三章说明归位）")
print("新0首块:", files[0]["content"][0]["value"][:30], "| 新0末块:", files[0]["content"][-1]["value"][:30])
print("新1首块:", files[1]["content"][0]["value"][:30])
print("新14首块:", files[14]["content"][0]["value"][:40], "| 新14末块:", files[14]["content"][-1]["value"][:30])
print("新20末块:", files[20]["content"][-1]["value"][:30])

if "--dry" in sys.argv:
    sys.exit(0)

# ---- toc ----
toc = []
for idx in range(21):
    toc.append({"type": "chapter", "title": files[idx]["title"], "index": idx, "level": 1})
out = []
pit = iter(PARTS)
next_part = next(pit, None)
for t in toc:
    if next_part and t["type"] == "chapter" and t["index"] == next_part[0]:
        out.append({"type": "part", "title": next_part[1], "index": next_part[0], "level": 0})
        next_part = next(pit, None)
    out.append(t)
toc = out
meta_new = {
    "chapterCount": 21,
    "chapterTitles": [files[i]["title"] for i in range(21)],
    "toc": toc,
}
print("\n=== toc ===")
for t in toc:
    print(f"  {t['type']:8s} idx{t['index']:2d} lv{t.get('level')} {t['title'][:36]}")

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
for idx in range(21):
    f = files[idx]
    json.dump({"index": idx, "title": f["title"], "content": f["content"]},
              open(os.path.join(SRC, f"{idx}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
meta = {
    "bookId": old_meta.get("bookId") or BID,
    "title": old_meta.get("title") or "生命的意义",
    "author": old_meta.get("author") or "威尔·杜兰特",
    "toc": toc,
    "cover": old_meta.get("cover"),
    "chapterCount": 21,
    "chapterTitles": meta_new["chapterTitles"],
}
json.dump(meta, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print(f"✓ 写入 {SRC}: 21 章 + meta.json")

shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
print("✓ 同步 DP chapters")

for p in (DETAIL_SRC, DETAIL_DST):
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))
        d["toc"] = toc
        d["chapterCount"] = 21
        d["chapterTitles"] = meta_new["chapterTitles"]
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
        print(f"✓ book_detail 更新: {p}")

if os.path.exists(BOOKS_JSON):
    bj = json.load(open(BOOKS_JSON, encoding="utf-8"))
    bl = bj if isinstance(bj, list) else bj.get("books", [])
    hit = False
    for b in bl:
        if b.get("id") == BID:
            b["chapterCount"] = 21
            hit = True
    if hit:
        with open(BOOKS_JSON, "w", encoding="utf-8") as f:
            json.dump(bl if isinstance(bj, list) else {**bj, "books": bl}, f,
                      ensure_ascii=False, indent=None)
        print("✓ books.json chapterCount 更新")
    else:
        print("⚠ books.json 未找到该书")
