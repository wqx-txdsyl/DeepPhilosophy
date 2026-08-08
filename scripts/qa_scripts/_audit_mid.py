# -*- coding: utf-8 -*-
"""中等差异书段落匹配: 存在与虚无 / 加缪全集 / 哲学的慰藉 / 悉达多"""
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

sus = [
    ("存在与虚无", "274c59617693", ["存在与虚无"]),
    ("加缪全集", "8078e65c3cb8", ["加缪全集"]),
    ("哲学的慰藉", "8a451d16f1b4", ["哲学的慰藉"]),
    ("悉达多", "436b1e7f9477", ["悉达多"]),
    ("瓦尔登湖", "5135fe68ee4a", ["瓦尔登湖"]),
    ("沉思录", "a43cd7310a57", ["沉思录"]),
    ("谈谈方法", "8c3044772b18", ["谈谈方法"]),
    ("内在体验", "8383f4e551c4", ["内在体验"]),
]
for name, bid, kws in sus:
    lib = lib_paras(bid)
    lib_norm = {norm(s): s for s in lib}
    print(f"\n【{name}】 库段落={len(lib)}")
    for p in sorted(glob.glob(r"F:/philosophy/**/*.epub", recursive=True)):
        bn = os.path.basename(p)
        if not all(k in p for k in kws):
            continue
        try:
            paras = epub_paras(p)
        except Exception as e:
            print(f"  ERR {p}: {e}")
            continue
        src_n = {norm(s) for s in paras}
        hit = sum(1 for s in lib if norm(s) in src_n)
        print(f"  源 {bn}: 源段={len(paras)} 库命中={hit}/{len(lib)} ({hit*100//len(lib)}%)")
