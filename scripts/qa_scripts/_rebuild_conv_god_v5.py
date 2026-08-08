# -*- coding: utf-8 -*-
"""《与神对话(全5卷)》重建 v5 — 位置感知的重复判定
v4 教训: `dw(t) in gold_dw` 整串子串检查对短段系统性误杀("公平"/"宽容"等
列表项、问题清单句——66万字黄金流里短串几乎必然出现), 且段首带标点变体
(".我来看看能否总结出…")漏检。
v5: 重复 = 段在黄金流中**紧邻插入点 j1 附近**(±400 字符)出现 → 边界歧义,
丢弃; 出现在别处或全无 → 真独有, 保留。
v4 实测: 黄金独有 0 ✓(无丢失), 815字重复(11问题段+列表项), 真独有 2705字。
"""
import sys, re, json, zipfile, os, difflib
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

# ---------- 2. 黄金流段列表 ----------
SKIP_NUM = set(range(1, 5)) | set(range(24, 29)) | set(range(52, 57)) | \
           set(range(82, 87)) | set(range(112, 117)) | {84, 144, 145}
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
JUNK_CH = {1, 2, 3, 23, 24, 25, 49, 50, 51, 77, 78, 104}   # 目录残留/书名页/CIP/版权页 整章垃圾
old = []   # (章号, text)
for i in range(111):
    if i in JUNK_CH:
        continue
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
print(f"旧库(剔除12垃圾章): {len(old)} 段 {len(old_dw)} 字")

sm = difflib.SequenceMatcher(a=old_dw, b=gold_dw)
ops = [op for op in sm.get_opcodes() if op[0] != "equal"]

# ---------- 4. 垃圾判定 ----------
JUNK_RE = re.compile(r"^(总目录|目录|Chapter ?\d+|导读|前言|致谢|后记|献词|序章|译者附记|图书在版编目|与神对话\d*$|与神为友$|与神合一$|\[美\]|李继宏|江西人民出版社|ISBN|Ⅰ\.|中国版本图书馆|著作权合同|版权|页$|第[一二三四五六七八九十]+部分|部分.{0,12}幻觉)")
CIP_KW = ("图书在版编目", "ISBN", "中国版本图书馆", "著作权合同登记", "Ⅰ.", "Ⅱ.", "Ⅲ.", "Ⅳ.",
          "责任编辑", "出版发行", "印刷", "版次", "印数", "定价", "开本", "字数", "赣版权登字",
          "All rights", "Copyright", "This edition", "Andrew Nurnberg", "Putnam", "Penguin",
          "版贸", "图书在版")
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
    if re.match(r"^与神(对话\. \d|为友 /|合一 /)", d) and "/" in t:
        return True
    return False

# ---------- 5. 收集插入段(v5: 位置感知重复判定) ----------
NEAR = 400   # 段在黄金流中出现位置距插入点 j1 的容差(字符)
def find_near(d, j1):
    """段 d 在黄金流中出现且位置与 j1 接近(边界歧义) → True; 全无/远距 → False"""
    pos = -1
    while True:
        pos = gold_dw.find(d, pos + 1)
        if pos < 0:
            return False
        if abs(pos - j1) <= NEAR:
            return True
    # 所有出现位置都距 j1 远 → 真独有(短段远距出现是常态, 如列表项) → False
    return False

inserts = {}   # j1 → [texts]
junk_list = []
dup_list = []
n_body = 0
for op, i1, i2, j1, j2 in ops:
    if op not in ("delete", "replace"):
        continue
    if not old_dw[i1:i2]:
        continue
    segs = []
    for k in range(len(old)):
        if o_acc[k + 1] > i1 and o_acc[k] < i2:
            segs.append(old[k][1])
    if not segs:
        continue
    for t in segs:
        td = dw(t)
        if is_junk(t):
            junk_list.append(t)
            print(f"  丢弃 {len(td)}字: {t[:46]!r}")
        elif find_near(td, j1):
            dup_list.append(t)      # 黄金流在插入点附近已有该段 → 边界歧义 → 丢弃
        else:
            inserts.setdefault(j1, []).append(t)
            n_body += 1
            print(f"  插入 @{j1} +{len(td)}字: {t[:40]!r}")
print(f"剔除垃圾: {len(junk_list)} 段, {sum(len(dw(t)) for t in junk_list)} 字")
print(f"丢弃重复(黄金流已有): {len(dup_list)} 段, {sum(len(dw(t)) for t in dup_list)} 字")
for t in dup_list:
    print(f"  重复丢弃 {len(dw(t))}字: {t[:40]!r}")
ins_w = sum(len(dw(t)) for v in inserts.values() for t in v)
print(f"\n补插正文: {n_body} 段, {ins_w} 字, 插入点 {len(inserts)} 个")
for j1, ts in sorted(inserts.items()):
    for t in ts:
        print(f"  @{j1} +{len(dw(t))}字: {t[:30]!r}")

# ---------- 6. 重建段序列 ----------
def split_at(text, off):
    n = 0
    for i, ch in enumerate(text):
        if not ch.isspace():
            if n == off:
                return text[:i], text[i:]
            n += 1
    return text, ""

rebuilt = []
expected_dw = []
ins_keys = sorted(inserts)
ins_i = 0
for k, (fn, t) in enumerate(gold):
    a, b = g_acc[k], g_acc[k + 1]
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
while ins_i < len(ins_keys):
    for txt in inserts[ins_keys[ins_i]]:
        rebuilt.append((gold[-1][0], txt))
        expected_dw.append(dw(txt))
    ins_i += 1

new_dw = "".join(expected_dw)
print(f"\n重建段: {len(rebuilt)} 段 {len(new_dw)} 字 (黄金 {len(gold_dw)} + 插入 {len(new_dw) - len(gold_dw)})")

# 零丢失: 旧库 vs 新库
sm2 = difflib.SequenceMatcher(a=old_dw, b=new_dw)
ops2 = [op for op in sm2.get_opcodes() if op[0] != "equal"]
od2 = gd2 = 0
for op, i1, i2, j1, j2 in ops2:
    if op in ("delete", "replace"):
        od2 += i2 - i1
    if op in ("insert", "replace"):
        gd2 += j2 - j1
print(f"零丢失: 旧库独有(垃圾) ≈ {od2} 字; 新库独有 ≈ {gd2} 字")
print("✓ 新库独有 = 0, 旧库正文全部保留" if gd2 == 0 else "!! 仍有新库独有!")
for op, i1, i2, j1, j2 in ops2:
    if op in ("insert", "replace") and j2 - j1 > 0:
        print(f"   新库独有: {new_dw[j1:j2][:50]!r}")

# ---------- 7. 章切分 ----------
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
INNER_NUM = {p for _, p in INNER_PARTS}

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
idx += 1
for vol_title, level, nums in VOLS:
    toc.append({"type": "part", "title": vol_title, "level": level})
    for n in nums:
        if n in INNER_NUM:
            toc.append({"type": "part", "title": next(t for t, p in INNER_PARTS if p == n), "level": 1})
            continue
        if n in SKIP_NUM:
            continue
        t = title_for(n)
        if t is None:
            continue
        ps = by_file.get(n, [])
        toc.append({"type": "chapter", "title": t, "index": idx, "level": 1})
        chapters.append((idx, t, ps))
        w = sum(len(x) for x in ps)
        tot += w
        idx += 1
print(f"总章数 = {idx}, 正文总字数 = {tot}")

# ---------- 8. 验证段落流 ----------
new_paras = [p for _, _, ps in chapters for p in ps]
ok = new_paras == [t for _, t in rebuilt]
print(f"\n验证: 新库段={len(new_paras)} vs rebuilt={len(rebuilt)}")
print("✓ 段落流一致" if ok else "✗ 不一致!")

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
