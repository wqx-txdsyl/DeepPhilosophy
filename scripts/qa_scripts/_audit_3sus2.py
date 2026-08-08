# -*- coding: utf-8 -*-
"""验证: 和狗狗 ch3 vs 源 part0006_split_001; 心理学炼金术缺段确认; 尼采四册源全览"""
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
    def handle_endtag(self, tag):
        if tag == "p" and self.cur == "p":
            self.blocks.append("".join(self.buf)); self.cur = None
    def handle_data(self, d):
        if self.cur: self.buf.append(d)

def gold(path, fn):
    z = zipfile.ZipFile(path)
    c = z.read(fn).decode("utf-8", errors="replace")
    p = PExtract(); p.feed(c)
    return [re.sub(r"\s+", " ", t).strip() for t in p.blocks if re.sub(r"\s+", "", t)]

# --- 1. 和狗狗 ch3 与源正文对比 ---
print("== 和狗狗 库ch3 (第一次漫步) vs 源 part0006_split_001 ==")
j = json.load(open(os.path.join(CH, "230068c4c6b6", "3.json"), encoding="utf-8"))
lib_ps = [b["value"] for b in j["content"] if b.get("type") == "text"][1:]
src_ps = gold(r"F:/philosophy/new/100本哲学书单全收录/96和狗狗的十二次哲学漫步/和狗狗的十二次哲学漫步(1).epub",
              "text/part0006_split_001.html")
print(f"库段数={len(lib_ps)} 源段数={len(src_ps)}")
print(f"库首段: {lib_ps[0][:60]!r}")
print(f"源首段: {src_ps[0][:60]!r}")
print(f"库末段: {lib_ps[-1][:60]!r}")
print(f"源末段: {src_ps[-1][:60]!r}")
# 库段是否按序在源中
ok = True
src_set = set(src_ps)
for i, s in enumerate(lib_ps):
    if s not in src_set:
        ok = False
        print(f"  第{i}段不在源中: {s[:50]!r}")
print("库段全部在源中:", ok)
# 库段是否是源的前缀序列
cut = 0
for i, s in enumerate(lib_ps):
    if i < len(src_ps) and src_ps[i] == s:
        cut += 1
    else:
        break
print(f"库与源前{cut}段逐段相同(之后断) → 截断位置确认: {cut}/{len(lib_ps)}")

# --- 2. 心理学炼金术: 源缺哪些章节 ---
print("\n== 心理学和炼金术: 源完整章节 vs 库 ==")
src = r"F:/philosophy/西方/卡尔·古斯塔夫·荣格/心理学和炼金术.epub"
z = zipfile.ZipFile(src)
for fn in sorted(z.namelist()):
    if not fn.lower().endswith((".xhtml", ".html")) or "toc" in fn.lower():
        continue
    c = z.read(fn).decode("utf-8", errors="replace")
    p = PExtract(); p.feed(c)
    hs = [re.sub(r"\s+", " ", t).strip() for tag, t in [(x, y) for x, y in []]]
    # h 单独提取
    hs = []
    for t_ in p.blocks:
        pass
    total = sum(len(re.sub(r"\s+", "", t)) for t in p.blocks)
    if total > 200:
        print(f"  {fn.split('/')[-1]}: {total:,} 字")
