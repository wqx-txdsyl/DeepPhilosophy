# -*- coding: utf-8 -*-
"""瓦尔登湖/内在体验/悉达多: 源段落中未入库的是哪些文件(h1 定位)"""
import sys, os, re, json, zipfile
from html.parser import HTMLParser
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CH = r"f:\program\Python\PhiAgent\backend\data\book_chapters"

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

def norm(t):
    return re.sub(r"\s+", "", t)

def lib_norm_set(bid):
    out = set()
    meta = json.load(open(os.path.join(CH, bid, "meta.json"), encoding="utf-8"))
    for i in range(meta.get("chapterCount", 0)):
        p = os.path.join(CH, bid, f"{i}.json")
        if not os.path.exists(p): continue
        j = json.load(open(p, encoding="utf-8"))
        for b in j.get("content", []):
            if b.get("type") == "text":
                out.add(norm(b["value"]))
    return out

def epub_blocks(path):
    z = zipfile.ZipFile(path)
    out = []
    for n in sorted(z.namelist()):
        if not n.lower().endswith((".xhtml", ".html")) or "toc" in n.lower():
            continue
        c = z.read(n).decode("utf-8", errors="replace")
        p = PExtract(); p.feed(c)
        hs = [re.sub(r"\s+", " ", t).strip() for tag, t in p.blocks if tag == "h"]
        ps = [re.sub(r"\s+", " ", t).strip() for tag, t in p.blocks if tag == "p" and re.sub(r"\s+", "", t)]
        out.append((n, hs, ps))
    return out

for name, bid, src in [
    ("瓦尔登湖", "5135fe68ee4a", r"F:/philosophy/西方/亨利·戴维·梭罗/瓦尔登湖.epub"),
    ("内在体验", "8383f4e551c4", None),
    ("悉达多", "436b1e7f9477", None),
]:
    if src is None:
        import glob
        hits = glob.glob(rf"F:/philosophy/**/*.epub", recursive=True)
        cand = [p for p in hits if name.split()[0] in os.path.basename(p)]
        src = cand[0] if cand else None
        print(f"{name}: 用源 {src}")
    ln = lib_norm_set(bid)
    print(f"\n== {name} 未入库的源文件 ==")
    for n, hs, ps in epub_blocks(src):
        miss = [p for p in ps if norm(p) not in ln]
        if miss:
            print(f"  {n.split('/')[-1]}: h={hs[:2]} 段{len(ps)} 未入库{len(miss)} (前3: {[m[:30] for m in miss[:3]]})")
