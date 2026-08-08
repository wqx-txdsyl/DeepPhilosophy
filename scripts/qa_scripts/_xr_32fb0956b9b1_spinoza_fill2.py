# -*- coding: utf-8 -*-
"""斯宾诺莎伦理学补全（主线3 #265）：3 章 → 6 章
补录: fail 8 页（155-159/171-173 临时故障重 OCR）+ 174-273（第4/5部分从未 OCR）+
  275-276（译后记）; p274 空白分隔跳过。p8 白页跳过。
源: F:/philosophy/西方/巴鲁赫·斯宾诺莎/伦理学.pdf（277 页, 贺麟译, 商务印书馆）
补录文本: _xr_spinoza_fill.txt（108 页）+ 单页 OCR（275/276）
页眉（补录区）: 奇页 '第X部分论…'+页码 / 偶页 页码+'伦理学'；部分区 '第X部分论…页码'粘连
标题页: p172 '第四部分论人的奴役或'+'情感的力量' / p242 '第五部分论理智的力量'+'或人的自由' 剥两行
修复: 章2 插 fail 页段; 新章3（第四部分 p172-241）/章4（第五部分 p242-273）/章5（译后记 p275-276）
  段落: 页级拼接（OCR 书范式）; toc 6 章平铺
用法: python _xr_32fb0956b9b1_spinoza_fill2.py [--dry]
"""
import json, os, re, sys, shutil, time

BID = "32fb0956b9b1"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DST2 = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"
AUTHOR = "巴鲁赫·斯宾诺莎"

def norm(s):
    return re.sub(r"\s+", "", s or "")

# 页眉（补录区通用，循环剥页首）
HEAD1 = re.compile(r"^第[三四五]部分论[一-鿿，、或]{2,16}$")        # '第三部分论情感的起源和性质'
HEAD2 = re.compile(r"^第[三四五]部分论[一-鿿，、或]{2,16}\d{1,3}$")  # '第四部分论人的奴投或情感的力量167'
HEAD3 = re.compile(r"^伦理学$")
PAGE = re.compile(r"^\d{1,3}$")
# 标题页（p172/p242）前两行
TITLE_PAGES = {172: ["第四部分论人的奴役或", "情感的力量"],
               242: ["第五部分论理智的力量", "或人的自由"]}

# 解析补录文本（fill.txt 108 页 + 单页 275/276）
HERE = os.path.dirname(os.path.abspath(__file__))
pages = {}
for fn in ("_xr_spinoza_fill.txt", "_xr_spinoza_275.txt"):
    raw = open(os.path.join(HERE, fn), encoding="utf-8").read()
    # fill 格式: '### p155 (686字) ###'；单页格式: '### p275 (3s) 664字 ###'
    for pat in (r"### p(\d+) \((\d+)字\) ###\n(.*?)\n### END ###",
                r"### p(\d+) \(\d+s\) (\d+)字 ###\n(.*?)\n### END ###"):
        for m in re.finditer(pat, raw, re.S):
            pages[int(m.group(1))] = m.group(3)

def page_paras(i, strip_heads=True):
    """页 → 段列表（页级拼接）"""
    t = pages.get(i)
    if not t:
        return []
    ls = [ln.strip() for ln in t.split("\n") if ln.strip()]
    if i in TITLE_PAGES:
        for h in TITLE_PAGES[i]:
            if ls and ls[0] == h:
                ls = ls[1:]
    if i in (275, 276):
        ls = [l for l in ls if l != "译后记"]   # p275 标题 / p276 页眉
    while ls and (HEAD1.match(ls[0]) or HEAD2.match(ls[0])
                  or HEAD3.match(ls[0]) or PAGE.match(ls[0])):
        ls = ls[1:]
    return ["".join(ls)] if ls else []

# ---- 读现有 3 章 ----
meta0 = json.load(open(os.path.join(SRC, "meta.json"), encoding="utf-8"))
chs = [json.load(open(os.path.join(SRC, f"{i}.json"), encoding="utf-8"))
       for i in range(meta0["chapterCount"])]
assert len(chs) == 3, f"现有章节数 {len(chs)} ≠ 3"
old_total = sum(sum(len(norm(b["value"])) for b in c["content"]) for c in chs)
print(f"现有 3 章总净: {old_total}")

# ---- 章2（第三部分）插入 fail 页段 ----
# p160 段定位（checkpoint 原文——不依赖，用现有数据里 p160 内容）
ckpt = json.load(open(r"f:\program\Python\PhiAgent\backend\data\dp_pdf_import_ckpt.json", encoding="utf-8"))
# 锚点: p160 正文中段（页首页码/页眉 '伦理学' 已被入库清洗剥除，故用正文句）
p160_anchor = "设想爱的性质"
ch2 = chs[2]
paras2 = [norm(b["value"]) for b in ch2["content"]]
anchor = next((j for j, v in enumerate(paras2) if p160_anchor in v), None)
assert anchor is not None, f"p160 锚点未找到: {p160_anchor}"
print(f"p160 锚点在章2 段{anchor}/{len(paras2)}: …{p160_anchor}…")
# 155-159 插入到 anchor 前; 171 追加末尾
ins = []
for i in (155, 156, 157, 158, 159):
    p = page_paras(i)
    if p:
        ins.extend(p)
new_content = ch2["content"][:anchor] + [{"type": "text", "value": v} for v in ins] + ch2["content"][anchor:]
p171 = page_paras(171)
if p171:
    new_content = new_content + [{"type": "text", "value": v} for v in p171]
chs[2] = {"index": 2, "title": ch2["title"], "content": new_content}
print(f"章2 插入 {len(ins)} 段(fail 页) + 1 段(p171), 共 {len(new_content)} 段")

# ---- 新章 3/4/5 ----
NEW = [
    ("第四部分 论人的奴役或情感的力量", range(172, 242)),   # p172 标题页 + 正文至 241
    ("第五部分 论理智的力量或人的自由", range(242, 274)),   # p242 标题页 + 正文至 273
    ("译后记", range(275, 277)),                            # p275-276（p274 空白跳过）
]
for title, rng in NEW:
    paras = []
    for i in rng:
        paras.extend(page_paras(i))
    idx = len(chs)
    chs.append({"index": idx, "title": title,
                "content": [{"type": "text", "value": p} for p in paras]})

# ---- 统计 ----
for c in chs:
    nc = sum(len(norm(b["value"])) for b in c["content"])
    first = norm(c["content"][0]["value"])[:32] if c["content"] else "(空)"
    last = norm(c["content"][-1]["value"])[:22] if c["content"] else ""
    print(f"[{c['index']}] {c['title']:<22s} {nc:6d}字 {len(c['content']):3d}段 | {first!r} … {last!r}")
total = sum(sum(len(norm(b["value"])) for b in c["content"]) for c in chs)
print(f"新总净: {total}（+{total - old_total}）")

# ---- 验证 ----
all_text = "".join(norm(b["value"]) for c in chs for b in c["content"])
# 页眉残留
bad_h = [f"章{c['index']}:{norm(b['value'])[:16]}" for c in chs for b in c["content"]
         if re.search(r"^第[三四五]部分论|^伦理学$", norm(b["value"]))]
print("页眉清零:", "✓" if not bad_h else f"✗ {bad_h[:6]}")
ch = {c["index"]: "".join(norm(b["value"]) for b in c["content"]) for c in chs}
checks = [
    (2, "命题五十九"), (2, "情绪的界说"), (2, "敬畏和侮慢"),
    (3, "我把人在控制和克制情感上的软弱无力称为奴役"), (3, "命题六十一"),
    (3, "自由人绝"), (4, "斯多葛"), (4, "最后我进到伦理学的另一部分"),
    (4, "思想和事物的观念"), (4, "幸福就是德性自身"), (5, "斯宾诺莎的"),
    (5, "1958年9月"),
]
print("验证:", "  ".join(f"{'✓'+kw[:8] if kw in ch[i] else '✗'+kw[:8]+'!'}"
                          for i, kw in checks))

toc = [{"type": "chapter", "title": c["title"], "index": i, "level": 1}
       for i, c in enumerate(chs)]
print(f"\ntoc 项: {len(toc)}")

if "--dry" in sys.argv:
    sys.exit(0)

# ---- 写入（旧 3 章 → 备份 _old_bad） ----
if os.path.isdir(SRC):
    suf = "_old_bad"
    i2 = 2
    while os.path.isdir(SRC + suf):
        suf = f"_old_bad{i2}"
        i2 += 1
    os.rename(SRC, SRC + suf)
    print(f"\n备份旧数据 → {os.path.basename(SRC) + suf}")
os.makedirs(SRC)
for c in chs:
    json.dump({"index": c["index"], "title": c["title"], "content": c["content"]},
              open(os.path.join(SRC, f"{c['index']}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
meta = {"bookId": BID, "title": "伦理学", "author": AUTHOR,
        "toc": toc, "cover": None, "chapterCount": len(chs),
        "chapterTitles": [c["title"] for c in chs]}
json.dump(meta, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print(f"✓ 写入 {SRC}: {len(chs)} 章 + meta.json")

shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
print("✓ 同步 DP backend chapters")
shutil.rmtree(DST2, ignore_errors=True)
shutil.copytree(SRC, DST2)
print("✓ 同步 DP app/public chapters")

for p in (DETAIL_SRC, DETAIL_DST):
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))
        d["toc"] = toc
        d["chapterCount"] = len(chs)
        d["chapterTitles"] = meta["chapterTitles"]
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
        print(f"✓ book_detail 更新: {p}")

if os.path.exists(BOOKS_JSON):
    bj = json.load(open(BOOKS_JSON, encoding="utf-8"))
    bl = bj if isinstance(bj, list) else bj.get("books", [])
    hit = False
    for b in bl:
        if b.get("id") == BID:
            b["chapterCount"] = len(chs)
            hit = True
    if hit:
        with open(BOOKS_JSON, "w", encoding="utf-8") as f:
            json.dump(bl if isinstance(bj, list) else {**bj, "books": bl}, f,
                      ensure_ascii=False, indent=None)
        print("✓ books.json chapterCount 更新")
    else:
        print("⚠ books.json 未找到该书")
