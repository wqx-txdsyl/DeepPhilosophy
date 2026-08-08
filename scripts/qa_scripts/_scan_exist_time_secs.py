# -*- coding: utf-8 -*-
"""存在与时间 黄金流内节标题行(第X节)形态扫描 — 为分级标题(篇→章→节)做准备"""
import sys, re, json, zipfile, os
from html.parser import HTMLParser
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

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

z = zipfile.ZipFile(r"F:/philosophy/西方/马丁·海德格尔/存在与时间.epub")
files = sorted([n for n in z.namelist() if re.search(r"part\d+\.html$", n)],
               key=lambda n: int(re.search(r"part(\d+)\.html$", n).group(1)))
SEC_RE = re.compile(r"^第[一二三四五六七八九十百零]+节[　\s]?\S")
CN = "零一二三四五六七八九十"
def cn2int(s):
    if not s: return None
    if s in CN: return CN.index(s)
    if s.startswith("十"): return 10 + (CN.index(s[1]) if len(s) > 1 else 0)
    if "十" in s:
        a, b = s.split("十")
        return CN.index(a) * 10 + (CN.index(b) if b else 0)
    return None

cur_sec = None
for fn in files:
    num = int(re.search(r"part(\d+)\.html$", fn).group(1))
    if num < 3: continue
    c = z.read(fn).decode("utf-8", errors="replace")
    p = PExtract(); p.feed(c)
    for i, t in enumerate(p.blocks):
        t = re.sub(r"\s+", " ", t).strip()
        if not t: continue
        m = SEC_RE.match(t)
        if m:
            # 取"第X节"后的标题文本
            s = t[len(m.group(0)):].strip()
            print(f"{fn}[{i}] 第{cn2int(re.search(r'第([一二三四五六七八九十百零]+)节', t).group(1))}节: {s!r}")
