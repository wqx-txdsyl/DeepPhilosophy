# -*- coding: utf-8 -*-
"""查与神对话 epub 边缘文件: text00112(text00001-04/24-28 等装饰页) 内容"""
import sys, re, zipfile
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
for fn in ["text00001", "text00002", "text00112", "text00144", "text00145"]:
    c = z.read(f"OEBPS/{fn}.html").decode("utf-8", errors="replace")
    p = PExtract(); p.feed(c)
    hs = [re.sub(r"\s+", " ", t).strip() for tag, t in p.blocks if tag == "h"]
    ps = [re.sub(r"\s+", " ", t).strip() for tag, t in p.blocks if tag == "p"]
    print(f"--- {fn} h={hs}")
    for t in ps:
        print(f"   p={t[:60]!r}")
