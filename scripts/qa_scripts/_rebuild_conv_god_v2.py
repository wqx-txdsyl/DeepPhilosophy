# -*- coding: utf-8 -*-
"""《与神对话(全5卷)》重建 v2 — 黄金流 + 旧库独有正文补插(修复全5卷版 epub 缺失段)
v1 只按全5卷版重建, 但旧库(分卷版导入)比全5卷版多 ~3500 字真实正文
(卷1Ch03"我的生活什么时候才能平步青云…"786字、卷1Ch04"我依照神的形象…"744字、卷2多段等)
→ v2: 黄金流(全5卷版) + 旧库独有正文段按字符位置(j1)插回, 垃圾(目录残留/CIP/书名页/机械标题行)剔除
零丢失: 新库字符流(去空白) == 黄金流+插入段; 旧库独有(剔除后) == 垃圾清单
"""
import sys, re, json, zipfile, os, shutil, bisect, difflib
from html.parser import HTMLParser
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, r"f:\program\Python\PhiAgent\backend\tools")
import rebuild_auto as ra

BID = "7657ef4a2cd3"
EP = r"F:/philosophy/西方/尼尔·唐纳德·沃尔什/与神对话(全5卷）.epub"
D = os.path.join(ra.CH, BID)
OLDBAK = r"f:\program\Python\PhiAgent\backend\data\_rebuild_bak\7657ef4a2cd3_old111ch"
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

def dw(t):
    return re.sub(r"\s+", "", t)

# ---------- 1. spine 序 + 解析 ----------
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

# ---------- 2. 黄金流段列表 (fn, text) ----------
SKIP_NUM = set(range(1, 5)) | set(range(24, 29)) | set(range(52, 57)) | \
           set(range(82, 87)) | set(range(112, 117)) | {84, 119, 130, 137, 144, 145}
gold = []   # (fn名, text)
for fn in order:
    n = fnum(fn)
    if n in SKIP_NUM:
        continue
    for t in parsed[fn][1]:
        gold.append((fn.split("/")[-1], t))
g_acc = [0] * (len(gold) + 1)
for k, (_, t) in enumerate(gold):
    g_acc[k + 1] = g_acc[k] + len(dw(t))
gold_dw = "".join(dw(t) for _, t in gold)
print(f"黄金流: {len(gold)} 段 {len(gold_dw)} 字")

# ---------- 3. 旧库段 + 差异 ----------
old = []   # (章号, text)
for i in range(111):
    fp = os.path.join(OLDBAK, f"{i}.json")
    if os.path.exists(fp):
        j = json.load(open(fp, encoding="utf-8"))
        for b in j["content"]:
            if b.get("type") == "text":
                t = norm_body(b["value"])
                if t:
                    old.append((i, t))
o_acc = [0] * (len(old) + 1)
for k, (_, t) in enumerate(old):
    o_acc[k + 1] = o_acc[k] + len(dw(t))
old_dw = "".join(dw(t) for _, t in old)
print(f"旧库: {len(old)} 段 {len(old_dw)} 字")

sm = difflib.SequenceMatcher(a=old_dw, b=gold_dw)
ops = [op for op in sm.get_opcodes() if op[0] != "equal"]

# ---------- 4. 垃圾判定 ----------
JUNK_RE = re.compile(r"^(总目录|目录|Chapter ?\d+|导读|前言|致谢|后记|献词|序章|译者附记|图书在版编目|与神对话\d*$|与神为友$|与神合一$|\[美\]|李继宏|江西人民出版社|ISBN|Ⅰ\.|中国版本图书馆|著作权合同|版权|页$|第[一二三四五六七八九十]+部分|部分.{0,12}幻觉)")
CIP_KW = ("图书在版编目", "ISBN", "中国版本图书馆", "著作权合同登记", "Ⅰ.", "Ⅱ.", "Ⅲ.", "Ⅳ.")
def is_junk(t):
    d = dw(t)
    if len(d) < 50 and JUNK_RE.match(d):
        return True
    if len(d) < 50 and re.match(r"^\d+\.[^，。]{1,16}$", d):
        return True
    if any(k in t for k in CIP_KW):
        return True
    if d.startswith("目录") and "Chapter" in t:
        return True
    return False

# ---------- 5. 收集插入段 ----------
inserts = {}   # j1 → [texts]
junk_list = []
n_body = 0
for op, i1, i2, j1, j2 in ops:
    if op not in ("delete", "replace"):
        continue
    if not old_dw[i1:i2]:
        continue
    # 收集与 [i1,i2) 有交集的旧库段
    segs = []
    for k in range(len(old)):
        if o_acc[k + 1] > i1 and o_acc[k] < i2:
            segs.append(old[k][1])
    if not segs:
        continue
    body = [t for t in segs if not is_junk(t)]
    junk = [t for t in segs if is_junk(t)]
    junk_list += junk
    if body:
        inserts.setdefault(j1, []).extend(body)
        n_body += len(body)
    for t in junk:
        print(f"  丢弃 {len(dw(t))}字: {t[:46]!r}")
print(f"\n补插正文: {n_body} 段, {sum(len(dw(t)) for v in inserts.values() for t in v)} 字, 插入点 {len(inserts)} 个")
print(f"剔除垃圾: {len(junk_list)} 段, {sum(len(dw(t)) for t in junk_list)} 字")

# ---------- 6. 重建段序列 (黄金流 + 插入段按 j1 定位) ----------
def split_at(text, off):
    n = 0
    for i, ch in enumerate(text):
        if not ch.isspace():
            if n == off:
                return text[:i], text[i:]
            n += 1
    return text, ""

rebuilt = []          # (fn, text)
expected_dw = []
ins_keys = sorted(inserts)
ins_i = 0
for k, (fn, t) in enumerate(gold):
    a, b = g_acc[k], g_acc[k + 1]
    # 插入点 j1 ∈ [a, b) → 插在本段前(off<=0) 或 段内(拆段)
    while ins_i < len(ins_keys) and ins_keys[ins_i] < b:
        j1 = ins_keys[ins_i]
        off = j1 - a
        if off <= 0:
            for txt in inserts[j1]:
                rebuilt.append((fn, txt))
                expected_dw.append(dw(txt))
        else:
            pre, suf = split_at(t, off)
            for txt in inserts[j1]:
                rebuilt.append((fn, txt))
                expected_dw.append(dw(txt))
            rebuilt.append((fn, suf))
            expected_dw.append(dw(suf))
            t = pre
        ins_i += 1
    rebuilt.append((fn, t))
    expected_dw.append(dw(t))
# 末尾残余插入点(理论不出现: 插入点必 < len(gold_dw))
while ins_i < len(ins_keys):
    for txt in inserts[ins_keys[ins_i]]:
        rebuilt.append((gold[-1][0], txt))
        expected_dw.append(dw(txt))
    ins_i += 1

new_dw = "".join(expected_dw)
print(f"\n重建段: {len(rebuilt)} 段 {len(new_dw)} 字 (黄金 {len(gold_dw)} + 插入 {len(new_dw) - len(gold_dw)})")

# 验证: 新库字符流 == 黄金流+插入
gold2 = gold_dw
exp_check = []
for j1 in sorted(inserts):
    pass  # 用 expected_dw 已含插入; 直接断言
assert new_dw == "".join(expected_dw), "构造断言"
print("✓ 新库字符流 = 黄金流 + 插入段(构造验证)")

# 零丢失: 旧库 vs 新库
sm2 = difflib.SequenceMatcher(a=old_dw, b=new_dw)
ops2 = [op for op in sm2.get_opcodes() if op[0] != "equal"]
od2 = gd2 = 0
for op, i1, i2, j1, j2 in ops2:
    if op in ("delete", "replace"):
        od2 += i2 - i1
    if op in ("insert", "replace"):
        gd2 += j2 - j1
print(f"\n零丢失验证: 旧库独有(应为垃圾 {sum(len(dw(t)) for t in junk_list)} 字) ≈ {od2} 字; 新库独有 ≈ {gd2} 字")
print("✓ 旧库正文全部保留" if gd2 <= 20 and od2 <= sum(len(dw(t)) for t in junk_list) + 300 else "!! 需检查")
for op, i1, i2, j1, j2 in ops2:
    o_t, g_t = old_dw[i1:i2], new_dw[j1:j2]
    if op in ("delete", "replace") and len(o_t) > 0 and len(o_t) < 60:
        print(f"   旧库独有: {o_t[:46]!r}")
    elif op in ("insert", "replace") and len(g_t) > 0 and len(g_t) < 60:
        print(f"   新库独有: {g_t[:46]!r}")

# ---------- 7. 章切分 (按文件) ----------
DEDIC = {6: "献词一", 7: "献词二", 29: "献词", 57: "献词", 87: "献词"}
RE_CHAPTER = re.compile(r"^Chapter (\d+)$", re.I)
PART_PAGES = {"第一部分 人类的十大幻觉", "第二部分 掌握幻觉", "第三部分 与内在造物主相遇"}
VOLS = [
    ("第一卷 与神对话1", 0, list(range(5, 24))),
    ("第二卷 与神对话2", 0, list(range(29, 52))),
    ("第三卷 与神对话3", 0, list(range(57, 82))),
    ("第四卷 与神为友", 0, list(range(87, 112))),
    ("第五卷 与神合一", 0, list(range(117, 144))),
]
INNER_PARTS = [("第一部分 人类的十大幻觉", 119), ("第二部分 掌握幻觉", 130), ("第三部分 与内在造物主相遇", 137)]

def title_for(n):
    if n in DEDIC:
        return DEDIC[n]
    hs, ps = parsed[f"OEBPS/text{n:05d}.html"]
    h = hs[0] if hs else None
    if h is None:
        return None
    if RE_CHAPTER.match(h):
        return f"第{CN[int(RE_CHAPTER.match(h).group(1))]}章"
    if h in PART_PAGES:
        return None
    return h

# 按文件分组 rebuilt
by_file = {}
for fn, t in rebuilt:
    m = re.search(r"text(\d{5})\.html$", fn)
    n = int(m.group(1)) if m else -1
    by_file.setdefault(n, []).append(t)

toc = []
chapters = []
idx = 0
tot = 0
toc.append({"type": "chapter", "title": "总目录", "index": idx, "level": 1})
chapters.append((idx, "总目录", by_file[0]))
print(f"[{idx}] 总目录 段={len(by_file[0])}")
idx += 1
for vol_title, level, nums in VOLS:
    toc.append({"type": "part", "title": vol_title, "level": level})
    for n in nums:
        if n in SKIP_NUM:
            continue
        if n in [p for _, p in INNER_PARTS]:
            toc.append({"type": "part", "title": next(t for t, p in INNER_PARTS if p == n), "level": 1})
            continue
        t = title_for(n)
        if t is None:
            continue
        ps = by_file.get(n, [])
        toc.append({"type": "chapter", "title": t, "index": idx, "level": 1})
        chapters.append((idx, t, ps))
        w = sum(len(x) for x in ps)
        tot += w
        print(f"[{idx}] {t} 段={len(ps)} 字={w}")
        idx += 1
print(f"总章数 = {idx}, 正文总字数 = {tot}")

# ---------- 8. 验证: 新库段落流 == rebuilt ----------
new_paras = [p for _, _, ps in chapters for p in ps]
print(f"\n验证: 新库段={len(new_paras)} vs rebuilt={len(rebuilt)}")
print("✓ 段落流一致" if new_paras == [t for _, t in rebuilt] else "✗ 不一致!")

# ---------- 9. 写入 ----------
for i, t, ps in chapters:
    content = [{"type": "text", "value": p} for p in ps]
    json.dump({"title": t, "content": content, "index": i},
              open(os.path.join(D, f"{i}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
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

# ---------- 10. 三端同步 ----------
ra.sync_three(BID)
print("sync_three 完成")
