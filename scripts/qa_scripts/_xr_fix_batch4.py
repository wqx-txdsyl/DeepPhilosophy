# -*- coding: utf-8 -*-
"""第四批修复（一次性）
1. 康德实践理性批判句读 aacc867ec43c ✗D：i2-14 标题去"第一章纯粹实践理性的诸原理"前缀
   + 页码残留（81./S1./83./4./86./6./S8./8.），定理号规范化，全部降 section/level 2
2. 第一哲学沉思集 88b56fb4da52 ✗D：7.json（含全部六个沉思 133 段）按六沉思拆 6 文件；
   原 8-15.json 后移为 13-20.json；toc i7 拆 6 条，i8"第二组沉思"修正为"第二组反驳"
3. 公共领域的新结构转型 0d31135f957d ✗D：0.json（学术委员会名单/版权页）并入 1.json 头部；
   第一/二/三部分改 part
4. 导读福柯 60eed962806b ✗D：0.json 删封面/目录 OCR 段（7 段 → 2-6 共 5 段），
   标题改"代译序"，并入 1/2.json（同一篇序被切三块）；代泽序错字随并入消除
同步 PhiAgent + DP。"""
import json, re, shutil, os

def load(p):
    return json.load(open(p, encoding="utf-8"))

def dump(p, data):
    json.dump(data, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)

SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters"
DST = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters"

# ────────── 1. 康德实践理性批判句读 ──────────
BID = "aacc867ec43c"
s = os.path.join(SRC, BID)

def clean_kant(t):
    t = t.replace("第一章纯粹实践理性的诸原理", "")
    t = re.sub(r"^\s*S?\d+[.．、]", "", t)          # 页码/段号残留
    t = t.replace("定理1", "定理Ⅰ").replace("定理I", "定理Ⅰ")
    t = t.replace("定理II", "定理Ⅱ").replace("定理V", "定理Ⅴ").replace("定理IV", "定理Ⅳ")
    t = re.sub(r"\s*\.\s*注释", "注释", t)          # 定理1.注释 → 定理Ⅰ注释
    t = re.sub(r"[\d.．、\s]+$", "", t)               # 尾部 1./I./空白
    return t.strip()

m = load(f"{s}/meta.json")
n_sec = 0
for t in m["toc"]:
    if t.get("index", 0) >= 2:
        new = clean_kant(t.get("title", ""))
        t["title"] = new
        t["type"] = "section"; t["level"] = 2
        n_sec += 1
        # 同步文件 title
        fp = f"{s}/{t['index']}.json"
        if os.path.exists(fp):
            d = load(fp); d["title"] = new; dump(fp, d)
m["chapterCount"] = sum(1 for t in m["toc"] if t.get("type") not in ("part", "section"))
dump(f"{s}/meta.json", m)
print(f"✓ 康德句读: {n_sec} 条降 section, cc={m['chapterCount']}")
print("  toc:", [t["title"] for t in m["toc"]])

# ────────── 2. 第一哲学沉思集 ──────────
BID = "88b56fb4da52"
s = os.path.join(SRC, BID)
d7 = load(f"{s}/7.json")
c = d7["content"]
marks = [(1, "第一个沉思 论可以引起怀疑的事物"),
         (14, "第二个沉思 论人的精神的本质以及精神比物质更容易被认识"),
         (31, "第三个沉思 论上帝和上帝的存在"),
         (72, "第四个沉思 论正确和错误"),
         (90, "第五个沉思 论物质事物的本质并再一次论上帝和上帝的存在"),
         (107, "第六个沉思 论物质事物的存在和论人的灵魂和肉体的真正区别")]
bounds = [x for x, _ in marks] + [len(c)]
assert c[0]["value"].startswith("论上帝的存在"), "段0应为书名页标题行"
for i in range(1, len(c)):
    if i in bounds:
        assert c[i]["value"].startswith(("第",)), f"边界 {i} 应为沉思标题"
assert c[-1]["value"].startswith("当然，这种考虑对我有很大好处"), "尾段应为第六沉思结尾"
# 拆分：段 0 删（书名页）；边界段作标题
for k, (start, title) in enumerate(marks):
    end = bounds[k + 1]
    body = [p for p in c[start + 1:end]]
    data = {"title": title, "content": body}
    dump(f"{s}/{7 + k}.json", data)
    print(f"  沉思{k+1}: {title[:18]} 段数={len(body)}")
# 原 8-15.json → 13-20.json
for i in range(15, 7, -1):
    os.rename(f"{s}/{i}.json", f"{s}/{i + 6}.json")
m = load(f"{s}/meta.json")
new_toc = []
for t in m["toc"]:
    idx = t.get("index", 0)
    if idx < 7:
        new_toc.append(t)
    elif idx == 7:
        for k, (_, title) in enumerate(marks):
            new_toc.append({"type": "chapter", "index": 7 + k, "title": title})
    else:
        t["index"] = idx + 6
        if idx == 8:
            t["title"] = "对第二组反驳的答辩（节录）"
        new_toc.append(t)
m["toc"] = new_toc
m["chapterCount"] = len(new_toc)
dump(f"{s}/meta.json", m)
print(f"✓ 沉思集: 六沉思拆 6 章, cc={m['chapterCount']}")

# ────────── 3. 公共领域的新结构转型 ──────────
BID = "0d31135f957d"
s = os.path.join(SRC, BID)
d0 = load(f"{s}/0.json"); d1 = load(f"{s}/1.json")
d1["content"] = d0["content"] + d1["content"]   # 名单并入前言头部（原书页序）
dump(f"{s}/1.json", d1)
os.remove(f"{s}/0.json")
m = load(f"{s}/meta.json")
toc = [t for t in m["toc"] if t.get("index") != 0]
for j, t in enumerate(toc):
    t["index"] = j
    if t.get("title", "").startswith(("第一部分", "第二部分", "第三部分")):
        t["type"] = "part"; t["level"] = 0
m["toc"] = toc
m["chapterCount"] = sum(1 for t in toc if t.get("type") not in ("part", "section"))
dump(f"{s}/meta.json", m)
print(f"✓ 公共领域: 名单并入前言, {sum(1 for t in toc if t.get('type')=='part')} 个 part, cc={m['chapterCount']}")

# ────────── 4. 导读福柯 ──────────
BID = "60eed962806b"
s = os.path.join(SRC, BID)
d0 = load(f"{s}/0.json"); d1 = load(f"{s}/1.json"); d2 = load(f"{s}/2.json")
d0["title"] = "代译序"
d0["content"] = d0["content"][2:] + d1["content"] + d2["content"]  # 删封面/目录段，合并三块
dump(f"{s}/0.json", d0)
os.remove(f"{s}/1.json"); os.remove(f"{s}/2.json")
for i in range(11, 2, -1):
    os.rename(f"{s}/{i}.json", f"{s}/{i - 2}.json")
m = load(f"{s}/meta.json")
toc = []
toc.append({"type": "chapter", "index": 0, "title": "代译序"})
for t in m["toc"]:
    if t.get("index", 0) >= 3:
        t["index"] -= 2
        toc.append(t)
m["toc"] = toc
m["chapterCount"] = len(toc)
dump(f"{s}/meta.json", m)
print(f"✓ 导读福柯: 序三块合一, 删封面章, cc={m['chapterCount']}")

# ────────── 同步 DP ──────────
for bid in ["aacc867ec43c", "88b56fb4da52", "0d31135f957d", "60eed962806b"]:
    sd = os.path.join(DST, bid)
    shutil.rmtree(sd, ignore_errors=True)
    shutil.copytree(os.path.join(SRC, bid), sd)
    print(f"✓ 同步 DP: {bid}")
