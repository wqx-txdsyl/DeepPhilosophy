# -*- coding: utf-8 -*-
"""《存在与时间》重建 v2 — 13 章 + 三级分级标题(篇 part / 章 chapter / 节 section)
- 按源内真实标题行切 13 章(导论+第一篇6章+第二篇6章), 真实标题, 断段合并
- 节标题行(第1-83节)保持 text 块(向量/正文零影响), 同时登记进 meta.toc 的 section 条目
- section: {type, title, index=章文件号, sec=章内text块序号}
- 零丢失验证: 新库段落流 == 黄金流(除剥离行); 节号 1-83 连续无缺
"""
import sys, re, json, zipfile, os
from html.parser import HTMLParser
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, r"f:\program\Python\PhiAgent\backend\tools")
import rebuild_auto as ra

BID = "c5013f33fe01"
EP = r"F:/philosophy/西方/马丁·海德格尔/存在与时间.epub"
D = os.path.join(ra.CH, BID)

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

z = zipfile.ZipFile(EP)

# ---------- 1. 黄金段落流 ----------
files = sorted([n for n in z.namelist() if re.search(r"part\d+\.html$", n)],
               key=lambda n: int(re.search(r"part(\d+)\.html$", n).group(1)))
gold = []
for fn in files:
    if int(re.search(r"part(\d+)\.html$", fn).group(1)) < 3: continue
    c = z.read(fn).decode("utf-8", errors="replace")
    p = PExtract(); p.feed(c)
    for i, t in enumerate(p.blocks):
        t = norm_body(t)
        if t:
            gold.append((fn, i, t))
print(f"黄金流: {len(gold)} 段, 总字 {sum(len(t) for _,_,t in gold)}")

# ---------- 2. 标题行定位 ----------
TITLES = [
    ("part0003", "导论 概述存在意义的问题"),
    ("part0004", "第一章 该说准备性的此在分析之任务"),
    ("part0004", "第二章 一般的“在世界之中存在”——此在的基本建构"),
    ("part0004", "第三章 世界之为世界"),
    ("part0005", "第四章 在世作为共在与自己存在。“常人”"),
    ("part0006", "第五章 “在之中”之为“在之中”"),
    ("part0007", "第六章 操心——此在的存在"),
    ("part0009", "第一章 此在之可能的整体存在，向死存在"),
    ("part0009", "第二章 一种本真能在的此在式的见证，决心"),
    ("part0010", "第三章 此在的本真整体能在与时间性之为操心的存在论意义"),
    ("part0011", "第四章 时间性与日常性"),
    ("part0012", "第五章 时间性与历史性"),
    ("part0013", "第六章 时间性以及作为流俗时间概念源头的时间内状态"),
]
STRIP = [
    ("part0003", "作者： （德）海德格尔 著，陈嘉映，王庆节 合译"),
    ("part0004", "第一部 依时间性阐释此在，解说时间之为存在问题的超越的视野"),
    ("part0004", "第一篇 准备性的此在基础分析"),
    ("part0009", "第二篇 此在与时间性"),
    ("part0014", "- 1 -"),
]

def locate(fn, text):
    hits = [gi for gi, (f, i, t) in enumerate(gold) if f.endswith(f"/{fn}.html") and t == text]
    if len(hits) != 1:
        print(f"!! 定位失败 {fn} {text!r}: 命中 {len(hits)}"); return None
    return hits[0]

idx = {}
for fn, text in TITLES:
    gi = locate(fn, text)
    if gi is None: sys.exit(f"终止: {fn} {text}")
    idx[text] = gi
    print(f"定位: {fn} [{gi}] {text}")
stripped = [gi for fn, text in STRIP if (gi := locate(fn, text)) is not None]

# ---------- 3. 组装 13 章 ----------
order = [t for _, t in TITLES]
bounds = [idx[t] for t in order] + [len(gold)]
skip = set(stripped)
CH_TITLES = [
    "导论 概述存在意义的问题",
    "第一章 该说准备性的此在分析之任务",
    "第二章 一般的“在世界之中存在”——此在的基本建构",
    "第三章 世界之为世界",
    "第四章 在世作为共在与自己存在。“常人”",
    "第五章 “在之中”之为“在之中”",
    "第六章 操心——此在的存在",
    "第一章 此在之可能的整体存在，与向死存在",
    "第二章 一种本真能在的此在式的见证，决心",
    "第三章 此在的本真整体能在与时间性之为操心的存在论意义",
    "第四章 时间性与日常性",
    "第五章 时间性与历史性",
    "第六章 时间性以及作为流俗时间概念源头的时间内状态",
]
PARTS = [
    {"type": "part", "title": "导论", "level": 0},
    {"type": "part", "title": "第一篇 准备性的此在基础分析", "level": 0},
    {"type": "part", "title": "第二篇 此在与时间性", "level": 0},
]

# 节标题行: "第X节 标题" 全行(独立段, ≤30字); 导论内部章标题行(part0003 内"第一章/第二章"行)
CN = "零一二三四五六七八九十"
def cn2int(s):
    if len(s) == 1: return CN.index(s)
    if s.startswith("十"): return 10 + (CN.index(s[1]) if len(s) > 1 else 0)
    if "十" in s:
        a, b = s.split("十")
        return CN.index(a) * 10 + (CN.index(b) if b else 0)
    return None
SEC_RE = re.compile(r"^第([一二三四五六七八九十百零]+)节")

toc = []          # 最终目录
toc.append({"type": "chapter", "title": "如何阅读本书", "index": 0, "level": 1})
sec_titles = []   # (章文件号, 标题, sec块序号)
sec_nums = []     # 节号收集(验证 1-83)
tot = 0

def ch_paras(ci):
    """章 ci (0起) 的正文段落列表 + 节信息"""
    paras = []
    k = 0
    for gi in range(bounds[ci] + 1, bounds[ci + 1]):
        if gi in skip: continue
        t = gold[gi][2]
        m = SEC_RE.match(t)
        if m and len(t) <= 50:
            n = cn2int(m.group(1))
            if n:
                sec_titles.append((ci + 1, t, k))
                sec_nums.append(n)
        # 导论内部章标题行(part0003 内)也登记
        if ci == 0 and gold[gi][0].endswith("/part0003.html") and re.match(r"^第[一二三四五六七八九十]+章 ", t):
            sec_titles.append((1, t, k))
        paras.append(t)
        k += 1
    return paras

for ci in range(13):
    paras = ch_paras(ci)
    content = [{"type": "text", "value": p} for p in paras]
    n = sum(len(p) for p in paras); tot += n
    json.dump({"title": CH_TITLES[ci], "content": content, "index": ci + 1},
              open(os.path.join(D, f"{ci + 1}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"章{ci+1}: {CH_TITLES[ci]!r} 段={len(paras)} 字={n}")
print(f"正文总字数(13章) = {tot}")

# 节号验证: 1-83 连续
sec_nums.sort()
expect = list(range(1, 84))
if sec_nums == expect:
    print(f"✓ 节号 1-83 连续完整 ({len(sec_nums)} 节)")
else:
    miss = [n for n in expect if n not in sec_nums]
    dup = [n for n in set(sec_nums) if sec_nums.count(n) > 1]
    print(f"✗ 节号异常: 缺 {miss} 重复 {dup}")

# ---------- 4. meta.toc (part + chapter + section 三级) ----------
toc.append(PARTS[0])   # 导论
toc.append({"type": "chapter", "title": CH_TITLES[0], "index": 1, "level": 1})
for s_title, s_sec in [(t, s) for (c, t, s) in sec_titles if c == 1]:
    toc.append({"type": "section", "title": s_title, "index": 1, "sec": s_sec, "level": 2})
for part, (lo, hi) in zip(PARTS[1:], ((1, 7), (7, 13))):   # 第一篇=章2-7, 第二篇=章8-13
    toc.append(part)
    for ci in range(lo, hi):
        toc.append({"type": "chapter", "title": CH_TITLES[ci], "index": ci + 1, "level": 1})
        for c, t, s in sec_titles:
            if c == ci + 1:
                toc.append({"type": "section", "title": t, "index": c, "sec": s, "level": 2})

m = json.load(open(os.path.join(D, "meta.json"), encoding="utf-8"))
m["toc"] = toc
m["chapterCount"] = 14
m["chapterTitles"] = ["如何阅读本书"] + CH_TITLES
json.dump(m, open(os.path.join(D, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"meta chapterCount=14, toc 条目: part={sum(1 for t in toc if t['type']=='part')} "
      f"chapter={sum(1 for t in toc if t['type']=='chapter')} section={sum(1 for t in toc if t['type']=='section')}")

# ---------- 5. 零丢失验证 ----------
new_paras = []
for i in range(1, 14):
    j = json.load(open(os.path.join(D, f"{i}.json"), encoding="utf-8"))
    new_paras += [b["value"] for b in j["content"] if b.get("type") == "text"]
gold_expected = [t for gi, (f, i, t) in enumerate(gold)
                 if gi not in skip and gi not in {idx[t0] for t0 in order}]
print(f"\n验证: 新库正文段={len(new_paras)} vs 黄金流应保留段={len(gold_expected)}")
print("✓ 段落流逐段一致" if new_paras == gold_expected else "✗ 段落流不一致!")

# ---------- 6. 三端同步 ----------
ra.sync_three(BID)
print("sync_three 完成 (PhiAgent book_chapters/book_detail + DP backend + DP public)")
