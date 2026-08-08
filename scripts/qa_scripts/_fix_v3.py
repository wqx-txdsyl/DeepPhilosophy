# -*- coding: utf-8 -*-
"""三本修复 (2026-08-08): 法哲学原理 3篇part / 叔本华 2部part / 新教伦理残行清理
用法: python _fix_v3.py [--write]
"""
import sys, os, re, json, shutil
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"f:\program\Python\PhiAgent\backend\tools")
import rebuild_auto as ra

WRITE = "--write" in sys.argv
CH = r"f:\program\Python\PhiAgent\backend\data\book_chapters"

def load(bid):
    D = os.path.join(CH, bid)
    mf = os.path.join(D, "meta.json")
    meta = json.load(open(mf, encoding="utf-8"))
    toc = meta["toc"]
    if isinstance(toc, dict):
        toc = [t for i, t in sorted(toc.items(), key=lambda kv: int(kv[0]))]
    meta["toc"] = toc
    return D, mf, meta

def strip_tail(D, idx, expect, tag):
    """删除章尾段, expect 为期望的残留文本(用于防误删)"""
    fp = os.path.join(D, f"{idx}.json")
    ch = json.load(open(fp, encoding="utf-8"))
    vals = [x for x in ch["content"] if isinstance(x, dict) and x.get("type") == "text"]
    last = vals[-1]["value"] if vals else ""
    nl = re.sub(r"\s+", "", last)
    ne = re.sub(r"\s+", "", expect)
    if nl != ne:
        print(f"  ✗ #{idx} [{ch['title'][:14]}] 尾段不符: {last[:30]!r} (期望 {expect!r})")
        return False
    ch["content"].remove(vals[-1])
    json.dump(ch, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"  #{idx} [{ch['title'][:14]}] 删尾段: {expect[:24]!r} ({tag})")
    return True

# ══ 1. 法哲学原理: 3 篇 part ══
BID = "17c85f942c78"
D, mf, meta = load(BID)
print(f"== 法哲学原理 part 重建")
PARTS = [("第一篇 抽象法", 4, 12), ("第二篇 道德", 13, 17), ("第三篇 伦理", 18, 38)]
if WRITE:
    BAK = os.path.join(CH, "_rebuild_bak", f"{BID}_v5_parts")
    os.makedirs(BAK, exist_ok=True)
    if not os.listdir(BAK):
        for f in sorted(os.listdir(D)):
            shutil.copy2(os.path.join(D, f), os.path.join(BAK, f))
    new_toc = []
    for t in meta["toc"]:
        for pt, lo, hi in PARTS:
            if t["index"] == lo:
                new_toc.append({"type": "part", "title": pt, "index": lo, "level": 0})
        new_toc.append({"type": "chapter", "title": t["title"], "index": t["index"], "level": 1})
    meta["toc"] = new_toc
    json.dump(meta, open(mf, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"  toc {len(meta['toc'])} 条 (3 part + {len(meta['toc'])-3} chapter)")
    ra.sync_three(BID)
    print("  sync_three 完成")

# ══ 2. 叔本华: 删残留 + 2 部 part ══
BID = "22a3677221e6"
D, mf, meta = load(BID)
print(f"== 叔本华及哲学的狂野年代")
if WRITE:
    BAK = os.path.join(CH, "_rebuild_bak", f"{BID}_v5_parts")
    os.makedirs(BAK, exist_ok=True)
    if not os.listdir(BAK):
        for f in sorted(os.listdir(D)):
            shutil.copy2(os.path.join(D, f), os.path.join(BAK, f))
    strip_tail(D, 0, "第一部", "第一部标题行")
    PARTS = [("第一部", 1, 11), ("第二部", 12, 24)]
    new_toc = []
    for t in meta["toc"]:
        for pt, lo, hi in PARTS:
            if t["index"] == lo:
                new_toc.append({"type": "part", "title": pt, "index": lo, "level": 0})
        new_toc.append({"type": "chapter", "title": t["title"], "index": t["index"], "level": 1})
    meta["toc"] = new_toc
    json.dump(meta, open(mf, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"  toc {len(meta['toc'])} 条 (2 part + {len(meta['toc'])-2} chapter)")
    ra.sync_three(BID)
    print("  sync_three 完成")

# ══ 3. 新教伦理: 删 2 处残留 ══
BID = "278a154690ce"
D, mf, meta = load(BID)
print(f"== 新教伦理与资本主义精神")
if WRITE:
    strip_tail(D, 9, "第一部分 问题", "部标题行")
    strip_tail(D, 18, "附录", "附录标题行")
    ra.sync_three(BID)
    print("  sync_three 完成")
print("done")
