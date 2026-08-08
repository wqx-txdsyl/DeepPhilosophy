# -*- coding: utf-8 -*-
"""对 3 本可疑书: 库全段落 vs F:/philosophy 下所有同书源(epub/txt) 段落匹配率
找库真实来源 + 计算库在最佳源的覆盖率"""
import sys, os, re, json, glob, zipfile
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

def norm(t):
    return re.sub(r"\s+", "", t)

def lib_paras(bid):
    out = []
    meta = json.load(open(os.path.join(CH, bid, "meta.json"), encoding="utf-8"))
    for i in range(meta.get("chapterCount", 0)):
        p = os.path.join(CH, bid, f"{i}.json")
        if not os.path.exists(p): continue
        j = json.load(open(p, encoding="utf-8"))
        for b in j.get("content", []):
            if b.get("type") == "text":
                out.append(b["value"])
    return out

def epub_paras(path):
    z = zipfile.ZipFile(path)
    out = []
    for n in sorted(z.namelist()):
        if not n.lower().endswith((".xhtml", ".html")) or "toc" in n.lower():
            continue
        c = z.read(n).decode("utf-8", errors="replace")
        p = PExtract(); p.feed(c)
        out.extend(p.blocks)
    return [re.sub(r"\s+", " ", t).strip() for t in out if re.sub(r"\s+", "", t)]

def txt_paras(path):
    c = open(path, encoding="utf-8", errors="replace").read()
    return [re.sub(r"\s+", " ", t).strip() for t in c.split("\n") if re.sub(r"\s+", "", t)]

sus = [
    ("和狗狗的十二次哲学漫步", "230068c4c6b6", ["狗狗", "十二次哲学漫步"]),
    ("心理学和炼金术", "e63a26081cb9", ["心理学和炼金术", "炼金术"]),
    ("尼采经典著作及研究丛书", "4cc9d23c7dbf", ["尼采经典", "尼采"]),
]
for name, bid, kws in sus:
    lib = lib_paras(bid)
    lib_n = {norm(s): s for s in lib}
    print(f"\n{'='*60}\n【{name}】 库段落={len(lib)}")
    # 收集候选源
    cands = []
    for p in glob.glob(r"F:/philosophy/**/*", recursive=True):
        if os.path.isfile(p) and (p.lower().endswith(".epub") or p.lower().endswith(".txt")):
            if all(k in p for k in kws):
                cands.append(p)
    for p in cands:
        try:
            paras = epub_paras(p) if p.lower().endswith(".epub") else txt_paras(p)
        except Exception as e:
            print(f"  ERR {p}: {e}")
            continue
        src_n = {norm(s) for s in paras}
        hit = sum(1 for s in lib if norm(s) in src_n)
        cover = sum(1 for s in lib if any(norm(t) == norm(s) or norm(t).startswith(norm(s)) for t in paras))
        print(f"  源: {p}")
        print(f"    源段数={len(paras)} 库精确命中={hit}/{len(lib)} 前缀命中={cover}/{len(lib)}")
