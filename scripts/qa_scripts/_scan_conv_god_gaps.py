# -*- coding: utf-8 -*-
"""与神对话源 epub: 超短章(text00018/45/68)前后内容连续性判断"""
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

z = zipfile.ZipFile(r"F:/philosophy/西方/尼尔·唐纳德·沃尔什/与神对话(全5卷）.epub")

def dump(fn, maxp=6, tail=2):
    c = z.read(f"OEBPS/{fn}.html").decode("utf-8", errors="replace")
    p = PExtract(); p.feed(c)
    hs = [re.sub(r"\s+", " ", t).strip() for tag, t in p.blocks if tag == "h"]
    ps = [re.sub(r"\s+", " ", t).strip() for tag, t in p.blocks if tag == "p" and re.sub(r"\s+", "", t)]
    print(f"--- {fn} h={hs} p={len(ps)} 字={sum(len(x) for x in ps)}")
    for t in ps[:maxp]: print(f"   > {t[:70]}")
    if len(ps) > maxp:
        print("   ...")
        for t in ps[-tail:]: print(f"   < {t[:70]}")
    return ps

print("== 卷1 Chapter 9/10/11 ==")
dump("text00017")
dump("text00018", maxp=3, tail=1)
dump("text00019", maxp=3, tail=1)
print("\n== 卷2 Chapter 14/15/16 ==")
dump("text00044", maxp=4, tail=1)
dump("text00045", maxp=3, tail=1)
dump("text00046", maxp=3, tail=1)
print("\n== 卷3 Chapter 9/10/11 ==")
dump("text00067", maxp=4, tail=1)
dump("text00068", maxp=3, tail=1)
dump("text00069", maxp=3, tail=1)
