# -*- coding: utf-8 -*-
"""尼采与哲学（e7c27b39a87c）抽查6修复
① 删章1 末段（'二、能动与反动' 标题粘连 + 章2 首段 531 字重复副本——用户'一悲剧末尾出现二能动与反动'）
② section 标题行（'N. xxx'/'结论' 等）嵌在正文段首行 → 拆出独立段，重算 toc sec 段索引
保留: 行内注释标号（①/❶，引用标注）、独立注释段（页脚注文本已独立成段）、页级拼接正文
"""
import json, os, re, sys, shutil

BID = "e7c27b39a87c"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DST2 = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

TITLE_RE = re.compile(r"^\d{1,2}\.\s*[^\d].{2,24}$")   # '2. 意义' / '14. 尼采与马拉美'
END_TITLE = re.compile(r"^结论$")

def norm(s):
    return re.sub(r"\s+", "", s or "")

meta0 = json.load(open(os.path.join(SRC, "meta.json"), encoding="utf-8"))
chs = [json.load(open(os.path.join(SRC, f"{i}.json"), encoding="utf-8"))
       for i in range(meta0["chapterCount"])]

# ① 章1 末段删除确认（与章2 首段重叠）
c0, c1 = chs[0], chs[1]
last0 = norm(c0["content"][-1].get("value", ""))
first1 = norm(c1["content"][0].get("value", ""))
assert last0.startswith("二、能动与反动"), last0[:20]
assert first1.startswith("1.身体"), first1[:20]
# 章1 末段去掉标题后是否被章2 首段包含
print(f"章1 末段 {len(last0)} 字 (待删) | 章2 首段 {len(first1)} 字")
print(f"包含关系: {first1.startswith(last0[7:])}")
# 删除章1 末段
chs[0]["content"] = chs[0]["content"][:-1]
print("✓ 章1 末段已删")

# ② 拆标题行
new_chs = []
for ci, c in enumerate(chs):
    paras = c["content"]
    new_paras = []
    for b in paras:
        if b.get("type") != "text":
            new_paras.append(b)
            continue
        v = b.get("value", "")
        lines = v.split("\n")
        if len(lines) >= 2 and TITLE_RE.match(lines[0].strip()):
            new_paras.append({"type": "text", "value": lines[0].strip()})
            new_paras.append({"type": "text", "value": "\n".join(lines[1:])})
        else:
            new_paras.append(b)
    new_chs.append({"index": ci, "title": c["title"], "content": new_paras})

# 统计
for ci, c in enumerate(new_chs):
    n = sum(len(norm(b.get("value",""))) for b in c["content"] if b.get("type")=="text")
    print(f"[{ci}] {c['title']}: {len(c['content'])}段 {n}字 (原{len(chs[ci]['content'])}段)")

# 重算 sec: 标题段（TITLE_RE 匹配整段）的位置即 sec；逐章扫描
new_toc = []
for t in meta0["toc"]:
    if t.get("type") == "section":
        ci = t["index"]
        title = norm(t["title"])
        paras = new_chs[ci]["content"]
        # 找该 section 标题匹配的段（标题段：整段只有标题 或 首行=标题）
        hit = None
        for i, b in enumerate(paras):
            if b.get("type") != "text":
                continue
            first_line = b["value"].split("\n")[0].strip()
            if norm(first_line) == title or norm(b["value"]) == title:
                hit = i
                break
        if hit is None:
            print(f"  ⚠ section 标题未定位: [{ci}] {title}")
        new_toc.append({"type": "section", "title": t["title"], "index": ci, "sec": hit if hit is not None else t["sec"], "level": 2})
    else:
        new_toc.append(t)
# 章1 末段已删 → toc 里 chapter/section 索引不变（只删 content 段），但需确认 toc 无引用
print("toc 项数:", len(new_toc))

if "--dry" in sys.argv:
    sys.exit(0)

# 写入
if os.path.isdir(SRC):
    suf = "_old_bad"
    i2 = 2
    while os.path.isdir(SRC + suf):
        suf = f"_old_bad{i2}"
        i2 += 1
    os.rename(SRC, SRC + suf)
    print(f"\n备份 → {os.path.basename(SRC) + suf}")
os.makedirs(SRC)
for c in new_chs:
    json.dump({"index": c["index"], "title": c["title"], "content": c["content"]},
              open(os.path.join(SRC, f"{c['index']}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
meta0["toc"] = new_toc
meta0["chapterCount"] = len(new_chs)
meta0["chapterTitles"] = [c["title"] for c in new_chs]
json.dump(meta0, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print("✓ 写入 SRC")

shutil.rmtree(DST, ignore_errors=True); shutil.copytree(SRC, DST)
shutil.rmtree(DST2, ignore_errors=True); shutil.copytree(SRC, DST2)
print("✓ 同步 DST/DST2")

for p in (DETAIL_SRC, DETAIL_DST):
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))
        d["toc"] = new_toc
        d["chapterCount"] = len(new_chs)
        d["chapterTitles"] = meta0["chapterTitles"]
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
        print("✓ detail", p)

if os.path.exists(BOOKS_JSON):
    bj = json.load(open(BOOKS_JSON, encoding="utf-8"))
    bl = bj if isinstance(bj, list) else bj.get("books", [])
    for b in bl:
        if b.get("id") == BID:
            b["chapterCount"] = len(new_chs)
    json.dump(bl if isinstance(bj, list) else {**bj, "books": bl},
              open(BOOKS_JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
    print("✓ books.json")
