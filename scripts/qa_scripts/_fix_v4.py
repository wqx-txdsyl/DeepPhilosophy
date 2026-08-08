# -*- coding: utf-8 -*-
"""修复 v4 (2026-08-08): 康德判断力批判术语索引 / MEGA丛书广告 / 尼采OCR噪声 / 陀氏集标题页码
用法: python _fix_v4.py [--write]
"""
import sys, os, re, json, shutil
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"f:\program\Python\PhiAgent\backend\tools")
import rebuild_auto as ra

WRITE = "--write" in sys.argv
CH = r"f:\program\Python\PhiAgent\backend\data\book_chapters"

def norm(s):
    return re.sub(r"\s+", "", s or "")

def load_ch(D, idx):
    return json.load(open(os.path.join(D, f"{idx}.json"), encoding="utf-8"))

def save_ch(D, idx, ch):
    json.dump(ch, open(os.path.join(D, f"{idx}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

def text_vals(ch):
    return [x for x in ch["content"] if isinstance(x, dict) and x.get("type") == "text"]

def del_range(ch, lo, hi):
    """删除 text 段索引 [lo, hi] 含"""
    vals = text_vals(ch)
    assert 0 <= lo <= hi < len(vals), f"越界 lo={lo} hi={hi} n={len(vals)}"
    for x in vals[lo:hi+1]:
        ch["content"].remove(x)
    return hi - lo + 1

# ══ 1. 康德 判断力批判 #13: 删 387-411 术语索引 (25 段) ══
BID = "10e1874c2255"
D = os.path.join(CH, BID)
ch = load_ch(D, 13)
vals = text_vals(ch)
print(f"== 康德判断力批判 #13 [{ch['title']}] {len(vals)} 段")
print(f"   前段[386]: {vals[386]['value'][:40]!r}")
print(f"   索引[387]: {vals[387]['value'][:40]!r}")
print(f"   索引[411]: {vals[411]['value'][:40]!r}")
n1 = del_range(ch, 387, 411)
print(f"   删 {n1} 段 (术语索引)")
if WRITE:
    save_ch(D, 13, ch)
    ra.sync_three(BID)
    print("   sync_three 完成")

# ══ 2. MEGA 德意志意识形态 #3: 删 355 段内广告 + 356-362 ══
BID = "1085686cbd33"
D = os.path.join(CH, BID)
ch = load_ch(D, 3)
vals = text_vals(ch)
print(f"\n== MEGA德意志意识形态 #3 [{ch['title']}] {len(vals)} 段")
mark = "《当代学术棱镜译丛》"
v355 = vals[355]["value"]
assert mark in v355, f"355 段无广告标记: {v355[:40]!r}"
head, tail = v355.split(mark, 1)
print(f"   355 前保留: {head[:40]!r}…")
print(f"   355 广告: 《当代学术棱镜译丛》{tail[:30]!r}")
ch["content"][ch["content"].index(vals[355])] = {"type": "text", "value": head.rstrip()}
n2 = del_range(ch, 356, 362)
print(f"   删 {n2} 段 (丛书广告)")
if WRITE:
    save_ch(D, 3, ch)
    ra.sync_three(BID)
    print("   sync_three 完成")

# ══ 3. 尼采: #0/#2/#3/#5 删尾段 OCR 噪声 ══
BID = "00fadd7de47c"
D = os.path.join(CH, BID)
NOISE = [(0, "/.9-"), (2, "7/-"), (3, ".9.9 -"), (5, "20.00元")]
print(f"\n== 尼采 4 处 OCR 噪声")
for idx, exp in NOISE:
    ch = load_ch(D, idx)
    vals = text_vals(ch)
    last = vals[-1]["value"]
    assert norm(last) == norm(exp), f"#{idx} 尾段不符: {last!r} != {exp!r}"
    ch["content"].remove(vals[-1])
    print(f"   #{idx} [{ch['title'][:16]}] 删尾段: {last!r}")
    if WRITE:
        save_ch(D, idx, ch)
if WRITE:
    ra.sync_three(BID)
    print("   sync_three 完成")

# ══ 4. 陀氏集: #476/#477/#479/#480 标题页码 + 重复首段 ══
BID = "343df8697039"
D = os.path.join(CH, BID)
print(f"\n== 陀思妥耶夫斯基作品集 标题页码清理")
FIX = {
    476: ("前言草 429", "前言草"),
    477: ("第一部", "第一部"),
    479: ("第一章 地下室 201", "第一章 地下室"),
    480: ("第二章 湿雪纷飞 230", "第二章 湿雪纷飞"),
}
for idx, (exp_first, new_title) in FIX.items():
    ch = load_ch(D, idx)
    vals = text_vals(ch)
    first = vals[0]["value"]
    assert norm(first) == norm(exp_first), f"#{idx} 首段不符: {first!r} != {exp_first!r}"
    ch["content"].remove(vals[0])
    old_title = ch["title"]
    ch["title"] = new_title
    print(f"   #{idx} [{old_title}] → 删首段 {first[:20]!r}, 标题 → {new_title}")
    if WRITE:
        save_ch(D, idx, ch)
if WRITE:
    ra.sync_three(BID)
    print("   sync_three 完成")
print("done")
