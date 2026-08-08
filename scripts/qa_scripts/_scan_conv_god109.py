# -*- coding: utf-8 -*-
"""抽检库[107-110] 内容 vs 源 text00131-143 首段, 确认 109/110 实际内容"""
import sys, re, json, os, zipfile
from html.parser import HTMLParser
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

D = r"f:\program\Python\PhiAgent\backend\data\book_chapters\7657ef4a2cd3"

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

print("=== 库 [107][108][109][110] ===")
for i in [107, 108, 109, 110]:
    j = json.load(open(os.path.join(D, f"{i}.json"), encoding="utf-8"))
    ts = [norm_body(b["value"]) for b in j["content"] if b.get("type") == "text"]
    print(f"\n[{i}] {j['title'][:20]} 段={len(ts)}")
    print(f"  首: {ts[0][:50]}")
    print(f"  末: {ts[-1][:50]}")

print("\n=== 源 text00131-143 首段 ===")
z = zipfile.ZipFile(r"F:/philosophy/西方/尼尔·唐纳德·沃尔什/与神对话(全5卷）.epub")
for n in range(131, 144):
    c = z.read(f"OEBPS/text{n:05d}.html").decode("utf-8", errors="replace")
    p = PExtract(); p.feed(c)
    ps = [norm_body(t) for tag, t in p.blocks if tag == "p"]
    ps = [t for t in ps if t]
    hs = [norm_body(t) for tag, t in p.blocks if tag == "h"]
    print(f"text{n:05d} {hs[:1]} 段={len(ps)} 首: {(ps[0][:40] if ps else '-')}")
