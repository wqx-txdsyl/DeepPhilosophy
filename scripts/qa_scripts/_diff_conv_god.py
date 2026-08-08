# -*- coding: utf-8 -*-
"""与神对话: 旧库 vs 黄金流 字符级差异分析(去空白)
两阶段: 块级(256字符)定位差异区 → 差异区内逐字符 difflib 明细
"""
import sys, re, json, zipfile, os, difflib
from html.parser import HTMLParser
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, r"f:\program\Python\PhiAgent\backend\tools")
import rebuild_auto as ra

BID = "7657ef4a2cd3"
EP = r"F:/philosophy/西方/尼尔·唐纳德·沃尔什/与神对话(全5卷）.epub"
D = r"f:\program\Python\PhiAgent\backend\data\_rebuild_bak\7657ef4a2cd3_old111ch"

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

# ---- 黄金流字符(去空白) ----
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
gold_chars = []
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
            gold_chars.append(t)
gold = "".join(gold_chars)
gold_dw = re.sub(r"\s+", "", gold)
print(f"黄金流: {len(gold_chars)} 段 {len(gold_dw)} 字(去空白)")

# ---- 旧库字符 ----
old_chars = []
for i in range(111):
    fp = os.path.join(D, f"{i}.json")
    if os.path.exists(fp):
        j = json.load(open(fp, encoding="utf-8"))
        for b in j["content"]:
            if b.get("type") == "text":
                t = norm_body(b["value"])
                if t:
                    old_chars.append(t)
old = "".join(old_chars)
old_dw = re.sub(r"\s+", "", old)
print(f"旧库: {len(old_chars)} 段 {len(old_dw)} 字(去空白)")

# ---- 两阶段比对 ----
BLK = 256
def to_blocks(s):
    return [s[i:i + BLK] for i in range(0, len(s), BLK)]

ob, gb = to_blocks(old_dw), to_blocks(gold_dw)
sm = difflib.SequenceMatcher(a=ob, b=gb, autojunk=False)
ops = [op for op in sm.get_opcodes() if op[0] != "equal"]
same_n = sum(i2 - i1 for op in sm.get_opcodes() for (op0, i1, i2, j1, j2) in [op] if op0 == "equal")
print(f"\n块级比对: 旧库块={len(ob)} 黄金块={len(gb)} 相同块字符={same_n*BLK} 差异操作={len(ops)}")

for k, (op, i1, i2, j1, j2) in enumerate(ops[:24]):
    o_txt = "".join(ob[i1:i2])
    g_txt = "".join(gb[j1:j2])
    print(f"--- [{k}] {op} 旧库[{i1*BLK}:{i2*BLK}] 黄金[{j1*BLK}:{j2*BLK}]")
    print(f"  旧库段: {o_txt[:120]!r}")
    print(f"  黄金段: {g_txt[:120]!r}")
if len(ops) > 24:
    print(f"... 共 {len(ops)} 个差异操作, 其余略")

# ---- 差异字符统计 ----
od, gd = 0, 0
for op, i1, i2, j1, j2 in ops:
    if op in ("delete", "replace"):
        od += (i2 - i1) * BLK
    if op in ("insert", "replace"):
        gd += (j2 - j1) * BLK
print(f"\n差异量: 旧库独有 ≈{od} 字, 黄金独有 ≈{gd} 字")
print(f"旧库去空白总 {len(old_dw)} - 差异 {od} = 与黄金共同 {len(old_dw) - od} 字")
