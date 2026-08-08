# -*- coding: utf-8 -*-
"""第二批小修（一次性）
1. 王阳明全集 909e887aac01 ✗D：分册版权页 11.json 并入 10.json 尾部，toc 删除，cc 66→65
2. 西方哲学二十一讲 9aea99ccb525 ✗B：第一部分改 part；\"近世哲学的精神\"前加 part\"第二部分 近代哲学\"
3. 红书 63a3b006c9d7 ✗B：第一卷/第二卷 chapter→part（index 保留），cc 47→45
同步 PhiAgent + DP。"""
import json, shutil, os

def load(p):
    return json.load(open(p, encoding="utf-8"))

def dump(p, data):
    json.dump(data, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)

SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters"
DST = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters"

# ────────── 1. 王阳明全集 ──────────
BID = "909e887aac01"
s = os.path.join(SRC, BID)
c10 = load(f"{s}/10.json"); c11 = load(f"{s}/11.json")
c10["content"].extend(c11["content"])
dump(f"{s}/10.json", c10)
os.remove(f"{s}/11.json")
# 重命名 12+ → 11+
for i in range(12, 66):
    if os.path.exists(f"{s}/{i}.json"):
        os.rename(f"{s}/{i}.json", f"{s}/{i-1}.json")
m = load(f"{s}/meta.json")
toc = [t for t in m["toc"] if not (t.get("index") == 11 and t.get("title") == "版权页")]
for j, t in enumerate(toc):
    t["index"] = j
m["toc"] = toc
m["chapterCount"] = 65
dump(f"{s}/meta.json", m)
print(f"✓ 王阳明全集: 版权页并入书六, cc={m['chapterCount']}")

# ────────── 2. 西方哲学二十一讲 ──────────
BID = "9aea99ccb525"
s = os.path.join(SRC, BID)
m = load(f"{s}/meta.json")
toc = m["toc"]
new_toc = []
for t in toc:
    if t.get("index") == 3 and t.get("title") == "第一部分 希腊哲学史":
        t["type"] = "part"; t["level"] = 0
        new_toc.append(t)
    elif t.get("index") == 15 and t.get("title") == "近世哲学的精神":
        new_toc.append({"type": "part", "index": 15, "level": 0, "title": "第二部分 近代哲学"})
        new_toc.append(t)
    else:
        new_toc.append(t)
m["toc"] = new_toc
dump(f"{s}/meta.json", m)
print(f"✓ 西方哲学二十一讲: 第一/二部分 part 化完成")

# ────────── 3. 红书 ──────────
BID = "63a3b006c9d7"
s = os.path.join(SRC, BID)
m = load(f"{s}/meta.json")
n_part = 0
for t in m["toc"]:
    if t.get("index") in (8, 20) and t.get("title") in ("第一卷", "第二卷"):
        t["type"] = "part"; t["level"] = 0
        n_part += 1
m["chapterCount"] = len(m["toc"]) - n_part
dump(f"{s}/meta.json", m)
print(f"✓ 红书: {n_part} 个卷级改 part, cc={m['chapterCount']}")

# ────────── 同步 DP ──────────
for bid in ["909e887aac01", "9aea99ccb525", "63a3b006c9d7"]:
    sd = os.path.join(DST, bid)
    shutil.rmtree(sd, ignore_errors=True)
    shutil.copytree(os.path.join(SRC, bid), sd)
    print(f"✓ 同步 DP: {bid}")
