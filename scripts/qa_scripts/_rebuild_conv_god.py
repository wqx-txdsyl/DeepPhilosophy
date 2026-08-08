# -*- coding: utf-8 -*-
"""《与神对话(全5卷)》重建 — 117 章 + 三级分级标题(5卷 part + 76 章真实命名 + 与神合一 21 幻觉章)
- 库旧 111 章: 卷1-4 机械标题 Chapter 01-76(每章首段=标题行残留), 与神合一 21 幻觉章被压成 3 大章(真实标题丢失)
- 源 epub 结构: 每文件=一章(h1=真实标题), 与神合一幻觉章 h1="1.需求的幻觉"等真实标题
- 重建: 每文件一章, Chapter NN → 第X章(汉字), 5 卷 part(level 0) + 与神合一内部 3 部分 part(level 1)
- 零丢失验证: 新库段落流 == 黄金流逐段; 旧库段落全覆盖(extra 段列出人工确认=标题行/目录/CIP)
"""
import sys, re, json, zipfile, os, shutil
from html.parser import HTMLParser
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, r"f:\program\Python\PhiAgent\backend\tools")
import rebuild_auto as ra

BID = "7657ef4a2cd3"
EP = r"F:/philosophy/西方/尼尔·唐纳德·沃尔什/与神对话(全5卷）.epub"
D = os.path.join(ra.CH, BID)
BAK = os.path.join(os.path.dirname(ra.CH), "_rebuild_bak", f"{BID}_old111ch")

CN = ["零", "一", "二", "三", "四", "五", "六", "七", "八", "九", "十",
      "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十", "二十一"]

class PExtract(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.cur = None; self.buf = []; self.blocks = []
    def handle_starttag(self, tag, attrs):
        if tag == "p": self.cur = "p"; self.buf = []
        elif re.match(r"h[1-6]$", tag): self.cur = "h"; self.buf = []
    def handle_endtag(self, tag):
        if tag == "p" and self.cur == "p":
            self.blocks.append(("p", "".join(self.buf))); self.cur = None
        elif re.match(r"h[1-6]$", tag) and self.cur == "h":
            self.blocks.append(("h", "".join(self.buf))); self.cur = None
    def handle_data(self, d):
        if self.cur: self.buf.append(d)

def norm_body(t):
    return re.sub(r"\s+", " ", t).strip()

# ---------- 1. spine 序 ----------
z = zipfile.ZipFile(EP)
opf = [n for n in z.namelist() if n.lower().endswith(".opf")][0]
c = z.read(opf).decode("utf-8", errors="replace")
items = {}
for m in re.finditer(r'<item\b([^>]*)/?>', c):
    attrs = dict(re.findall(r'(\w+)\s*=\s*"([^"]*)"', m.group(1)))
    if attrs.get("href"):
        items[attrs.get("id", "")] = (attrs["href"], os.path.dirname(opf))
order = []
for s in re.findall(r'<itemref\b[^>]*?idref="([^"]+)"', c):
    if s in items:
        href, base = items[s]
        p = (os.path.join(base, href) if not href.startswith(base) else href).replace("\\", "/")
        if p not in z.namelist():
            cand = [n for n in z.namelist() if n.endswith("/" + href)]
            p = cand[0] if cand else p
        order.append(p)

# ---------- 2. 解析每文件 (fn→(hs, ps)) ----------
parsed = {}
for fn in order:
    c2 = z.read(fn).decode("utf-8", errors="replace")
    p = PExtract(); p.feed(c2)
    hs = [norm_body(t) for tag, t in p.blocks if tag == "h"]
    ps = [norm_body(t) for tag, t in p.blocks if tag == "p"]
    parsed[fn] = (hs, [t for t in ps if t])

def fnum(fn):
    m = re.search(r"text(\d{5})\.html$", fn)
    return int(m.group(1)) if m else None

# ---------- 3. 章标题映射 (文件号 → 标题; None=跳过; part 标记) ----------
DEDIC = {6: "献词一", 7: "献词二", 29: "献词", 57: "献词", 87: "献词"}
RE_CHAPTER = re.compile(r"^Chapter (\d+)$", re.I)
RE_ILLUSION = re.compile(r"^\d+\.")
PART_PAGES = {"第一部分 人类的十大幻觉", "第二部分 掌握幻觉", "第三部分 与内在造物主相遇"}
SKIP_NUM = set(range(1, 5)) | set(range(24, 29)) | set(range(52, 57)) | \
           set(range(82, 87)) | set(range(112, 117)) | {84, 144, 145}

# 卷定义: (part标题, level, 文件号范围)
VOLS = [
    ("第一卷 与神对话1", 0, list(range(5, 24))),      # 导读5 献词6-7 前言8 Ch9-22 致谢23
    ("第二卷 与神对话2", 0, list(range(29, 52))),     # 献词29 前言30 Ch31-50 致谢51
    ("第三卷 与神对话3", 0, list(range(57, 82))),     # 献词57 前言58 Ch59-79 后记80 致谢81
    ("第四卷 与神为友", 0, list(range(87, 112))),     # 献词87 前言88 Ch89-109 后记110 致谢111
    ("第五卷 与神合一", 0, list(range(117, 144))),    # 前言117 序章118 [P1]119 幻觉120-129 [P2]130 131-136 [P3]137 138-142 译者附记143
]
# 与神合一内嵌 part: (标题, 文件号)
INNER_PARTS = [("第一部分 人类的十大幻觉", 119), ("第二部分 掌握幻觉", 130), ("第三部分 与内在造物主相遇", 137)]

def title_for(n):
    if n in DEDIC:
        return DEDIC[n]
    hs, ps = parsed[f"OEBPS/text{n:05d}.html"]
    h = hs[0] if hs else None
    if h is None:
        return None if not ps else None   # 无 h 且非献词 → 跳过(装饰页)
    if RE_CHAPTER.match(h):
        return f"第{CN[int(RE_CHAPTER.match(h).group(1))]}章"
    if h in PART_PAGES:
        return None                       # 部分标题页 → 由 INNER_PARTS 处理
    return h

# ---------- 4. 组装 ----------
toc = []
chapters = []   # (index, title, paras)
idx = 0
tot = 0

# 总目录 (text00000)
hs0, ps0 = parsed["OEBPS/text00000.html"]
toc.append({"type": "chapter", "title": "总目录", "index": idx, "level": 1})
chapters.append((idx, "总目录", ps0))
print(f"[{idx}] 总目录 段={len(ps0)} 字={sum(len(t) for t in ps0)}")
idx += 1

for vol_title, level, nums in VOLS:
    toc.append({"type": "part", "title": vol_title, "level": level})
    in_vol = False
    for n in nums:
        if n in SKIP_NUM:
            continue
        # 内嵌部分页检查
        if n in [p for _, p in INNER_PARTS]:
            inner_title = next(t for t, p in INNER_PARTS if p == n)
            toc.append({"type": "part", "title": inner_title, "level": 1})
            continue
        t = title_for(n)
        if t is None:
            continue
        _, ps = parsed[f"OEBPS/text{n:05d}.html"]
        toc.append({"type": "chapter", "title": t, "index": idx, "level": 1})
        chapters.append((idx, t, ps))
        w = sum(len(x) for x in ps)
        tot += w
        print(f"[{idx}] {t} 段={len(ps)} 字={w}")
        idx += 1
        in_vol = True

print(f"总章数 = {idx}, 正文总字数 = {tot}")

# ---------- 5. 零丢失验证 ----------
# 5a. 新库段 == 黄金流(非跳过文件所有 p 段)
gold = []
for fn in order:
    n = fnum(fn)
    if n in SKIP_NUM or n in [p for _, p in INNER_PARTS]:
        continue
    gold += parsed[fn][1]
new_paras = [p for _, _, ps in chapters for p in ps]
print(f"\n验证5a: 新库段={len(new_paras)} vs 黄金流段={len(gold)}")
print("✓ 段落流逐段一致" if new_paras == gold else "✗ 段落流不一致!")
# 5b. 旧库全覆盖
old_paras = []
for i in range(111):
    fp = os.path.join(D, f"{i}.json")
    if os.path.exists(fp):
        j = json.load(open(fp, encoding="utf-8"))
        old_paras += [norm_body(b["value"]) for b in j["content"] if b.get("type") == "text"]
old_paras = [t for t in old_paras if t]
oldw = sum(len(t) for t in old_paras)
extra = []
i = j = 0
while i < len(old_paras) and j < len(gold):
    if old_paras[i] == gold[j]:
        i += 1; j += 1
    else:
        extra.append(old_paras[i]); i += 1
extra += old_paras[i:]
print(f"\n验证5b: 旧库段={len(old_paras)} 字={oldw} vs 新库字={tot}")
print(f"旧库未命中黄金流: {len(extra)} 段 (应全为标题行/目录行/CIP/书名页元数据)")
for k, t in enumerate(extra):
    print(f"   extra[{k}] {t[:50]!r}")
# 5c. 黄金流在旧库中未覆盖的段(旧库缺段 = 丢失风险)
miss = []
i = j = 0
while i < len(old_paras) and j < len(gold):
    if old_paras[i] == gold[j]:
        i += 1; j += 1
    else:
        miss.append(gold[j]); j += 1
miss += gold[j:]
print(f"验证5c: 黄金流未被旧库覆盖段: {len(miss)} (0 = 旧库已含全部正文)")
for k, t in enumerate(miss[:20]):
    print(f"   miss[{k}] {t[:50]!r}")

# ---------- 6. 备份 + 写入 ----------
if os.path.exists(BAK):
    shutil.rmtree(BAK)
shutil.copytree(D, BAK)
print(f"\n备份 → {BAK}")

for i, t, ps in chapters:
    content = [{"type": "text", "value": p} for p in ps]
    json.dump({"title": t, "content": content, "index": i},
              open(os.path.join(D, f"{i}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
# 删除多余旧文件
for fn in os.listdir(D):
    if re.match(r"^\d+\.json$", fn) and int(fn[:-5]) >= idx:
        os.remove(os.path.join(D, fn))

m = json.load(open(os.path.join(D, "meta.json"), encoding="utf-8"))
m["toc"] = toc
m["chapterCount"] = idx
m["chapterTitles"] = [t for _, t, _ in chapters]
json.dump(m, open(os.path.join(D, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"meta chapterCount={idx}, toc: part={sum(1 for t in toc if t['type']=='part')} "
      f"chapter={sum(1 for t in toc if t['type']=='chapter')}")

# ---------- 7. 三端同步 ----------
ra.sync_three(BID)
print("sync_three 完成")
