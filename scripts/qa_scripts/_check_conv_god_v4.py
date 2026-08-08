# -*- coding: utf-8 -*-
"""v3 结果深检:
1. 新库独有 25 字(3处)在旧库中是否存在(匹配歧义 vs 真丢字)
2. 黄金流 vs 新库零丢失(拆段插入 bug 检查)
3. 各插入段与 v2 期望位置核对
"""
import sys, re, json, os, zipfile, difflib
from html.parser import HTMLParser
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

D = r"f:\program\Python\PhiAgent\backend\data\book_chapters\7657ef4a2cd3"
OLDBAK = r"f:\program\Python\PhiAgent\backend\data\_rebuild_bak\7657ef4a2cd3_old111ch"
EP = r"F:/philosophy/西方/尼尔·唐纳德·沃尔什/与神对话(全5卷）.epub"
JUNK_CH = {1, 2, 3, 23, 24, 25, 49, 50, 51, 77, 78, 104}

def dw(t):
    return re.sub(r"\s+", "", t)

# 新库全文(去空白)
new_dw = ""
new_paras = []
for i in range(117):
    j = json.load(open(os.path.join(D, f"{i}.json"), encoding="utf-8"))
    for b in j["content"]:
        if b.get("type") == "text":
            t = b["value"]
            new_paras.append(t)
            new_dw += dw(t)
print(f"新库: {len(new_paras)} 段 {len(new_dw)} 字")

# 旧库(剔除垃圾章)全文
old_dw = ""
old_paras = []
for i in range(111):
    if i in JUNK_CH:
        continue
    j = json.load(open(os.path.join(OLDBAK, f"{i}.json"), encoding="utf-8"))
    for b in j["content"]:
        if b.get("type") == "text":
            t = b["value"].strip()
            if t:
                old_paras.append(t)
                old_dw += dw(t)
print(f"旧库(剔除垃圾): {len(old_paras)} 段 {len(old_dw)} 字")

print("\n=== 1. 新库独有 3 段在旧库的存在性 ===")
probes = ["。我来看看能否总结出你在第三章中谈到的要点", "是："]
for p in probes:
    pd = dw(p)
    print(f"\n探针 {p[:30]!r} (去空白 {len(pd)}字):")
    print(f"  旧库出现 {old_dw.count(pd)} 次, 新库出现 {new_dw.count(pd)} 次")
    if old_dw.count(pd):
        k = old_dw.find(pd)
        print(f"  旧库上下文: ...{old_dw[max(0,k-25):k+30]}...")
        # 找所在旧库段
        acc = 0
        for pi, t in enumerate(old_paras):
            if acc + len(dw(t)) > k:
                print(f"  所在旧库段[{pi}](章{old_paras[pi][:0] or ''}): {t[:60]!r}")
                break
            acc += len(dw(t))
    k = new_dw.find(pd)
    if k >= 0:
        print(f"  新库上下文: ...{new_dw[max(0,k-25):k+30]}...")
        acc = 0
        for pi, t in enumerate(new_paras):
            if acc + len(dw(t)) > k:
                # 找章号
                cc = 0; ci = -1
                for i in range(117):
                    j = json.load(open(os.path.join(D, f"{i}.json"), encoding="utf-8"))
                    n = sum(1 for b in j["content"] if b.get("type") == "text")
                    if cc + n > pi:
                        ci = i; break
                    cc += n
                print(f"  所在新库章[{ci}]: {t[:60]!r}")
                break
            acc += len(dw(t))

print("\n=== 2. 黄金流 vs 新库 零丢失 ===")
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

z = zipfile.ZipFile(EP)
opf = [n for n in z.namelist() if n.lower().endswith(".opf")][0]
c = z.read(opf).decode("utf-8", errors="replace")
items = {}
for m in re.finditer(r'<item\b([^>]*)/?>', c):
    attrs = dict(re.findall(r'(\w+)\s*=\s*"([^"]*)"', m.group(1)))
    if attrs.get("href"):
        items[attrs.get("id", "")] = (attrs["href"], os.path.dirname(opf))
order = []
for s in re.findall(r'<itemref\b[^>]*?idref="([^"]+)"', c):
    if s in items:
        href, base = items[s]
        p = (os.path.join(base, href) if not href.startswith(base) else href).replace("\\", "/")
        if p not in z.namelist():
            cand = [n for n in z.namelist() if n.endswith("/" + href)]
            p = cand[0] if cand else p
        order.append(p)
SKIP_NUM = set(range(1, 5)) | set(range(24, 29)) | set(range(52, 57)) | \
           set(range(82, 87)) | set(range(112, 117)) | {84, 144, 145}
gold_dw = ""
gold_paras = []
for fn in order:
    m = re.search(r"text(\d{5})\.html$", fn)
    if m and int(m.group(1)) in SKIP_NUM:
        continue
    c2 = z.read(fn).decode("utf-8", errors="replace")
    p = PExtract(); p.feed(c2)
    for t in p.blocks:
        t2 = re.sub(r"\s+", " ", t).strip()
        if t2:
            gold_paras.append(t2)
            gold_dw += dw(t2)
print(f"黄金流: {len(gold_paras)} 段 {len(gold_dw)} 字")
sm = difflib.SequenceMatcher(a=gold_dw, b=new_dw, autojunk=False)
gd_only = 0
for op, i1, i2, j1, j2 in sm.get_opcodes():
    if op in ("delete", "replace"):
        gd_only += i2 - i1
print(f"黄金独有(新库缺) = {gd_only} 字", "✓ 零丢失" if gd_only == 0 else "✗!!")
if gd_only:
    for op, i1, i2, j1, j2 in sm.get_opcodes():
        if op in ("delete", "replace") and i2 - i1 > 0:
            t = gold_dw[i1:i2]
            print(f"  gold独有({len(t)}字): {t[:60]!r}")
            break
# 新库比黄金多出的(= 插入正文)分布
ins_total = 0
for op, i1, i2, j1, j2 in sm.get_opcodes():
    if op in ("insert", "replace"):
        ins_total += j2 - j1
print(f"新库多出(插入正文) = {ins_total} 字")

print("\n=== 3. 关键章字数核对(应等于源+v2期望) ===")
# v2 期望: 导读 28段5238 献词一 12段94 献词二 11段90 前言 15段1799+?
EXP = {1: (28, 5238), 2: (12, 94), 3: (11, 90), 4: (18, 1899), 5: (478, 31623),
       7: (121+13, 8135+786), 8: (54+10, 2310+744), 24: (244+18, 9453+557),
       25: (81+16, 4272+461), 30: (197+7, 11396+113), 32: (122+2, 6216+103),
       33: (217+12, 10245+196), 39: (180+7, 8620+178), 40: (195+6, 8348+121),
       41: (88+1, 4267+16), 48: (184+4, 11615+56), 64: (153+2, 7781+12),
       65: (304+1, 12905+27), 93: (68, 3016), 20: (15, 97), 43: (16, 125), 68: (12, 116)}
for i, (en, ew) in EXP.items():
    j = json.load(open(os.path.join(D, f"{i}.json"), encoding="utf-8"))
    ts = [b["value"] for b in j["content"] if b.get("type") == "text"]
    w = sum(len(dw(t)) for t in ts)
    ok = "✓" if len(ts) == en and w == ew else "?"
    print(f"  [{i}] {j['title'][:12]:<14} 段{len(ts)}/{en} 字{w}/{ew} {ok}")
