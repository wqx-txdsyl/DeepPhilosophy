# -*- coding: utf-8 -*-
"""卡拉马佐夫兄弟 (bid=1325746d6f46) 卷级 toc 重建 (2026-08-08)
现状: 110 章全扁平, 12 卷+尾声卷标题被挤进注释章尾段
方案: ① 删 13 处注释章尾段卷标题行 ② meta.toc 重写: 13 part(level0) + 110 chapter(level1)
用法: python _rebuild_karamazov_toc.py [--write]
"""
import sys, os, json, shutil
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"f:\program\Python\PhiAgent\backend\tools")
import rebuild_auto as ra

WRITE = "--write" in sys.argv
BID = "1325746d6f46"
CH = ra.CH
D = os.path.join(CH, BID)
mf = os.path.join(D, "meta.json")
meta = json.load(open(mf, encoding="utf-8"))
toc = meta["toc"]
assert len(toc) == 110

# 卷边界: (part 标题, 起始章 index, 结束章 index 含, 卷标题行所在的注释章 index)
VOLUMES = [
    ("第一卷　一户人家的历史", 0, 6),
    ("第二卷　不该举行的聚会", 7, 15),
    ("第三卷　酒色之徒", 16, 27),
    ("第四卷　咄咄怪事", 28, 35),
    ("第五卷　正与反", 36, 43),
    ("第六卷　俄罗斯修士", 44, 47),
    ("第七卷　阿辽沙", 48, 52),
    ("第八卷　米　嘉", 53, 61),
    ("第九卷　预　审", 62, 71),
    ("第十卷　大男孩和小男孩", 72, 79),
    ("第十一卷　伊　万", 80, 90),
    ("第十二卷　错　案", 91, 105),
    ("尾声", 106, 109),
]
# 注释章尾段 = 卷标题行 (13 处: 每卷边界注释章)
STRIP_TAIL = [0, 6, 15, 27, 35, 43, 47, 52, 61, 71, 79, 90, 105]

# ── 1. 删注释章尾段卷标题行 ──
for idx in STRIP_TAIL:
    fp = os.path.join(D, f"{idx}.json")
    ch = json.load(open(fp, encoding="utf-8"))
    vals = [x for x in ch["content"] if isinstance(x, dict) and x.get("type") == "text"]
    last = vals[-1]["value"]
    # 卷标题行特征: 第X卷/尾声 开头
    assert last.startswith(("第", "尾")), f"#{idx} 尾段异常: {last[:30]!r}"
    ch["content"].remove(vals[-1])
    print(f"#{idx} [{ch['title']}] 删尾段卷标题: {last[:24]!r}")
    if WRITE:
        json.dump(ch, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ── 2. 重写 meta.toc ──
new_toc = []
for vt, lo, hi in VOLUMES:
    new_toc.append({"type": "part", "title": vt, "index": lo, "level": 0})
    for t in toc:
        if lo <= t["index"] <= hi:
            new_toc.append({"type": "chapter", "title": t["title"], "index": t["index"], "level": 1})
print(f"新 toc: {len(new_toc)} 条 (13 part + 110 chapter), chapterCount={meta['chapterCount']}")
meta["toc"] = new_toc
if WRITE:
    BAK = os.path.join(CH, "_rebuild_bak", f"{BID}_v3_vol")
    os.makedirs(BAK, exist_ok=True)
    if not os.listdir(BAK):
        for f in sorted(os.listdir(D)):
            shutil.copy2(os.path.join(D, f), os.path.join(BAK, f))
    json.dump(meta, open(mf, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("meta.json 写入完成")
    ra.sync_three(BID)
    print("sync_three 完成")
