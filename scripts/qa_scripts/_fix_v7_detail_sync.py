# -*- coding: utf-8 -*-
"""修复 v7 (2026-08-08): 两端 book_detail 字段级不一致修复
根因: sync_three 只同步 toc/chapterCount/chapterTitles/title 4 字段,
      author/tags/summary/cover 不覆盖 → DP 侧 detail 陈旧; PHI 侧 OCR
      重建时 author 写成斜杠格式, 且与神对话/恐惧与战栗 tags 等被清空。
修复:
  1. title 4 本: PHI(规范化) → DP 两侧
  2. author 6 本: 统一为 MERGE_RULES 顿号合并值 (两端)
  3. tags/summary/cover 4 本: PHI 缺的从 DP 补回, PHI 新的覆盖 DP
用法: python _fix_v7_detail_sync.py
"""
import sys, os, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PD = r"f:\program\Python\PhiAgent\backend\data\book_detail"          # PHI 源
DD = r"f:\program\Python\DeepPhilosophy\DeepPhilosophy\backend\data\book_detail"
DPUB = r"f:\program\Python\DeepPhilosophy\DeepPhilosophy\app\public\book_detail"

def load(p):
    return json.load(open(p, encoding="utf-8"))

def dump(p, d):
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ══ 1. title: PHI → DP 两侧 ══
TITLE_BIDS = ["215af36cac9f", "75efcbb151b7", "cba9d40254dc", "d036e1e712eb"]  # 奥古斯丁/莱布尼茨/苏格拉底/帕斯卡尔
for bid in TITLE_BIDS:
    a = load(os.path.join(PD, f"{bid}.json"))
    for dst in (DD, DPUB):
        p = os.path.join(dst, f"{bid}.json")
        b = load(p)
        if b.get("title") != a["title"]:
            b["title"] = a["title"]
            dump(p, b)
            print(f"title  {bid[:8]}: {b.get('title')!r} → {a['title']!r}  ({dst.split(chr(92))[-2]})")

# ══ 2. author: 统一顿号合并值 (MERGE_RULES 权威) ══
AUTHOR_FIX = {
    "1085686cbd33": "卡尔·马克思、弗里德里希·恩格斯",  # MEGA 德意志意识形态
    "26f5e0df6d76": "扬布里柯、波爱修斯",              # 哲学规劝录 哲学的慰藉
    "420f076ba733": "卡尔·马克思、弗里德里希·恩格斯",  # 共产党宣言
    "7729ccdecb0f": "卡尔·马克思、弗里德里希·恩格斯",  # 马克思恩格斯文集
    "ae97dec227b6": "卡尔·马克思、弗里德里希·恩格斯",  # 德意志意识形态（节选本）
    "c309f9dd4214": "卡尔·马克思、弗里德里希·恩格斯",  # 神圣家族
}
for bid, author in AUTHOR_FIX.items():
    for dst in (PD, DD, DPUB):
        p = os.path.join(dst, f"{bid}.json")
        d = load(p)
        if d.get("author") != author:
            old = d.get("author")
            d["author"] = author
            dump(p, d)
            print(f"author {bid[:8]}: {old!r} → {author!r}  ({dst.split(chr(92))[-2]})")

# ══ 3. tags/summary/cover: 取较全的值, 两端统一 ══
# 7657ef4a 与神对话 / f1e06cec 恐惧与战栗: PHI 被清空, 从 DP 补回
# bedc9c78 尼采文集: PHI 为重建新值, 覆盖 DP
for bid in ["7657ef4a2cd3", "f1e06cece874", "bedc9c78dfdf"]:
    pa, da = load(os.path.join(PD, f"{bid}.json")), load(os.path.join(DD, f"{bid}.json"))
    winner = {}
    for f in ("tags", "summary", "cover"):
        pv, dv = pa.get(f), da.get(f)
        if pv and not dv:
            winner[f] = pv          # PHI 有 DP 无 → 用 PHI
        elif dv and not pv:
            winner[f] = dv          # DP 有 PHI 无 → 用 DP 补回
        elif pv == dv:
            winner[f] = pv
        else:
            winner[f] = pv          # 都有但不同 → PHI (重建新值) 为准
        print(f"  {f:7s} {bid[:8]}: PHI={str(pv)[:24]!r:26s} DP={str(dv)[:24]!r:26s} → {str(winner.get(f))[:24]!r}")
    for dst, d in ((PD, pa), (DD, da), (DPUB, load(os.path.join(DPUB, f"{bid}.json")))):
        changed = False
        for f in winner:
            if d.get(f) != winner[f]:
                d[f] = winner[f]
                changed = True
        if changed:
            dump(os.path.join(dst, f"{bid}.json"), d)
            print(f"  写入 {dst.split(chr(92))[-2]}")

print("\ndone")
