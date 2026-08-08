# -*- coding: utf-8 -*-
"""全库修复 v2 (2026-08-08) — 目录章删除 + 章末标题行通用清理
A. 目录章删除 (15 本): 删除标题含'目录/目次'的章, index 重排
B. 章末标题行清理: 尾段 norm == toc 任一 chapter 标题 norm → 删 (法哲学原理/道德情操论/康德著作集/叔本华/新教伦理/哲学的底色)
用法: python _fix_v2.py [--write]
"""
import sys, os, re, json, shutil
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"f:\program\Python\PhiAgent\backend\tools")
import rebuild_auto as ra

WRITE = "--write" in sys.argv
CH = r"f:\program\Python\PhiAgent\backend\data\book_chapters"  # 绝对路径, 杜绝歧义

def norm(s):
    return re.sub(r"\s+", "", s or "")

def load_bid(bid):
    D = os.path.join(CH, bid)
    mf = os.path.join(D, "meta.json")
    meta = json.load(open(mf, encoding="utf-8"))
    toc = meta["toc"]
    if isinstance(toc, dict):
        toc = [t for i, t in sorted(toc.items(), key=lambda kv: int(kv[0]))]
    meta["toc"] = toc
    return D, mf, meta

def write_chapter(D, idx, ch):
    json.dump(ch, open(os.path.join(D, f"{idx}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

# ══ A. 目录章删除 ══
DROP = [
    ("哲学的底色：人类永恒追求的六大哲学主题", None),
    ("沙发上的哲学家", None),
    ("美学理论", None),
    ("周易", None),
    ("加缪全集（散文卷Ⅰ）", None),
    ("自我与本我", None),
    ("鬼谷子", None),
    ("道德情操论", None),
    ("和狗狗的十二次哲学漫步", None),
    ("三十六计", None),
    ("新教伦理与资本主义精神", None),
    ("单向度的人", None),
    ("康德著作集", None),
    ("生命的意义", None),
    ("中国哲学简史", None),
]
BOOKS = json.load(open(r"f:\program\Python\PhiAgent\app\public\books.json", encoding="utf-8"))
def bid_of(title):
    return next(b["id"] for b in BOOKS if b["title"] == title)

print("═══ A. 目录章删除 ═══")
for name, _ in DROP:
    bid = bid_of(name)
    D, mf, meta = load_bid(bid)
    drop = [t for t in meta["toc"] if re.search(r"目录|目次|章题", t.get("title", ""))]
    if not drop:
        print(f"✗ {name}: 无目录章")
        continue
    drop_idx = {t["index"] for t in drop}
    keep = [t for t in meta["toc"] if t["index"] not in drop_idx]
    print(f"== {name} (bid={bid}) 删 {len(drop)} 章: {[t['title'][:14] for t in drop]}")
    if WRITE:
        BAK = os.path.join(CH, "_rebuild_bak", f"{bid}_v4_dirtoc")
        os.makedirs(BAK, exist_ok=True)
        if not os.listdir(BAK):
            for f in sorted(os.listdir(D)):
                shutil.copy2(os.path.join(D, f), os.path.join(BAK, f))
        for new_i, t in enumerate(keep):
            old_i = t["index"]
            ch = json.load(open(os.path.join(D, f"{old_i}.json"), encoding="utf-8"))
            ch["index"] = new_i
            t["title"] = ch["title"]
            t["index"] = new_i
            write_chapter(D, new_i, ch)
            if new_i != old_i:
                os.remove(os.path.join(D, f"{old_i}.json"))
        meta["toc"] = keep
        meta["chapterCount"] = len(keep)
        meta["chapterTitles"] = [t["title"] for t in keep]
        json.dump(meta, open(mf, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"   {len(keep)} 章写入, sync_three...")
        ra.sync_three(bid)

# ══ B. 章末标题行清理 ══
EDGE = ["法哲学原理", "道德情操论", "康德著作集",
        "叔本华及哲学的狂野年代", "新教伦理与资本主义精神",
        "哲学的底色：人类永恒追求的六大哲学主题"]
print("\n═══ B. 章末标题行清理 ═══")
for name in EDGE:
    bid = bid_of(name)
    D, mf, meta = load_bid(bid)
    titles = {norm(t["title"]): t["title"] for t in meta["toc"]}
    n_chg = 0
    for t in meta["toc"]:
        idx = t["index"]
        fp = os.path.join(D, f"{idx}.json")
        ch = json.load(open(fp, encoding="utf-8"))
        vals = [x for x in ch["content"] if isinstance(x, dict) and x.get("type") == "text"]
        if not vals:
            continue
        last = vals[-1].get("value", "")
        nl = norm(last)
        if nl and nl in titles and nl != norm(ch["title"]):
            ch["content"].remove(vals[-1])
            n_chg += 1
            print(f"   {name[:10]} #{idx} [{ch['title'][:14]}] 删尾段: {last.strip()[:26]!r}")
            if WRITE:
                write_chapter(D, idx, ch)
    print(f"== {name} (bid={bid}) 清理 {n_chg} 处")
    if WRITE and n_chg:
        ra.sync_three(bid)
print("done")
