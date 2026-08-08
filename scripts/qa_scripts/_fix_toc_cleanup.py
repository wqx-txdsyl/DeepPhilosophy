# -*- coding: utf-8 -*-
"""全库内容级校验修复 (2026-08-08)
A. 目录/壳章删除 + index 重排 (他者的消失/在绝望之巅/织梦人/康德三大批判合集/中国哲学十九讲)
B. 章末混入下一章标题清理 (论正义 23处 + 卡拉马佐夫兄弟 12处); 论正义另删首段重复标题
用法: python _fix_toc_cleanup.py [--write]
"""
import sys, os, re, json, shutil
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"f:\program\Python\PhiAgent\backend\tools")
import rebuild_auto as ra

WRITE = "--write" in sys.argv
CH = ra.CH

def norm(s):
    return re.sub(r"\s+", "", s)

# ── A. 目录/壳章删除: (bid, [要删的 index], {old_index: 修正标题}) ──
DROP = [
    ("0a9a96184411", [1], {}),   # 他者的消失: 目录
    ("0ed8c0c49e2f", [1], {}),   # 在绝望之巅: 目录
    ("0f00c3a90243", [1], {13: "第五章 上帝"}),  # 织梦人: 目录; 修正"第五 章上帝"
    ("10e1874c2255", [0, 10, 11], {}),  # 康德: 版本信息与目录/章题/目录
    ("167cb7f3a631", [1], {}),   # 中国哲学十九讲: 目录
]

# ── B. 章末标题行清理: (bid,) 通用规则 ──
EDGE = ["102319ab18e7", "6d9730f1f8b1"]  # 论正义 / 卡拉马佐夫兄弟(bid 待查)
EDGE = ["102319ab18e7", "卡拉马佐夫"]

# 先解析卡拉马佐夫 bid
BOOKS = json.load(open(r"f:\program\Python\PhiAgent\app\public\books.json", encoding="utf-8"))
def bid_of(title):
    return next(b["id"] for b in BOOKS if b["title"] == title)

KARAMAZOV = bid_of("卡拉马佐夫兄弟")
EDGE = ["102319ab18e7", KARAMAZOV]
print("卡拉马佐夫兄弟 bid:", KARAMAZOV)

# ══ A ══
for bid, drop_idxs, retitle in DROP:
    D = os.path.join(CH, bid)
    mf = os.path.join(D, "meta.json")
    meta = json.load(open(mf, encoding="utf-8"))
    toc = meta["toc"]
    if isinstance(toc, dict):
        toc = [t for i, t in sorted(toc.items(), key=lambda kv: int(kv[0]))]
    meta["toc"] = toc
    title = meta.get("title", "?")
    print(f"== A. {title} (bid={bid}) 删章 {drop_idxs}")
    keep = [t for t in toc if t["index"] not in drop_idxs]
    print(f"   {len(toc)} -> {len(keep)} 章")
    if WRITE:
        BAK = os.path.join(CH, "_rebuild_bak", f"{bid}_v2_dirtoc")
        os.makedirs(BAK, exist_ok=True)
        if not os.listdir(BAK):
            for f in sorted(os.listdir(D)):
                shutil.copy2(os.path.join(D, f), os.path.join(BAK, f))
        for new_i, t in enumerate(keep):
            old_i = t["index"]
            ch = json.load(open(os.path.join(D, f"{old_i}.json"), encoding="utf-8"))
            ch["index"] = new_i
            if old_i in retitle:
                ch["title"] = retitle[old_i]
            t["title"] = ch["title"]
            t["index"] = new_i
            if new_i != old_i:
                json.dump(ch, open(os.path.join(D, f"{new_i}.json"), "w", encoding="utf-8"),
                          ensure_ascii=False, indent=1)
                os.remove(os.path.join(D, f"{old_i}.json"))
            else:
                json.dump(ch, open(os.path.join(D, f"{new_i}.json"), "w", encoding="utf-8"),
                          ensure_ascii=False, indent=1)
        meta["chapterCount"] = len(keep)
        meta["chapterTitles"] = [t["title"] for t in keep]
        json.dump(meta, open(mf, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"   写入完成, 调用 sync_three")
        ra.sync_three(bid)
        print(f"   sync_three 完成")

# ══ B ══
for bid in EDGE:
    D = os.path.join(CH, bid)
    mf = os.path.join(D, "meta.json")
    meta = json.load(open(mf, encoding="utf-8"))
    toc = meta["toc"]
    if isinstance(toc, dict):
        toc = [t for i, t in sorted(toc.items(), key=lambda kv: int(kv[0]))]
    meta["toc"] = toc
    title = meta.get("title", "?")
    print(f"== B. {title} (bid={bid}) 章末标题行清理")
    if not WRITE:
        continue
    # 下一章标题映射: 每章的后一章标题 (按 toc 顺序)
    next_title = {}
    for i, t in enumerate(toc):
        if i + 1 < len(toc):
            next_title[t["index"]] = toc[i + 1].get("title", "")
    changed = 0
    for t in toc:
        idx = t["index"]
        fp = os.path.join(D, f"{idx}.json")
        ch = json.load(open(fp, encoding="utf-8"))
        content = ch["content"]
        vals = [x for x in content if isinstance(x, dict) and x.get("type") == "text"]
        if not vals:
            continue
        # 尾段 == 下一章标题 (去空白) → 删
        nt = next_title.get(idx, "")
        last = vals[-1].get("value", "")
        if nt and norm(last) == norm(nt):
            content.remove(vals[-1])
            changed += 1
            print(f"   章#{idx} [{ch['title'][:18]}] 删尾段(下章标题): {last[:30]!r}")
        # 首段 == 本章标题 (去空白) → 删
        first = vals[0].get("value", "")
        if norm(first) == norm(ch["title"]) and len(vals) > 1:
            content.remove(vals[0])
            changed += 1
            print(f"   章#{idx} [{ch['title'][:18]}] 删首段(重复标题)")
        if changed:
            json.dump(ch, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if changed:
        ra.sync_three(bid)
        print(f"   清理 {changed} 处, sync_three 完成")
    else:
        print(f"   无改动")
