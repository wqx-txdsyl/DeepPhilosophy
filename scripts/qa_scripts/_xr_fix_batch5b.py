# -*- coding: utf-8 -*-
"""第五批补丁（一次性）：接 batch5 断点（君主论已完成，跳过）
2. 大问题 2cbf90eb6f69：绪论 9 节合并 + 12-24 → 4-16 重命名
3. 哲学与人生 a8f6e375ccef：节标题裁剪 + 补（六）
同步 PhiAgent + DP。"""
import json, re, shutil, os

def load(p):
    return json.load(open(p, encoding="utf-8"))

def dump(p, data):
    json.dump(data, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)

SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters"
DST = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters"

# ────────── 2. 大问题 ──────────
BID = "2cbf90eb6f69"
s = os.path.join(SRC, BID)
if load(f"{s}/1.json")["title"] == "绪论":
    print("✓ 大问题: 绪论已合并，跳过")
else:
    m = load(f"{s}/meta.json")
    d1 = load(f"{s}/1.json")
    d1["title"] = "绪论"
    for i in range(4, 12):
        di = load(f"{s}/{i}.json")
        d1["content"].append({"type": "text", "value": f"◆ {di['title']}"})
        d1["content"].extend(di["content"])
        os.remove(f"{s}/{i}.json")
    dump(f"{s}/1.json", d1)
    for i in range(12, 25):       # 升序：12→4 腾位
        os.rename(f"{s}/{i}.json", f"{s}/{i - 8}.json")
    toc = []
    for t in m["toc"]:
        idx = t.get("index", 0)
        if idx == 1:
            t["title"] = "绪论"
            toc.append(t)
        elif idx in (2, 3):
            t["index"] = idx - 1
            toc.append(t)
        elif 4 <= idx <= 11:
            pass
        else:
            t["index"] = idx - 8
            toc.append(t)
    m["toc"] = toc
    m["chapterCount"] = len(toc)
    dump(f"{s}/meta.json", m)
    print(f"✓ 大问题: 绪论合并, cc={m['chapterCount']}")

# ────────── 3. 哲学与人生 ──────────
BID = "a8f6e375ccef"
s = os.path.join(SRC, BID)
SEC_FIX = {
    3: ("（二）《辞海》对哲学的解释", "哲学是人们对于整个世界"),
    4: ("（三）哲学是系统化、理论化的世界观", "哲学的这一定义"),
    5: ("（四）哲学是对自然科学、社会科学和思维科学的概括和总结", "哲学与具体科学"),
    6: ("（五）哲学是世界观与方法论的统一", "任何哲学既是世界观"),
    7: ("（六）马克思主义哲学", "它是辩证唯物主义和历史唯物主义"),
    10: ("（八）哲学即逻辑", "罗素、奎因"),
    19: ("（十三）周国平认为，哲学有四种不同的存在形式", "一是作为形而上学的沉思"),
    24: ("（十六）儒家以仁为核心的哲学思想", "作为我国传统文化中"),
    33: ("（二十一）兵家的军事哲学思想", "“军事哲学”是关于军事斗争"),
    38: ("（二十四）哲学：定位宇宙、安排人生", "在实践上，就是教人学习"),
}
d0 = load(f"{s}/0.json")
# 按序号匹配（（六）兼容"（六、"）：以序号开头且含正文尾巴的段裁剪
fixed = 0
for title, body_start in SEC_FIX.values():
    num = re.match(r"^（([一二三四五六七八九十]+)", title).group(1)
    for c in d0["content"]:
        v = c.get("value", "")
        # 序号后必须是 ）、 之一（排除（二十一）误匹配（二））
        if re.match(rf"^（{num}[）、]", v) and v != title and body_start in v:
            i = v.find(body_start)
            assert i > 0, f"未找到正文起点: {v[:30]}"
            c["value"] = title
            idx = d0["content"].index(c)
            d0["content"].insert(idx + 1, {"type": "text", "value": v[i:]})
            fixed += 1
            break
dump(f"{s}/0.json", d0)
print(f"  0.json 裁剪 {fixed} 段")

m = load(f"{s}/meta.json")
def secs_of(f):
    d = load(f"{s}/{f}.json")
    return [c["value"] for c in d["content"]
            if re.match(r"^（[一二三四五六七八九十]+[）、]", c.get("value", ""))]
s0, s1, s2 = secs_of("0"), secs_of("1"), secs_of("2")
print("  0.json 节:", len(s0), "| 1.json:", len(s1), "| 2.json:", len(s2))
assert len(s0) == 24, f"0.json 应为 24 节, 实为 {len(s0)}"
toc = []
for idx, title in [(0, "一、哲学是什么？认识哲学。"),
                   (1, "二、人是什么？认识你自己。"),
                   (2, "三、哲学引领你通往幸福快乐的人生。")]:
    toc.append({"type": "chapter", "index": idx, "title": title})
    for sv in [s0, s1, s2][idx]:
        toc.append({"type": "section", "index": idx, "level": 2, "title": sv})
m["toc"] = toc
dump(f"{s}/meta.json", m)
print(f"✓ 哲学与人生: {len(s0)+len(s1)+len(s2)} 节标题重建（补（六））")

# ────────── 同步 DP ──────────
for bid in ["2cbf90eb6f69", "a8f6e375ccef"]:
    sd = os.path.join(DST, bid)
    shutil.rmtree(sd, ignore_errors=True)
    shutil.copytree(os.path.join(SRC, bid), sd)
    print(f"✓ 同步 DP: {bid}")
