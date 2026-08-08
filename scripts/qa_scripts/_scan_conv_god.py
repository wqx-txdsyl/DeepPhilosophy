# -*- coding: utf-8 -*-
"""与神对话(全5卷) 西方版源 epub: spine 序 + 每文件 h1/真实标题行分析"""
import sys, re, zipfile, os
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

def structure(path, start=0, limit=200, show_titles=False):
    z = zipfile.ZipFile(path)
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
    for i, n in enumerate(order):
        if n not in z.namelist(): continue
        c = z.read(n).decode("utf-8", errors="replace")
        p = PExtract(); p.feed(c)
        hs = [re.sub(r"\s+", " ", t).strip() for tag, t in p.blocks if tag == "h"]
        ps = [re.sub(r"\s+", " ", t).strip() for tag, t in p.blocks if tag == "p" and re.sub(r"\s+", "", t)]
        title_lines = []
        if show_titles:
            for t in ps[:4] + ps[-2:]:
                ts = re.sub(r"\s+", "", t)
                if len(ts) <= 30 and re.match(r"^(第[一二三四五六卷]|卷[一二三四五]|Chapter|附|序|前言|后记|跋|导)", ts):
                    title_lines.append(t[:40])
        out.append((n, hs[:2], len(ps), sum(len(x) for x in ps), title_lines))
    return out

path = r"F:/philosophy/西方/尼尔·唐纳德·沃尔什/与神对话(全5卷）.epub"
print(f"=== {path} ===")
st = structure(path, show_titles=True)
print(f"共 {len(st)} 文件")
for i, (n, hs, np_, w, tl) in enumerate(st):
    hstr = ",".join(hs)[:50] if hs else "-"
    tstr = " | ".join(tl[:3])[:80] if tl else ""
    print(f"[{i}] {n.split('/')[-1]}: h={hstr} p={np_} 字={w} {tstr}")
