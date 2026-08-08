# -*- coding: utf-8 -*-
"""第四批修复补丁（batch4 后两处修正，一次性）
A. 康德句读 aacc867ec43c：罗马数字替换顺序 bug 产生的中间态标题再清理
   （定理ⅠV注释 → 定理Ⅳ注释；课题1注释 → 课题Ⅰ注释；尾部注释I → 注释）
B. 导读福柯 60eed962806b：3-11.json 重命名冲突（11→9 撞 9.json）——
   两步走：先 3-11 → t3-t11 临时名，再 t3-t11 → 1-9
同步 PhiAgent + DP。"""
import json, re, shutil, os

def load(p):
    return json.load(open(p, encoding="utf-8"))

def dump(p, data):
    json.dump(data, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)

SRC = "f:/program/Python/PhiAgent/backend/data/book_chapters"
DST = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters"

# ────────── A. 康德句读 二次清理 ──────────
BID = "aacc867ec43c"
s = os.path.join(SRC, BID)

def clean_kant2(t):
    t = t.replace("第一章纯粹实践理性的诸原理", "")
    t = re.sub(r"^\s*S?\d+[.．、]", "", t)            # 页码/段号残留
    t = t.replace("定理ⅠV", "定理Ⅳ").replace("定理IV", "定理Ⅳ")  # 中间态优先
    t = t.replace("定理V", "定理Ⅴ").replace("定理II", "定理Ⅱ")
    t = t.replace("课题1", "课题Ⅰ").replace("定理1", "定理Ⅰ")
    t = t.replace("定理I", "定理Ⅰ")
    t = re.sub(r"\s*\.\s*注释", "注释", t)
    t = re.sub(r"[I\d.．\s]+$", "", t)                 # 尾部 注释I. → 注释
    return t.strip()

m = load(f"{s}/meta.json")
for t in m["toc"]:
    if t.get("index", 0) >= 2:
        new = clean_kant2(t.get("title", ""))
        t["title"] = new
        fp = f"{s}/{t['index']}.json"
        if os.path.exists(fp):
            d = load(fp); d["title"] = new; dump(fp, d)
dump(f"{s}/meta.json", m)
print("✓ 康德句读 二次清理:")
for t in m["toc"]:
    print("  ", t.get("index"), t.get("type"), "|", t.get("title"))

# ────────── B. 导读福柯 重命名两步走 + toc ──────────
BID = "60eed962806b"
s = os.path.join(SRC, BID)
for i in range(3, 12):                       # 3-11 → t3-t11
    os.rename(f"{s}/{i}.json", f"{s}/t{i}.json")
for i in range(3, 12):                       # t3-t11 → 1-9
    os.rename(f"{s}/t{i}.json", f"{s}/{i - 2}.json")
m = load(f"{s}/meta.json")
toc = [{"type": "chapter", "index": 0, "title": "代译序"}]
for t in m["toc"]:
    if t.get("index", 0) >= 3:
        t["index"] -= 2
        toc.append(t)
m["toc"] = toc
m["chapterCount"] = len(toc)
dump(f"{s}/meta.json", m)
print(f"✓ 导读福柯: cc={m['chapterCount']}")
for t in m["toc"]:
    print("  ", t.get("index"), t.get("type"), "|", t.get("title"))

# ────────── 同步 DP ──────────
for bid in ["aacc867ec43c", "60eed962806b"]:
    sd = os.path.join(DST, bid)
    shutil.rmtree(sd, ignore_errors=True)
    shutil.copytree(os.path.join(SRC, bid), sd)
    print(f"✓ 同步 DP: {bid}")
