# -*- coding: utf-8 -*-
"""第五批修复（一次性）
1. 君主论 2e66606c2854 ✗D：7 条截断章标题用 content[0] 续文补全并裁剪该段；
   0.json（出版说明+译者序+献辞三合一）拆三章
2. 大问题 2cbf90eb6f69 ✗D：绪论 9 节（哲学的主题~篇末问题）合并为"绪论"一章；
   致教师/致谢独立保留
3. 哲学与人生 a8f6e375ccef ✗D：9 条长句截断节标题裁剪（toc+内容段同步），补缺失（六）
同步 PhiAgent + DP。"""
import json, shutil, os

def load(p):
    return json.load(open(p, encoding="utf-8"))

def dump(p, data):
    json.dump(data, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)

SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters"
DST = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters"

# ────────── 1. 君主论 ──────────
BID = "2e66606c2854"
s = os.path.join(SRC, BID)

# 1a. 截断章标题补全（title + content[0] 裁剪）
# (文件号, 完整标题, content[0] 待删除前缀)
CH_FIX = {
    4: ("第四章　为什么亚历山大大帝所征服的大流士王国在亚历山大死后没有背叛其后继者", "服的大流士王国在亚历山大死后没有背叛其后继者"),
    5: ("第五章　对于占领前在各自法律下生活的城市或君主国应当怎样统治", "下生活的城市或君主国应当怎样统治"),
    7: ("第七章　论依靠他人的武力或者由于幸运而取得的新君主国", "于幸运而取得的新君主国"),
    17: ("第十七章　论残酷与仁慈，被人爱戴是否比被人畏惧来得好些", "戴是否比被人畏惧来得好些"),
    20: ("第二十章　堡垒以及君主们每日做的其他许多事情是有益的还是无益的", "的其他许多事情是有益的还是无益的"),
    24: ("第二十四章　意大利的君主们为什么丧失了他们的国家", "么丧失了他们的国家"),
    25: ("第二十五章　命运在人世事务上有多大力量和怎样对抗", "多大力量和怎样对抗"),
}
for idx, (title, prefix) in CH_FIX.items():
    d = load(f"{s}/{idx}.json")
    d["title"] = title
    v = d["content"][0]["value"]
    assert v.startswith(prefix), f"{idx}.json 段0 前缀不符: {v[:20]}"
    d["content"][0]["value"] = v[len(prefix):]
    dump(f"{s}/{idx}.json", d)
print(f"✓ 君主论: {len(CH_FIX)} 条截断标题补全")

# 1b. 0.json 拆三章：出版说明 / 译者序 / 献辞
d0 = load(f"{s}/0.json")
c = d0["content"]
assert c[0]["value"].startswith("我馆历来重视移译"), "段0应为出版说明"
assert "商务印书馆编辑部1985年10月" in c[1]["value"] and "译者序" in c[1]["value"]
assert c[77]["value"].startswith("尼科洛·马基雅维里上洛伦佐·梅迪奇殿下书")
# 段1 拆：落款并入 0；"译者序在历史上的地位…"为译者序正文首段
sig = "商务印书馆编辑部1985年10月"
d0["title"] = "出版说明"
d0["content"] = [c[0], {"type": "text", "value": sig}]
dump(f"{s}/0.json", d0)
# 译者序：段1 的后半 + 段2-76
v1 = c[1]["value"]
idx = v1.find("译者序")
rest = v1[idx + len("译者序"):]
sec = {"type": "text", "value": "译者序"}
trans = [{"type": "text", "value": rest}] + c[2:77]
dump(f"{s}/1.json", {"title": "译者序", "content": [sec] + trans})
# 献辞：段77 标题拆出 + 段78-81
v77 = c[77]["value"]
ded = {"type": "text", "value": "尼科洛·马基雅维里上洛伦佐·梅迪奇殿下书"}
d77 = {"type": "text", "value": v77[len("尼科洛·马基雅维里上洛伦佐·梅迪奇殿下书"):]}
dump(f"{s}/2.json", {"title": "献辞（尼科洛·马基雅维里上洛伦佐·梅迪奇殿下书）", "content": [ded, d77] + c[78:82]})
# 原 1-26 → 3-28
for i in range(26, 0, -1):
    os.rename(f"{s}/{i}.json", f"{s}/{i + 2}.json")
m = load(f"{s}/meta.json")
toc = [
    {"type": "chapter", "index": 0, "title": "出版说明"},
    {"type": "chapter", "index": 1, "title": "译者序"},
    {"type": "chapter", "index": 2, "title": "献辞（尼科洛·马基雅维里上洛伦佐·梅迪奇殿下书）"},
]
for t in m["toc"]:
    if t.get("index", 0) >= 1:
        t["index"] += 2
        if t["index"] in CH_FIX:
            t["title"] = CH_FIX[t["index"]][0]
        toc.append(t)
m["toc"] = toc
m["chapterCount"] = len(toc)
dump(f"{s}/meta.json", m)
print(f"✓ 君主论: 拆 出版说明/译者序/献辞, cc={m['chapterCount']}")

# ────────── 2. 大问题 ──────────
BID = "2cbf90eb6f69"
s = os.path.join(SRC, BID)
m = load(f"{s}/meta.json")
# i1 哲学的主题 → 绪论，并入 i4-11（避免时髦词语~篇末问题）
d1 = load(f"{s}/1.json")
d1["title"] = "绪论"
for i in range(4, 12):
    di = load(f"{s}/{i}.json")
    d1["content"].append({"type": "text", "value": f"◆ {di['title']}"})
    d1["content"].extend(di["content"])
    os.remove(f"{s}/{i}.json")
dump(f"{s}/1.json", d1)
# 12-24 → 4-16（升序：12→4 腾位，20→12 时空位成立）
for i in range(12, 25):
    os.rename(f"{s}/{i}.json", f"{s}/{i - 8}.json")
toc = []
for t in m["toc"]:
    idx = t.get("index", 0)
    if idx == 1:
        t["title"] = "绪论"
        toc.append(t)
    elif idx in (2, 3):
        t["index"] = idx - 1      # 致教师→1, 致谢→2
        toc.append(t)
    elif 4 <= idx <= 11:
        pass                      # 并入绪论
    else:
        t["index"] = idx - 8      # 12-24 → 4-16
        toc.append(t)
m["toc"] = toc
m["chapterCount"] = len(toc)
dump(f"{s}/meta.json", m)
print(f"✓ 大问题: 绪论合并, cc={m['chapterCount']}")

# ────────── 3. 哲学与人生 ──────────
BID = "a8f6e375ccef"
s = os.path.join(SRC, BID)
# (段号, 新标题, 正文起始文本)
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
for para, (title, body_start) in SEC_FIX.items():
    v = d0["content"][para]["value"]
    i = v.find(body_start)
    assert i > 0, f"段{para} 未找到正文起点: {v[:30]}"
    d0["content"][para]["value"] = title
    d0["content"].insert(para + 1, {"type": "text", "value": v[i:]})
dump(f"{s}/0.json", d0)
m = load(f"{s}/meta.json")
# 重建 toc section 顺序：以文件内容标题段顺序为准（0.json 各段序号），
# 从内容中提取（一）~（二十四），再拼接 1/2.json 的节
def secs_of(f):
    d = load(f"{s}/{f}.json")
    out = []
    for c in d["content"]:
        v = c.get("value", "")
        import re as _re
        if _re.match(r"^（[一二三四五六七八九十]+）", v):
            out.append(v)
    return out
s0 = secs_of("0.json")
s1 = secs_of("1.json")
s2 = secs_of("2.json")
print("  0.json 节:", len(s0), "| 1.json:", len(s1), "| 2.json:", len(s2))
assert len(s0) == 24, f"0.json 应为 24 节, 实为 {len(s0)}"
toc = []
for idx, title in [(0, "一、哲学是什么？认识哲学。"), (1, "二、人是什么？认识你自己。"), (2, "三、哲学引领你通往幸福快乐的人生。")]:
    toc.append({"type": "chapter", "index": idx, "title": title})
    for sv in [s0, s1, s2][idx]:
        toc.append({"type": "section", "index": idx, "level": 2, "title": sv})
m["toc"] = toc
dump(f"{s}/meta.json", m)
print(f"✓ 哲学与人生: {len(s0)+len(s1)+len(s2)} 节标题重建（补（六））")

# ────────── 同步 DP ──────────
for bid in ["2e66606c2854", "2cbf90eb6f69", "a8f6e375ccef"]:
    sd = os.path.join(DST, bid)
    shutil.rmtree(sd, ignore_errors=True)
    shutil.copytree(os.path.join(SRC, bid), sd)
    print(f"✓ 同步 DP: {bid}")
