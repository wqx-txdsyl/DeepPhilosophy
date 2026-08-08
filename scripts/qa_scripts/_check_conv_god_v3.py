# -*- coding: utf-8 -*-
"""查 v2 错插内容: 导读/献词/前言 章内的异常段"""
import sys, re, json, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

D = r"f:\program\Python\PhiAgent\backend\data\book_chapters\7657ef4a2cd3"
# 源各文件首段(判断插入段)
def src_first(n):
    import zipfile
    from html.parser import HTMLParser
    class P(HTMLParser):
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
    z = zipfile.ZipFile(r"F:/philosophy/西方/尼尔·唐纳德·沃尔什/与神对话(全5卷）.epub")
    c = z.read(f"OEBPS/text{n:05d}.html").decode("utf-8", errors="replace")
    p = P(); p.feed(c)
    return [re.sub(r"\s+", " ", t).strip() for t in p.blocks if t.strip()]

# 源文件 → 章号 映射
CH_SRC = {1: 5, 20: 29, 43: 57, 68: 87, 93: 117}
for ci, sn in CH_SRC.items():
    j = json.load(open(os.path.join(D, f"{ci}.json"), encoding="utf-8"))
    ts = [b["value"] for b in j["content"] if b.get("type") == "text"]
    src_ps = src_first(sn)
    src_set = {re.sub(r"\s+", "", t) for t in src_ps}
    extra = [t for t in ts if re.sub(r"\s+", "", t) not in src_set]
    print(f"\n=== 章[{ci}] {j['title']} 源{sn} 段 {len(ts)} (源 {len(src_ps)}), 非源段 {len(extra)}:")
    for t in extra:
        print(f"   + {t[:70]!r}")
