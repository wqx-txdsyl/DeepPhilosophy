# -*- coding: utf-8 -*-
"""列全部差异操作, 分类旧库独有正文段(排除目录/标题/CIP/书名页垃圾)"""
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
gpos = []
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
            w = len(re.sub(r"\s+", "", t))
            gold.append((fn, w, t))
gold_dw = "".join(re.sub(r"\s+", "", t) for _, _, t in gold)
# 文件边界表
fmap = []
pos = 0
for fn, w, _ in gold:
    fmap.append((fn.split("/")[-1], pos, w))
    pos += w

old = []
for i in range(111):
    fp = os.path.join(D, f"{i}.json")
    if os.path.exists(fp):
        j = json.load(open(fp, encoding="utf-8"))
        for b in j["content"]:
            if b.get("type") == "text":
                t = norm_body(b["value"])
                if t:
                    old.append((i, t))
old_dw = "".join(re.sub(r"\s+", "", t) for _, t in old)
# 旧库章边界表
omap = []
pos = 0
for ci, t in old:
    w = len(re.sub(r"\s+", "", t))
    omap.append((ci, pos, w))
    pos += w

sm = difflib.SequenceMatcher(a=old_dw, b=gold_dw)
ops = [op for op in sm.get_opcodes() if op[0] != "equal"]

def file_at(fmap, p):
    for fn, s, w in fmap:
        if s <= p < s + w:
            return fn
    return "?"

def ch_at(omap, p):
    for ci, s, w in omap:
        if s <= p < s + w:
            return ci
    return "?"

JUNK_RE = re.compile(r"^(总目录|目录|Chapter ?\d+|导读|前言|致谢|后记|献词|序章|译者附记|图书在版编目|与神对话|与神为友|与神合一|\[美\]|李继宏|江西人民出版社|ISBN|Ⅰ\.|中国版本图书馆|著作权合同|版权|页|第[一二三四五六七八九十]+部分|第一部分|第二部分|第三部分)")

print("=== 旧库独有段分类 ===")
garbage_n = garbage_w = 0
body = []
for op, i1, i2, j1, j2 in ops:
    o_txt = old_dw[i1:i2]
    if op in ("delete", "replace") and o_txt:
        if JUNK_RE.match(o_txt) and len(o_txt) < 40:
            garbage_n += 1
            garbage_w += len(o_txt)
        else:
            body.append((i1, i2, o_txt, ch_at(omap, i1), file_at(fmap, j1)))
print(f"垃圾(标题/目录/CIP行): {garbage_n} 条 {garbage_w} 字")
print(f"疑似正文: {len(body)} 条 {sum(len(t) for _,_,t,_,_ in body)} 字")
for i1, i2, t, ci, fn in body:
    print(f"\n--- 旧库章[{ci}] 黄金文件[{fn}] {len(t)}字:")
    print(f"   {t[:180]}")
