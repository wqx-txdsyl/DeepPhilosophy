# -*- coding: utf-8 -*-
"""全库扫描: meta.toc 与 chapterCount/chapterTitles 不一致（尼采与哲学式漏同步）"""
import sys, os, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CH = r"f:/program/Python/PhiAgent/backend/data/book_chapters"
bad = []
for bid in sorted(os.listdir(CH)):
    bd = os.path.join(CH, bid)
    mfp = os.path.join(bd, "meta.json")
    if not os.path.exists(mfp):
        continue
    m = json.load(open(mfp, encoding="utf-8"))
    n = m.get("chapterCount")
    toc = m.get("toc", [])
    titles = m.get("chapterTitles", [])
    tlen = len(toc)
    def _tt(t):
        return t.get("title") if isinstance(t, dict) else t
    toc_idx = [t.get("index") if isinstance(t, dict) else None for t in toc]
    toc_titles = [_tt(t) for t in toc if isinstance(t, dict) or True]
    # 字符串 toc = 全 chapter 无 index → 按序对齐
    if all(i is None for i in toc_idx):
        toc_idx = list(range(tlen))
    ok = (tlen == n and toc_idx == list(range(n)) and titles == toc_titles)
    if not ok:
        bad.append((bid, m.get("title", "")[:20], n, tlen, len(titles), toc_idx[:6], toc_idx[-3:]))
print(f"共 {len(bad)} 本 toc 不一致:")
for b in bad:
    print(" ✗", b)
