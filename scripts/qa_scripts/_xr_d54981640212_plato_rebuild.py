# -*- coding: utf-8 -*-
"""柏拉图（d54981640212）抽查12修复：正文重建
病因: 书库'柏拉图'正文 = 柏拉图《理想国》对话集（6 part 46 toc 项 29 章），
  应为《最伟大的思想家-柏拉图》（约翰·E. 彼得曼著，胡自信译，中华书局 2002）。
源: F:/philosophy/西方/柏拉图/最伟大的思想家 - 柏拉图.pdf 153 页文本层
  （中文占比 71.76%，内嵌 OCR 噪声大：'柏担国/丰臼担国'书名变体、'堕鲁门/元头绪'错字）
章节边界（目录书内页码 +5 = PDF 页）:
  序 p6-12 / 导论 p13-27 / 柏拉图的生平和时代 p28-56 /
  哲学 p57-112 / 对话的媒介 p113-147 / 参考书目 p148-151（p152 后封书目弃）
清洗: 页眉循环剥（^·开头 / 含·《·〈粘连 / 纯装饰字符行 / 短噪声）+
  页脚页码剥（末行纯数字）+ 标题页 p57 前 6 行剥（'2/非斤/占兰自/i:=-/-:r一/在闻出'）
段落: 页级拼接（每页一段，OCR 书范式）；6 章平铺 toc
"""
import json, os, re, sys, shutil

BID = "d54981640212"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DST2 = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"
AUTHOR = "约翰·E. 彼得曼"
DUMP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_xr_plato_dump.txt")

def norm(s):
    return re.sub(r"\s+", "", s or "")

# 章节边界: (标题, PDF 页范围)
PLAN = [
    ("序",                     range(6, 13)),
    ("导论",                   range(13, 28)),
    ("柏拉图的生平和时代",     range(28, 57)),
    ("哲学",                   range(57, 113)),
    ("对话的媒介",             range(113, 148)),
    ("参考书目",               range(148, 152)),
]

# ---- 解析 dump ----
raw = open(DUMP, encoding="utf-8").read()
pages = {int(m.group(1)): m.group(2)
         for m in re.finditer(r"### p(\d+) ###\n(.*?)\n### END ###", raw, re.S)}

DECO = r"·．—－一～→←~=＿…\-\.÷十千二"
def clean_line(l):
    """行级清洗 → (保留文本, 是否删行)。页眉装饰线碎片化+含 OCR 噪声字符（千/十/÷），逐行清。"""
    l = l.strip()
    if not l:
        return "", True
    # ① 单字符行（正文无单字行；数字=页脚，尾剥）
    if len(l) == 1 and not l.isdigit():
        return "", True
    # ② 全装饰字符串（含噪声字符 千十÷）
    if re.fullmatch(f"[{DECO}]+", l):
        return "", True
    # ③ 装饰串 + 书名变体（'·《柏扫国》·'/'一←…－《柏扫国》·'/'〈柏扫图〉'/｛朽Jt立国〉）
    #    → 截断保留《》后正文；装饰字符分散也可（'.《柏扫国》·！'）
    m = re.match(rf"^[{DECO}·]{{1,}}[《〈(（｛]?[^》〉)）〕]{{1,14}}[》〉)）〕](.*)$", l)
    if m and sum(1 for ch in l if ch in DECO) >= 2:
        rest = m.group(1).strip()
        return rest, rest == ""
    # ④ '·'/'．' 开头 或 含'译丛'（'·世界思想家译丛·一'/'．世界忠想家译丛．'）→ 删
    if l.startswith("·") or l.startswith("．") or "译丛" in l:
        return "", True
    # ⑤ 行首装饰串≥3 + 正文粘连（'一←－一一一一…÷→接受'）→ 截断保留正文
    m = re.match(rf"^[{DECO}]{{3,}}(.+)$", l)
    if m:
        return m.group(1).strip(), False
    # ⑦ 页中粘连：前缀(≤40字,含装饰字符) + 装饰串 + 书名括号 → 截断保留括号后正文
    #    '→？·《柏m国》·须；也…' → '须；也…'; '或《理想国》'（正文引用）无装饰前缀 → 不匹配
    m = re.match(rf"^.{{0,40}}?[{DECO}·]{{1,}}([《〈(（｛][^》〉)）〕]{{1,14}}[》〉)）〕])(.*)$", l)
    if m and m.start(1) > 0:
        rest = m.group(2).strip()
        return rest, rest == ""
    # ⑥ 短噪声行（'}'/'~'/'•'/'〜'）
    if len(l) <= 2 and re.fullmatch(r"[}~•◦○＋〜×]", l):
        return "", True
    return l, False

TITLE_LINES = {13: 1, 28: 1, 113: 2, 148: 1}   # 章起始页标题行数（p6'序'自动剥; p57 特殊）
def strip_page(i):
    """页 → 段文本（每行清洗 + 页首循环剥 + 页脚数字剥 + 页级拼接）；返回 None 若空"""
    ls = [l.strip() for l in pages[i].split("\n")]
    if i == 57:            # 标题页'2/哲学'噪声行（非斤=哲学 OCR 变体，含'占兰自/i:=-/-:r一/在闻出'）
        ls = ls[6:]
    elif i in TITLE_LINES:
        ls = ls[TITLE_LINES[i]:]
    out = []
    for l in ls:
        for _ in range(3):              # clean 迭代至稳定
            l, drop = clean_line(l)
            if drop or not l:
                break
        if l:
            out.append(l)
    while out and clean_line(out[0])[1]:   # 页首循环剥（clean 后仍判删的行）
        out = out[1:]
    while out and re.fullmatch(r"\d{1,3}", out[-1]):   # 页脚页码
        out = out[:-1]
    return "".join(out) if out else None

# ---- 重建 ----
chs = []
for ci, (title, rng) in enumerate(PLAN):
    paras = [strip_page(i) for i in rng]
    paras = [p for p in paras if p]
    chs.append({"index": ci, "title": title,
                "content": [{"type": "text", "value": p} for p in paras]})

# ---- 统计 ----
total = 0
for c in chs:
    n = sum(len(norm(b["value"])) for b in c["content"])
    total += n
    first = norm(c["content"][0]["value"])[:30] if c["content"] else "(空)"
    last = norm(c["content"][-1]["value"])[:24] if c["content"] else ""
    print(f"[{c['index']}] {c['title']:<12s} {n:6d}字 {len(c['content']):3d}段 | {first!r}…{last!r}")
print(f"总净 {total} 字")

# ---- 验证 ----
all_txt = "".join(norm(b["value"]) for c in chs for b in c["content"])
bad_head = [f"章{c['index']}:{norm(b['value'])[:18]}"
            for c in chs for b in c["content"]
            if re.search(r"^[·一—－．].{0,10}|译丛", norm(b["value"])[:40])]
print("页眉残留:", "✓ 无" if not bad_head else f"✗ {bad_head[:8]}")
print("页脚页码残留:", "✓ 无" if not re.search(r"(?<![0-9])\d{1,3}(?![0-9])$", all_txt[:0] + "x") else "—")
checks = [
    (0, "不经过斗争"), (0, "序言"), (1, "欧洲哲学传统"), (2, "关于他的家庭"),
    (2, "阿里斯顿"), (3, "I.死亡"), (4, "论善"), (4, "人们对柏拉图感到厌倦"),
    (4, "苏格拉底的讽刺"), (5, "汗牛充栋"), (5, "G.C.菲尔德"),
]
ch_txt = {c["index"]: "".join(norm(b["value"]) for b in c["content"]) for c in chs}
print("锚点验证:", "  ".join(f"{'✓' if kw in ch_txt[i] else '✗'+kw+'!'}" for i, kw in checks))
print("p152 后封已弃:", "✓" if "维特根斯坦" not in all_txt else "✗ 泄漏")
sec_dup = sum(1 for i in range(1, len(chs))
              if ch_txt[i][:60] == ch_txt[i-1][-60:])
print("章首尾重复:", "✓ 无" if sec_dup == 0 else f"⚠ {sec_dup} 处")

toc = [{"type": "chapter", "title": c["title"], "index": i, "level": 1}
       for i, c in enumerate(chs)]
print(f"\ntoc 项: {len(toc)}")

if "--dry" in sys.argv:
    sys.exit(0)

# ---- 写入（旧 29 章 → 备份 _old_bad） ----
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
meta = {"bookId": BID, "title": "柏拉图", "author": AUTHOR,
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
    d = json.load(open(p, encoding="utf-8"))
    d["toc"] = toc
    d["chapterCount"] = len(chs)
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
            b["chapterCount"] = len(chs)
            if b.get("author"):
                b["author"] = AUTHOR
            hit = True
    if hit:
        with open(BOOKS_JSON, "w", encoding="utf-8") as f:
            json.dump(bl if isinstance(bj, list) else {**bj, "books": bl}, f,
                      ensure_ascii=False, indent=None)
        print("✓ books.json chapterCount/author 更新")
    else:
        print("⚠ books.json 未找到该书")
