# -*- coding: utf-8 -*-
"""存在与时间 源 epub: 找每个 part 文件内的真实章节标题行
《存在与时间》真实结构 = 导论 + 第一篇6章 + 第二篇6章
目标: 确定正确章节边界(真实标题所在行/文件)
"""
import sys, os, re, glob, zipfile
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

path = r"F:/philosophy/西方/马丁·海德格尔/存在与时间.epub"
z = zipfile.ZipFile(path)

# 按 spine 序取 part0003-0014
import fnmatch
files = sorted([n for n in z.namelist() if re.search(r"part\d+\.html$", n)],
               key=lambda n: int(re.search(r"part(\d+)\.html$", n).group(1)))
print("spine 文件序:", files)

TITLE_RE = re.compile(r"^(导论|第[一二三四五六]篇|第[一二三四五六]章|结语|附录|译后记|目录|第一章|第二章|第三章|第四章|第五章|第六章|第七章|第八章|第九章|第十章|第十一章|第十二章)")
# 更宽: 行以"第X"开头或 3-20字独立短行含"问题|存在|时间|此在"
WIDE_RE = re.compile(r"^(第[一二三四五六0-9]+[篇章节部]|导论|序|前言|引言|附论|结语|跋|译后记|附录)")

for fn in files:
    c = z.read(fn).decode("utf-8", errors="replace")
    p = PExtract(); p.feed(c)
    paras = [re.sub(r"\s+", " ", t).strip() for t in p.blocks if re.sub(r"\s+", "", t)]
    print(f"\n===== {fn} ({len(paras)} 段) =====")
    print(f"  首3段: {paras[:3]}")
    print(f"  末2段: {paras[-2:]}")
    hits = []
    for i, t in enumerate(paras):
        ts = re.sub(r"\s+", "", t)
        if WIDE_RE.match(ts) and len(ts) <= 30:
            hits.append(f"  [{i}] {t}")
    if hits:
        print("  疑似标题行:")
        print("\n".join(hits))
