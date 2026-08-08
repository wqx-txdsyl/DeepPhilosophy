# -*- coding: utf-8 -*-
"""存在与时间 / 与神对话 源 epub 结构 (spine 序 + h1)"""
import sys, os, re, glob, zipfile
from html.parser import HTMLParser
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

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

def structure(path, limit=80):
    z = zipfile.ZipFile(path)
    # spine 序
    opf = [n for n in z.namelist() if n.lower().endswith(".opf")][0]
    c = z.read(opf).decode("utf-8", errors="replace")
    items = {}
    for m in re.finditer(r'<item\b([^>]*)/?>', c):
        attrs = dict(re.findall(r'(\w+)\s*=\s*"([^"]*)"', m.group(1)))
        if attrs.get("href"):
            items[attrs.get("id", "")] = (attrs["href"], os.path.dirname(opf))
    spine = re.findall(r'<itemref\b[^>]*?idref="([^"]+)"', c)
    order = []
    for s in spine:
        if s in items:
            href, base = items[s]
            p = os.path.join(base, href) if not href.startswith(base) else href
            p = p.replace("\\", "/")
            if p not in z.namelist():
                cand = [n for n in z.namelist() if n.endswith("/" + href)]
                p = cand[0] if cand else p
            order.append(p)
    if not order:
        order = sorted(n for n in z.namelist() if n.lower().endswith((".xhtml", ".html")) and "toc" not in n.lower())
    out = []
    for n in order:
        if n not in z.namelist(): continue
        c = z.read(n).decode("utf-8", errors="replace")
        p = PExtract(); p.feed(c)
        hs = [re.sub(r"\s+", " ", t).strip() for tag, t in p.blocks if tag == "h"]
        ps = [re.sub(r"\s+", " ", t).strip() for tag, t in p.blocks if tag == "p" and re.sub(r"\s+", "", t)]
        out.append((n, hs, len(ps), sum(len(x) for x in ps)))
    return out

print("========== 存在与时间 源 ==========")
hits = glob.glob(r"F:/philosophy/**/存在与时间*.epub", recursive=True)
print("候选:", hits)
for p in hits:
    if "释义" in p: continue
    st = structure(p)
    print(f"\n{p}:")
    for n, hs, np_, w in st[:60]:
        print(f"  {n.split('/')[-1]}: h={hs[:3]} p={np_} 字={w}")

print("\n========== 与神对话 源 (卷1 前 20 文件) ==========")
hits = glob.glob(r"F:/philosophy/**/*与神对话*.epub", recursive=True)
print("候选:", hits)
for p in hits:
    st = structure(p)
    print(f"\n{p} 共{len(st)}文件:")
    for n, hs, np_, w in st[:20]:
        print(f"  {n.split('/')[-1]}: h={hs[:3]} p={np_} 字={w}")
    break
