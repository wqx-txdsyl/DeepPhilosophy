# -*- coding: utf-8 -*-
"""#未入清单 伦理学（32fb0956b9b1，斯宾诺莎）补录修复
病因: OCR 完成的 20 本未入清单书之一。books.json cc=0（从未章节化，
  book_chapters 无目录无数据，book_detail 仅有基础信息）。
源: F:/philosophy/西方/巴鲁赫·斯宾诺莎/伦理学.pdf（174 页扫描版，
  贺麟译，商务印书馆'汉译世界学术名著丛书'，checkpoint OCR 174 页 fail 9：
  8/155/156/157/158/159/171/172/173；书内页码 = PDF页 - 6）
结构（目录 p7 确认 5 部分 + 译后记，本 PDF 只含前 3 部分）:
  p0-2 封面/CIP ｜ p3-6 出版说明（目录无，跳过；书内 i-iv 罗马页码）
  p7 目录 ｜ p8 fail 目录尾页（跳过）
  p9-49 第一部分 论神（书内 1-43；p9 章前+正文起'界说'）
  p50-101 第二部分 论心灵的性质和起源（书内 44-95）
  p102-170 第三部分 论情感的起源和性质（书内 96-164）
    ——p155-159 fail = 书内 149-153 正文 5 页（内容断裂 p154'此证。'→p160 新命题，待重 OCR 补录）
  p171 fail = 书内 165（第三部分尾页，缺） ｜ p172-173 fail = 书内 166-167（第四部分头 2 页，缺）
  ⚠ PDF 残本：第四部分（书内 166+）、第五部分（236+）、译后记（269+）整体缺失（174 页后无内容）
页眉系统: 奇数页章名页眉（'第X部分论…'，OCR 变体'论情的起源和性质'）
  偶数页书名+页码页眉（'伦理学'+'N' 两行）；p23 页眉区 OCR 噪声'图卡第'；
  p163 页眉后跟书内页码行'157'；p23 行'4。'页码噪声
修复: 新建 3 章（无旧数据可备份）:
  页眉过滤: 章名前缀'第[一二三四五]部分论' / 书名行'伦理学' / 裸数字页码（含'4。'）逐层剥首行；
  '图卡第'噪声行页内剔除；
  段落: 每页过滤后行拼接为一段（OCR 书范式）；
  fail 页缺内容如实保留；第四/五部分+译后记 PDF 缺失不补不编造。
  待办: OCR 队列完成后重 OCR p155-159/p171-173 补录 8 页正文。
用法: python _xr_32fb0956b9b1_lxx_rebuild.py [--dry]
"""
import json, os, re, sys, shutil

BID = "32fb0956b9b1"
CKPT = r"f:\program\Python\PhiAgent\backend\data\dp_pdf_import_ckpt.json"
SAFE = "西方_巴鲁赫_斯宾诺莎_伦理学.pdf"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

def norm(s):
    return re.sub(r"\s+", "", s or "")

# 3 章: (idx, 标题, 起始页, 结束页) — PDF 页
CH = [
    (0, "第一部分 论神", 9, 49),
    (1, "第二部分 论心灵的性质和起源", 50, 101),
    (2, "第三部分 论情感的起源和性质", 102, 170),   # p155-159 fail 缺中段；p171-173 fail 为尾页+第四部分头页
]
# 章名页眉（前缀匹配，容 OCR 变体'论情的'）
HEADER_RE = re.compile(r"^第[一二三四五]部分论")
# 偶数页书名页眉
BOOK_HEADER = "伦理学"
# 书内页码（页眉区/页码行，含'4。'噪声）
BARE_NUM_RE = re.compile(r"^\d{1,4}[。.]?$")
# 页内噪声行（p23 页眉区 OCR 噪声）
STRIP_TITLES = {"图卡第"}

ckpt = json.load(open(CKPT, encoding="utf-8"))
pages = ckpt["ocr"][SAFE]
npages = {int(k): v for k, v in pages.items() if v and v != "__FAILED__"}
fails = sorted([int(k) for k, v in pages.items() if v == "__FAILED__"])
print(f"OCR 页: {min(npages)}-{max(npages)} 共 {len(npages)} 页, fail {len(fails)} 页: {fails}")

def page_lines(i):
    """页 → 过滤页眉/书名/页码后的行"""
    t = npages.get(i, "")
    if not t:
        return []
    ls = [ln.strip() for ln in t.split("\n") if ln.strip()]
    if not ls:
        return []
    ls = [l for l in ls if l not in STRIP_TITLES]   # 先剔噪声行（'图卡第'，否则阻塞页眉剥除）
    while ls and (HEADER_RE.match(ls[0]) or ls[0] == BOOK_HEADER
                  or BARE_NUM_RE.fullmatch(ls[0])):
        ls.pop(0)
    return ls

# ---- 逐章解析（页级段落范式） ----
files = {}
for idx, title, p0, p1 in CH:
    paras = []
    for i in range(p0, p1 + 1):
        lss = page_lines(i)
        if lss:
            paras.append("".join(lss))
    if not paras:
        print(f"⚠ 章{idx} {title!r}: 无内容")
    files[idx] = {"index": idx, "title": title,
                  "content": [{"type": "text", "value": p} for p in paras]}
    nc = sum(len(norm(p)) for p in paras)
    first = paras[0][:30] if paras else "(空)"
    last = paras[-1][:22] if paras else ""
    print(f"[{idx:2d}] {title[:26]:<28s} {nc:6d}字 {len(paras):3d}段 | {first!r} … {last!r}")
assert len(files) == 3

# ---- 验证 ----
total = 0
for idx, _, _, _ in CH:
    total += sum(len(norm(b["value"])) for b in files[idx]["content"])
print(f"\n新总净: {total}  (旧无数据, books.json cc=0)")

all_text = "".join(norm(b["value"]) for idx, _, _, _ in CH for b in files[idx]["content"])
# 页眉清零：'伦理学'独立段 / '第X部分论'行不得残留
bad = [norm(b["value"]) for idx, _, _, _ in CH for b in files[idx]["content"]
       if norm(b["value"]) == "伦理学" or HEADER_RE.match(norm(b["value"]))]
print("页眉清零:", "✓" if not bad else f"✗ {bad[:4]}")
# 噪声行清零
print("噪声清零:", "✓" if "图卡第" not in all_text else "✗")
# 关键内容验证
ch = {idx: "".join(norm(b["value"]) for b in files[idx]["content"]) for idx, _, _, _ in CH}
checks = [
    (0, "第一部分", "自因"),
    (1, "第二部分", "我现在进而说明从神或永恒无限的存在的本质必然而出的那些东西"),
    (2, "第三部分", "大部分写文章谈论人类的情感和生活方式的人"),
]
print("验证:", "  ".join(f"{'✓'+t if kw in ch[i] else '✗'+t+'!'}" for i, t, kw in checks))
# 断裂确认（fail 页前后不连续属预期）
print("第三部分 p154尾含'此证':", "此证" in ch[2])

# ---- toc ----
toc = [{"type": "chapter", "title": files[i]["title"], "index": i, "level": 1} for i in range(3)]
print(f"\ntoc 项: {len(toc)}")
for t in toc:
    print(f"  {t['type']:8s} idx{t['index']} {t['title'][:36]}")

if "--dry" in sys.argv:
    sys.exit(0)

# ---- 写入（无旧数据，不备份） ----
if os.path.isdir(SRC):
    print("⚠ SRC 已存在，跳过（不应发生——本书无旧数据）")
else:
    os.makedirs(SRC)
for idx, title, p0, p1 in CH:
    f = files[idx]
    json.dump({"index": idx, "title": f["title"], "content": f["content"]},
              open(os.path.join(SRC, f"{idx}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
meta = {
    "bookId": BID, "title": "伦理学", "author": "巴鲁赫·斯宾诺莎",
    "toc": toc, "cover": None, "chapterCount": 3,
    "chapterTitles": [files[i]["title"] for i in range(3)],
}
json.dump(meta, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print(f"✓ 写入 {SRC}: 3 章 + meta.json")

shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
print("✓ 同步 DP chapters")

for p in (DETAIL_SRC, DETAIL_DST):
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))
        d["toc"] = toc
        d["chapterCount"] = 3
        d["chapterTitles"] = meta["chapterTitles"]
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
        print(f"✓ book_detail 更新: {p}")

if os.path.exists(BOOKS_JSON):
    bj = json.load(open(BOOKS_JSON, encoding="utf-8"))
    bl = bj if isinstance(bj, list) else bj.get("books", [])
    hit = False
    for b in bl:
        if b.get("id") == BID:
            b["chapterCount"] = 3
            hit = True
    if hit:
        with open(BOOKS_JSON, "w", encoding="utf-8") as f:
            json.dump(bl if isinstance(bj, list) else {**bj, "books": bl}, f,
                      ensure_ascii=False, indent=None)
        print("✓ books.json chapterCount 更新")
    else:
        print("⚠ books.json 未找到该书")
