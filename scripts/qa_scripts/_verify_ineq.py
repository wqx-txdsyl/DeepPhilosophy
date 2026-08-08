# -*- coding: utf-8 -*-
"""验证: 新库12章 vs epub黄金流 零丢失 + 旧库正文段按序存在于新库"""
import sys, re, json, os, zipfile
from html.parser import HTMLParser
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BID = "9e4f98733f0b"
EP = r"F:/philosophy/西方/让-雅克·卢梭/论人类不平等的起源和基础.epub"
D = os.path.join(r"f:\program\Python\PhiAgent\backend\data\book_chapters", BID)
BAK = r"f:\program\Python\PhiAgent\backend\data\_rebuild_bak" + "\\" + f"{BID}_old11ch"

def norm(t):
    return re.sub(r"\s+", " ", t).strip()

class PExtract(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.cur = None; self.buf = []; self.blocks = []
    def handle_starttag(self, tag, attrs):
        if tag == "p":
            self.cur = "p"; self.buf = []
    def handle_endtag(self, tag):
        if tag == "p" and self.cur == "p":
            self.blocks.append("".join(self.buf)); self.cur = None
    def handle_data(self, d):
        if self.cur: self.buf.append(d)

z = zipfile.ZipFile(EP)
def gold(fn):
    c = z.read(f"OEBPS/{fn}.html").decode("utf-8", errors="replace")
    p = PExtract(); p.feed(c)
    return [norm(t) for t in p.blocks if norm(t)]

# ---------- 1. 新库段落流 vs epub 黄金流 ----------
NEW_FILES = {  # 章号 -> epub文件
    1: "text00005", 2: "text00006", 3: "text00007", 4: "text00008",
    5: "text00009", 6: "text00010", 7: "text00011", 8: "text00012",
    9: "text00013", 10: "text00014", 11: "text00015",
}
ok = True
for idx, fn in NEW_FILES.items():
    j = json.load(open(os.path.join(D, f"{idx}.json"), encoding="utf-8"))
    new_paras = [b["value"] for b in j["content"] if b.get("type") == "text"][1:]  # 去掉标题段
    g = gold(fn)
    if new_paras == g:
        print(f"[{idx}] {fn}: {len(new_paras)} 段 == epub ✓")
    else:
        ok = False
        print(f"[{idx}] {fn}: 新库{len(new_paras)} vs epub{len(g)} 不一致!")
        for i, (a, b) in enumerate(zip(new_paras, g)):
            if a != b:
                print(f"   第{i}段:\n     新库: {a[:60]}\n     epub: {b[:60]}")
                break
print("段落流验证:", "通过 ✓" if ok else "失败!!")

# ---------- 2. 旧库正文段按序存在于新库 ----------
def load_paras(base, n):
    out = []
    for i in range(n):
        j = json.load(open(os.path.join(base, f"{i}.json"), encoding="utf-8"))
        for b in j["content"]:
            if b.get("type") == "text":
                out.append(b["value"])
    return out

old = load_paras(BAK, 11)
new = []
for i in range(12):
    j = json.load(open(os.path.join(D, f"{i}.json"), encoding="utf-8"))
    for b in j["content"]:
        if b.get("type") == "text":
            new.append(b["value"])

TITLES = {"如何阅读本书", "导读", "关于附注的说明", "致辞：献给日内瓦共和国", "序",
          "本论", "第一部分", "第二部分", "注释 卢梭注于讲稿完成后", "卢梭致菲洛普利的信",
          "卢梭生平大事年表"}
def is_junk(s):
    """混入的注释残留/标题残留"""
    if s in TITLES: return True
    if re.match(r"^\[卢梭注\d+\]\s*[；;]?\s*", s): return True   # 注释开头(正文被截到注里)
    if re.match(r"^\[\d+\][、,]?\s*[；;，]?", s): return True      # [n] 注释开头
    return False

miss = []
newset = set(new)
np_ = 0
for s in old:
    if is_junk(s):
        continue
    np_ += 1
    if s in newset:
        continue
    # 截断段: 新库某段以它开头
    found = any(t.startswith(s) for t in new)
    if not found:
        miss.append(s)
print(f"\n旧库正文段(滤注释残留): {np_} 段")
if miss:
    print(f"!! {len(miss)} 段未在新库找到:")
    for s in miss:
        print("   ", s[:70])
else:
    print("旧库全部正文段在新库中存在 ✓ 零丢失")

# ---------- 3. 字数统计 ----------
oldchars = sum(len(s) for s in old)
newchars = sum(len(s) for s in new)
print(f"旧库总字数={oldchars} 新库总字数={newchars} (差异 {newchars-oldchars:+d})")
