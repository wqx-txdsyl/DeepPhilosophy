# -*- coding: utf-8 -*-
"""第一批小修（CHKLIST 检查产物，一次性）
1. 西塞罗 2321fab7e032 ✗D：i6/i8 两条正文句误当章标题
   → 6.json 并入 5.json（第六章尾），8.json 并入 7.json（第七章尾），删除+重编号
2. 纯粹现象学通论 a3e1832a509d ✗D：i4 标题 OCR 粘连修正为"§9 区域和区域本质学"
3. 西西弗神话 c80947d011a6 ✗D：《卡利古拉》三幕前加 part 标题
同步 PhiAgent + DP。"""
import json, shutil, os

def load(p):
    return json.load(open(p, encoding="utf-8"))

def dump(p, data):
    json.dump(data, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)

SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters"
DST = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters"

# ────────── 1. 西塞罗 ──────────
BID = "2321fab7e032"
s = os.path.join(SRC, BID)
c5 = load(f"{s}/5.json"); c6 = load(f"{s}/6.json")
c7 = load(f"{s}/7.json"); c8 = load(f"{s}/8.json")
c5["content"].extend(c6["content"])
c7["content"].extend(c8["content"])
dump(f"{s}/5.json", c5)
dump(f"{s}/7.json", c7)
os.remove(f"{s}/6.json"); os.remove(f"{s}/8.json")
os.rename(f"{s}/9.json", f"{s}/8.json")
mp = f"{s}/meta.json"
m = load(mp)
m["chapterCount"] = 8
new_toc = [t for t in m["toc"] if t.get("title") not in (
    "第二章 中，对话探讨了技术方面的问题.但也一直并",
    "第二章 由对斯多葛主义有精深研究的Q.卢齐利乌")]
# 重编号
for j, t in enumerate(new_toc):
    t["index"] = j
m["toc"] = new_toc
dump(mp, m)
print(f"✓ 西塞罗: 5.json 现 {len(c5['content'])} 段, 7.json 现 {len(c7['content'])} 段, cc={m['chapterCount']}")

# ────────── 2. 纯粹现象学通论 ──────────
BID = "a3e1832a509d"
s = os.path.join(SRC, BID)
d4 = load(f"{s}/4.json")
d4["title"] = "§9 区域和区域本质学"
dump(f"{s}/4.json", d4)
m = load(f"{s}/meta.json")
for t in m["toc"]:
    if t.get("index") == 4 and "区域" in t.get("title", ""):
        t["title"] = "§9 区域和区域本质学"
        t["type"] = "section"; t["level"] = 2   # 属第一编第一章内小节
dump(f"{s}/meta.json", m)
print("✓ 纯粹现象学通论: 4.json 标题修正为 §9 区域和区域本质学")

# ────────── 3. 西西弗神话 ──────────
BID = "c80947d011a6"
s = os.path.join(SRC, BID)
m = load(f"{s}/meta.json")
toc = m["toc"]
assert any(t.get("index") == 14 and "第一幕" in t.get("title", "") for t in toc)
part = {"type": "part", "index": 13, "level": 0, "title": "卡利古拉（剧本）"}
toc = [part if t.get("index") == 13 and t.get("title") == "弗兰茨·卡夫卡作品中的希望与荒诞" else t for t in toc]
m["toc"] = toc
m["chapterCount"] = 17
dump(f"{s}/meta.json", m)
print("✓ 西西弗神话: 卡利古拉三幕前已插入 part")

# ────────── 同步 DP ──────────
for bid in ["2321fab7e032", "a3e1832a509d", "c80947d011a6"]:
    sd = os.path.join(DST, bid)
    shutil.rmtree(sd, ignore_errors=True)
    shutil.copytree(os.path.join(SRC, bid), sd)
    print(f"✓ 同步 DP: {bid}")
