# -*- coding: utf-8 -*-
"""真旧库 vs 黄金流: 全字符 SequenceMatcher 零丢失验证
关键指标: 黄金独有字符(旧库缺失=丢失) 必须 ≈ 0
"""
import sys, re, json, zipfile, os, difflib
from html.parser import HTMLParser
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

D = r"f:\program\Python\PhiAgent\backend\data\_rebuild_bak\7657ef4a2cd3_old111ch"
EP = r"F:/philosophy/西方/尼尔·唐纳德·沃尔什/与神对话(全5卷）.epub"

class PExtract(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.cur = None; self.buf = []; self.blocks = []
    def handle_starttag(self, tag, attrs):
        if tag == "p": self.cur = "p"; self.buf = []
    def handle_endtag(self, tag):
        if tag == "p" and self.cur == "p":
            self.blocks.append("".join(self.buf)); self.cur = None
    def handle_data(self, d):
        if self.cur: self.buf.append(d)

def norm_body(t):
    return re.sub(r"\s+", " ", t).strip()

# ---- 黄金流 ----
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
SKIP_NUM = set(range(1, 5)) | set(range(24, 29)) | set(range(52, 57)) | \
           set(range(82, 87)) | set(range(112, 117)) | {84, 119, 130, 137, 144, 145}
gold = []
for fn in order:
    m = re.search(r"text(\d{5})\.html$", fn)
    n = int(m.group(1)) if m else -1
    if n in SKIP_NUM:
        continue
    c2 = z.read(fn).decode("utf-8", errors="replace")
    p = PExtract(); p.feed(c2)
    for t in p.blocks:
        t = norm_body(t)
        if t:
            gold.append(t)
gold_dw = "".join(re.sub(r"\s+", "", t) for t in gold)
print(f"黄金流: {len(gold)} 段 {len(gold_dw)} 字")

# ---- 旧库 ----
old = []
for i in range(111):
    fp = os.path.join(D, f"{i}.json")
    if os.path.exists(fp):
        j = json.load(open(fp, encoding="utf-8"))
        for b in j["content"]:
            if b.get("type") == "text":
                t = norm_body(b["value"])
                if t:
                    old.append(t)
old_dw = "".join(re.sub(r"\s+", "", t) for t in old)
print(f"旧库: {len(old)} 段 {len(old_dw)} 字")

# ---- 全字符比对 ----
sm = difflib.SequenceMatcher(a=old_dw, b=gold_dw)
ops = [op for op in sm.get_opcodes() if op[0] != "equal"]
print(f"\n差异操作 {len(ops)} 个")
od = gd = 0
for op, i1, i2, j1, j2 in ops:
    if op in ("delete", "replace"):
        od += i2 - i1
    if op in ("insert", "replace"):
        gd += j2 - j1
print(f"旧库独有(插入/CIP等) ≈ {od} 字")
print(f"黄金独有(旧库缺失=丢失) ≈ {gd} 字")
print("✓ 黄金内容全部保留" if gd <= 200 else f"!! 黄金独有 {gd} 字 — 旧库缺内容!")

# 输出差异明细(黄金独有部分最重要)
n_show = 0
for op, i1, i2, j1, j2 in ops:
    o_txt = old_dw[i1:i2]
    g_txt = gold_dw[j1:j2]
    tag = "黄金独有" if op in ("insert", "replace") and g_txt else ("旧库独有" if op in ("delete", "replace") and o_txt else "")
    if op == "replace":
        tag = f"替换(旧{gd and len(o_txt)} vs 黄{len(g_txt)})"
    print(f"--- {tag} 旧[{i1}:{i2}] 黄[{j1}:{j2}]")
    if o_txt:
        print(f"  旧: {o_txt[:100]!r}")
    if g_txt:
        print(f"  黄: {g_txt[:100]!r}")
    n_show += 1
    if n_show >= 30:
        print(f"... 共 {len(ops)} 个, 其余略")
        break
