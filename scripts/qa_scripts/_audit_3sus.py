# -*- coding: utf-8 -*-
"""3 本可疑书深入分析: 库章节 vs epub 结构"""
import sys, os, re, json, zipfile
from html.parser import HTMLParser
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CH = r"f:\program\Python\PhiAgent\backend\data\book_chapters"
DD = r"f:\program\Python\PhiAgent\backend\data\book_detail"

def lib_info(bid):
    meta = json.load(open(os.path.join(CH, bid, "meta.json"), encoding="utf-8"))
    n = meta.get("chapterCount", 0)
    chs = []
    for i in range(n):
        p = os.path.join(CH, bid, f"{i}.json")
        if not os.path.exists(p): continue
        j = json.load(open(p, encoding="utf-8"))
        texts = [b["value"] for b in j.get("content", []) if b.get("type") == "text"]
        chs.append((j.get("title", "?"), sum(len(x) for x in texts)))
    return meta.get("title", bid), n, chs

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

def epub_structure(path):
    z = zipfile.ZipFile(path)
    out = []
    for n in sorted(z.namelist()):
        if not n.lower().endswith((".xhtml", ".html")) or "toc" in n.lower():
            continue
        c = z.read(n).decode("utf-8", errors="replace")
        p = PExtract(); p.feed(c)
        hs = [re.sub(r"\s+", " ", t).strip() for tag, t in p.blocks if tag == "h"]
        nps = len([1 for tag, t in p.blocks if tag == "p" and re.sub(r"\s+", "", t)])
        total = sum(len(re.sub(r"\s+", "", t)) for tag, t in p.blocks)
        out.append((n, hs, nps, total))
    return out

sus = [
    ("和狗狗的十二次哲学漫步", "230068c4c6b6"),
    ("尼采经典著作及研究丛书（四册全）", "4cc9d23c7dbf"),
    ("心理学和炼金术", "e63a26081cb9"),
]
import glob
for t, bid in sus:
    print(f"\n{'='*70}\n【{t}】 bid={bid}")
    title, n, chs = lib_info(bid)
    print(f"库章节数={n}:")
    for i, (ct, cc) in enumerate(chs):
        print(f"  [{i}] {ct}: {cc:,}")
    # 找源 epub
    hits = glob.glob(rf"F:/philosophy/**/*.epub", recursive=True)
    for p in hits:
        try:
            z = zipfile.ZipFile(p)
            opf = [x for x in z.namelist() if x.lower().endswith(".opf")]
            c = z.read(opf[0]).decode("utf-8", errors="replace")
            m = re.search(r"<dc:title[^>]*>(.*?)</dc:title>", c, re.S)
            pt = re.sub(r"<[^>]+>", "", m.group(1)) if m else ""
        except Exception:
            continue
        if t in pt or pt in t or (t[:5] in pt):
            print(f"\n源: {p}\n  dc:title={pt}")
            for n_, hs, nps, total in epub_structure(p)[:40]:
                print(f"  {n_} h={hs} p={nps} 字={total}")
            break
