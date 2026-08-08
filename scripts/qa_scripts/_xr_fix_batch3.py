# -*- coding: utf-8 -*-
"""第三批修复（一次性）
1. 图斯库兰论辩集 4be7b72cf01d ✗D：①译注并入正文章尾，toc 去重；10/11 标题 OCR 修正
2. 变形记 ad61ed0fd976 ✗D：i23-25 数字前缀清理（2．判决→判决）
3. 查第格 bf1ff4a2bb68 ✗D：i23 前插 part\"小大人\"
4. 论正义 102319ab18e7 ✗D：i23 前补 chapter\"第二十四章 国家\"，第一百零一~一百零九节降 section
同步 PhiAgent + DP。"""
import json, shutil, os

def load(p):
    return json.load(open(p, encoding="utf-8"))

def dump(p, data):
    json.dump(data, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)

SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters"
DST = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters"

# ────────── 1. 图斯库兰论辩集 ──────────
BID = "4be7b72cf01d"
s = os.path.join(SRC, BID)
PAIRS = [("0.json","1.json"), ("2.json","3.json"), ("4.json","5.json"),
         ("6.json","7.json"), ("8.json","9.json")]
for main, note in PAIRS:
    d_main = load(f"{s}/{main}"); d_note = load(f"{s}/{note}")
    n0 = len(d_main["content"])
    d_main["content"].extend(d_note["content"])
    dump(f"{s}/{main}", d_main)
    os.remove(f"{s}/{note}")
    print(f"✓ 图斯库兰 {main} += {note} ({n0}→{len(d_main['content'])}段)")
# 10/11 标题修正
d10 = load(f"{s}/10.json"); d11 = load(f"{s}/11.json")
d10["title"] = "第一部分：论修辞学（5卷）"
d11["title"] = "第三部分：哲学论著（6卷）"
dump(f"{s}/10.json", d10); dump(f"{s}/11.json", d11)
m = load(f"{s}/meta.json")
new_toc = [t for t in m["toc"] if not t.get("title", "").endswith("①")]
for t in new_toc:
    if t.get("index") == 10: t["title"] = "第一部分：论修辞学（5卷）"
    if t.get("index") == 11: t["title"] = "第三部分：哲学论著（6卷）"
    t["index"] = new_toc.index(t)
m["toc"] = new_toc
m["chapterCount"] = len(new_toc)
dump(f"{s}/meta.json", m)
print(f"✓ 图斯库兰: cc={m['chapterCount']}, toc={len(new_toc)}")

# ────────── 2. 变形记 ──────────
BID = "ad61ed0fd976"
s = os.path.join(SRC, BID)
fix = {"2．判决": "判决", "3．变形记": "变形记", "4．在流放地": "在流放地"}
for f, old, new in [("23.json","2．判决","判决"), ("24.json","3．变形记","变形记"), ("25.json","4．在流放地","在流放地")]:
    d = load(f"{s}/{f}")
    d["title"] = new
    dump(f"{s}/{f}", d)
m = load(f"{s}/meta.json")
for t in m["toc"]:
    if t.get("title") in fix:
        t["title"] = fix[t["title"]]
dump(f"{s}/meta.json", m)
print("✓ 变形记: 数字前缀已清理")

# ────────── 3. 查第格 ──────────
BID = "bf1ff4a2bb68"
s = os.path.join(SRC, BID)
m = load(f"{s}/meta.json")
toc = m["toc"]
new_toc = []
for t in toc:
    if t.get("index") == 23 and "天狼星系" in t.get("title", ""):
        new_toc.append({"type": "part", "index": 23, "level": 0, "title": "小大人"})
    new_toc.append(t)
m["toc"] = new_toc
dump(f"{s}/meta.json", m)
print("✓ 查第格: 小大人 part 已插入")

# ────────── 4. 论正义 ──────────
BID = "102319ab18e7"
s = os.path.join(SRC, BID)
m = load(f"{s}/meta.json")
toc = m["toc"]
new_toc = []
for t in toc:
    if t.get("index") == 23 and t.get("title") == "第一百零一节":
        new_toc.append({"type": "chapter", "index": 23, "title": "第二十四章 国家"})
        t["type"] = "section"; t["level"] = 2
    new_toc.append(t)
m["toc"] = new_toc
m["chapterCount"] = sum(1 for t in new_toc if t.get("type") != "section")
dump(f"{s}/meta.json", m)
print(f"✓ 论正义: 第二十四章已补, cc={m['chapterCount']}")

# ────────── 同步 DP ──────────
for bid in ["4be7b72cf01d", "ad61ed0fd976", "bf1ff4a2bb68", "102319ab18e7"]:
    sd = os.path.join(DST, bid)
    shutil.rmtree(sd, ignore_errors=True)
    shutil.copytree(os.path.join(SRC, bid), sd)
    print(f"✓ 同步 DP: {bid}")
