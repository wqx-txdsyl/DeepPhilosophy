# -*- coding: utf-8 -*-
"""定位旧库缺失的 ~10400 字在黄金流中的位置"""
import sys, re, json, zipfile, os
from html.parser import HTMLParser
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, r"f:\program\Python\PhiAgent\backend\tools")
import rebuild_auto as ra

BID = "7657ef4a2cd3"
EP = r"F:/philosophy/西方/尼尔·唐纳德·沃尔什/与神对话(全5卷）.epub"
D = os.path.join(ra.CH, BID)

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
print("spine 序(尾部 12 文件):")
for fn in order[-12:]:
    print("  ", fn.split("/")[-1])

# 黄金流 + 文件边界索引
fidx = []   # (fn, 起始字符位置, 字数)
gold = []
pos = 0
for fn in order:
    m = re.search(r"text(\d{5})\.html$", fn)
    n = int(m.group(1)) if m else -1
    c2 = z.read(fn).decode("utf-8", errors="replace")
    p = PExtract(); p.feed(c2)
    w = 0
    for t in p.blocks:
        t = norm_body(t)
        if t:
            gold.append(t)
            w += len(re.sub(r"\s+", "", t))
    fidx.append((fn.split("/")[-1], pos, w))
    pos += w
gold_dw = "".join(re.sub(r"\s+", "", t) for t in gold)
print(f"\n黄金流总 {len(gold_dw)} 字")
print("\n尾部文件边界:")
for fn, s, w in fidx:
    if s + w > 645000:
        print(f"  {fn}: [{s}:{s+w}] {w} 字")

# 旧库结尾段
old_last = []
for i in range(110, -1, -1):
    fp = os.path.join(D, f"{i}.json")
    j = json.load(open(fp, encoding="utf-8"))
    ts = [norm_body(b["value"]) for b in j["content"] if b.get("type") == "text" and norm_body(b["value"])]
    old_last = ts + old_last
    if sum(len(re.sub(r"\s+", "", t)) for t in old_last) > 1200:
        break
old_tail = "".join(re.sub(r"\s+", "", t) for t in old_last)
print(f"\n旧库尾部 1200 字: ...{old_tail[-600:]}")

# 找旧库尾部段在黄金中的位置
probe = re.sub(r"\s+", "", old_tail[-60:])
i = gold_dw.find(probe)
print(f"\n探针 {probe[:40]!r}... 在黄金流位置 {i} (共 {len(gold_dw)})")
if i >= 0:
    print(f"黄金流从 {i} 起 200 字: {gold_dw[i:i+200]}")
    print(f"黄金流剩余 {len(gold_dw)-i} 字")
    # 归属文件
    for fn, s, w in fidx:
        if s <= i < s + w:
            print(f"→ 属于 {fn} [{s}:{s+w}]")
