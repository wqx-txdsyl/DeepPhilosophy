# -*- coding: utf-8 -*-
"""《论人类不平等的起源和基础》epub 完全重建 v2
修正: 段落内空白压缩为单空格(不删除), h1 标题全删空白+去[1]尾。
用 HTMLParser 提取黄金标准段落流, 验证正则提取零丢失。
"""
import sys, re, json, zipfile, os
from html.parser import HTMLParser
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, r"f:\program\Python\PhiAgent\backend\tools")
import rebuild_auto as ra

BID = "9e4f98733f0b"
EP = r"F:/philosophy/西方/让-雅克·卢梭/论人类不平等的起源和基础.epub"
D = os.path.join(ra.CH, BID)

class PExtract(HTMLParser):
    """提取 <p> 与 <h1-6> 的纯文本(含子标签文本)"""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.cur = None       # 当前块: None|"p"|"h"
        self.buf = []
        self.blocks = []      # (tag, text)
    def handle_starttag(self, tag, attrs):
        if tag == "p":
            self.cur = "p"; self.buf = []
        elif re.match(r"h[1-6]$", tag):
            self.cur = "h"; self.buf = []
    def handle_endtag(self, tag):
        if tag == "p" and self.cur == "p":
            self.blocks.append(("p", "".join(self.buf))); self.cur = None
        elif re.match(r"h[1-6]$", tag) and self.cur == "h":
            self.blocks.append(("h", "".join(self.buf))); self.cur = None
    def handle_data(self, d):
        if self.cur:
            self.buf.append(d)

def gold_blocks(fn):
    c = z.read(f"OEBPS/{fn}.html").decode("utf-8", errors="replace")
    p = PExtract(); p.feed(c)
    return p.blocks

def norm_body(t):
    t = re.sub(r"\s+", " ", t).strip()   # 压缩为单空格
    return t

def clean_title(t):
    t = re.sub(r"\s+", "", t)
    t = re.sub(r"\[1\]$", "", t).strip()
    return t

z = zipfile.ZipFile(EP)

# ---------- 验证所有文件的段落流一致性(epub7 说 text00015 有 63 p) ----------
for fn in sorted(n for n in z.namelist() if re.match(r"OEBPS/text\d+\.html$", n)):
    bs = gold_blocks(fn[6:-5])
    ps = [t for tag, t in bs if tag == "p"]
    hs = [t for tag, t in bs if tag == "h"]
    print(f"{fn}: p={len(ps)} h={len(hs)} h1={clean_title(hs[0]) if hs else ''!r}")

# ---------- 章节定义 ----------
CHS = [
    ("text00005", "导读"),
    ("text00006", "关于附注的说明"),
    ("text00007", "致辞：献给日内瓦共和国"),
    ("text00008", "序"),
    ("text00009", "本论"),
    ("text00010", "第一部分"),
    ("text00011", "第二部分"),
    ("text00012", "注释 卢梭注于讲稿完成后"),
    ("text00013", "卢梭致菲洛普利的信"),
    ("text00014", "卢梭生平大事年表"),
    ("text00015", "注释"),
]

# ---------- 逐章写入 ----------
tot = 0
for i, (fn, title) in enumerate(CHS, start=1):
    bs = gold_blocks(fn)
    ps = [norm_body(t) for tag, t in bs if tag == "p" and norm_body(t)]
    content = [{"type": "text", "value": title}] + [{"type": "text", "value": p} for p in ps]
    json.dump({"title": title, "content": content, "index": i},
              open(os.path.join(D, f"{i}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    n = sum(len(p) for p in ps) + len(title)
    tot += n
    print(f"写入 {i}.json {fn} {title!r} 段数={len(content)} 字={n}")

# ---------- meta ----------
toc = [{"type": "chapter", "title": "如何阅读本书", "index": 0}]
toc += [{"type": "chapter", "title": t, "index": i} for i, (_, t) in enumerate(CHS, start=1)]
m = json.load(open(os.path.join(D, "meta.json"), encoding="utf-8"))
m["toc"] = toc
m["chapterCount"] = len(toc)
m["chapterTitles"] = ["如何阅读本书"] + [t for _, t in CHS]
json.dump(m, open(os.path.join(D, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"\nmeta chapterCount={len(toc)} 正文总字数(不含0章)={tot}")

# ---------- 00004 验证(库0 是否含 epub 全部段落) ----------
old0 = json.load(open(os.path.join(D, "0.json"), encoding="utf-8"))
old0texts = [b["value"] for b in old0["content"] if b.get("type") == "text"]
ep4 = [norm_body(t) for tag, t in gold_blocks("text00004") if tag == "p" and norm_body(t)]
missing = [t for t in ep4 if t not in old0texts]
print(f"\n== 00004: epub 段={len(ep4)} 库0缺={len(missing)}")
for t in missing:
    print("  缺:", t[:60])

# ---------- 三端同步 ----------
ra.sync_three(BID)
print("sync_three 完成")
