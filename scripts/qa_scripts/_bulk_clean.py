# -*- coding: utf-8 -*-
"""全库标题行批量清理 (2026-08-08):
  H: 章首重复标题 (首段 norm == 章标题 norm → 删首段)
  T: 章尾标题污染 (尾段 norm == toc 任一 chapter 标题 norm, != 本章 → 删尾段)
跳过 OCR 重建队列书 (主 ckpt 中的 17 本) 与存在与虚无
用法: python _bulk_clean.py [--write]
"""
import sys, os, re, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"f:\program\Python\PhiAgent\backend\tools")
import rebuild_auto as ra

WRITE = "--write" in sys.argv
CH = r"f:\program\Python\PhiAgent\backend\data\book_chapters"
BOOKS = json.load(open(r"f:\program\Python\PhiAgent\app\public\books.json", encoding="utf-8"))
names = {b["id"]: b["title"] for b in BOOKS}

# OCR 重建队列书标题 (后台任务正在写, 跳过)
SKIP_TITLES = {
    "道家与道教思想简史", "西利斯", "尼各马可伦理学[注释导读本]", "形而上学",
    "自然与快乐", "判断力批判", "康德实践理性批判句读", "康德三大批判合集",
    "纯粹现象学通论", "政治学", "悲剧的诞生", "恐惧与战栗", "擬仿物與擬像",
    "读《资本论》", "美学中的不满", "纯粹理性批判", "西塞罗全集·修辞学卷",
}

def norm(s):
    return re.sub(r"\s+", "", s or "")

ndir = sorted(d for d in os.listdir(CH) if os.path.isdir(os.path.join(CH, d)) and not d.startswith("_"))
n_head_b, n_tail_b, n_head, n_tail = 0, 0, 0, 0
for bid in ndir:
    if bid == "274c59617693":
        continue
    name = names.get(bid, bid)
    if name in SKIP_TITLES:
        print(f"skip OCR中: {name[:20]}")
        continue
    D = os.path.join(CH, bid)
    mf = os.path.join(D, "meta.json")
    meta = json.load(open(mf, encoding="utf-8"))
    toc = meta["toc"]
    if isinstance(toc, dict):
        toc = [t for i, t in sorted(toc.items(), key=lambda kv: int(kv[0]))]
    if not toc or not isinstance(toc[0], dict):
        continue
    all_titles = {norm(t["title"]): t["title"] for t in toc if t.get("type") == "chapter"}
    changed = False
    for t in toc:
        if t.get("type") != "chapter":
            continue
        fp = os.path.join(D, f"{t['index']}.json")
        if not os.path.exists(fp):
            continue
        ch = json.load(open(fp, encoding="utf-8"))
        vals = [x for x in ch["content"] if isinstance(x, dict) and x.get("type") == "text"]
        if not vals:
            continue
        nt = norm(ch["title"])
        # H. 首段 == 章标题
        if len(vals) >= 2 and norm(vals[0]["value"]) == nt:
            ch["content"].remove(vals[0])
            changed = True
            n_head += 1
            if not WRITE:
                print(f"  H {bid} #{t['index']} [{ch['title'][:18]}]")
        vals = [x for x in ch["content"] if isinstance(x, dict) and x.get("type") == "text"]
        # T. 尾段 == 其他章标题 (删后至少剩 1 段)
        if len(vals) >= 2:
            nl = norm(vals[-1]["value"])
            if nl and nl in all_titles and nl != nt:
                ch["content"].remove(vals[-1])
                changed = True
                n_tail += 1
                if not WRITE:
                    print(f"  T {bid} #{t['index']} 尾 {vals[-1]['value'][:24]!r}")
        if changed and WRITE:
            json.dump(ch, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            changed = False
    if WRITE:
        ra.sync_three(bid)
        print(f"ok {name[:20]:20s} sync")
print(f"\n== 首删 {n_head} 段 / 尾删 {n_tail} 段 ==")
