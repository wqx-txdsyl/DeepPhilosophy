# -*- coding: utf-8 -*-
"""复核: 34 段未命中 -> 去空白/标点归一化后再匹配, 找出真正差异"""
import sys, re, json, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BID = "9e4f98733f0b"
D = os.path.join(r"f:\program\Python\PhiAgent\backend\data\book_chapters", BID)
BAK = r"f:\program\Python\PhiAgent\backend\data\_rebuild_bak" + "\\" + f"{BID}_old11ch"

def load_paras(base, n):
    out = []
    for i in range(n):
        j = json.load(open(os.path.join(base, f"{i}.json"), encoding="utf-8"))
        for b in j["content"]:
            if b.get("type") == "text":
                out.append(b["value"])
    return out

old = load_paras(BAK, 11)
new = load_paras(D, 12)
newset = set(new)
def norm_ws(t):
    return re.sub(r"\s+", "", t)

new_nws = {norm_ws(t): t for t in new}

TITLES = {"如何阅读本书", "导读", "关于附注的说明", "致辞：献给日内瓦共和国", "序",
          "本论", "第一部分", "第二部分", "注释 卢梭注于讲稿完成后", "卢梭致菲洛普利的信",
          "卢梭生平大事年表"}
def is_junk(s):
    if s in TITLES: return True
    if re.match(r"^\[卢梭注\d+\]\s*[；;]?\s*", s): return True
    if re.match(r"^\[\d+\][、,]?\s*[；;，]?", s): return True
    return False

miss = []
for s in old:
    if is_junk(s): continue
    if s in newset: continue
    if norm_ws(s) in new_nws:
        continue   # 仅空白差异
    found = any(norm_ws(t).startswith(norm_ws(s)) for t in new)
    if not found:
        miss.append(s)

print(f"去空白归一化后仍不匹配: {len(miss)} 段")
for s in miss:
    print("\n--- 旧段:", s[:80])
    # 找最接近的新段
    cand = sorted(new, key=lambda t: len(set(norm_ws(t)) ^ set(norm_ws(s))))
    print("    最接近新段:", cand[0][:80] if cand else "无")
    # 逐字符 diff 前 40 字符
    a, b = s[:40], cand[0][:40] if cand else ""
    print("    旧:", repr(a))
    print("    新:", repr(b))
