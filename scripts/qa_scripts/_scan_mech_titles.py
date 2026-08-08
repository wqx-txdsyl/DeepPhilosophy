# -*- coding: utf-8 -*-
"""全库扫机械化章节标题: chapter_x / part_x / text_x / sec_x 等
+ 检查这些书的章节首段是否以标题残渣开头"""
import sys, os, re, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CH = r"f:\program\Python\PhiAgent\backend\data\book_chapters"

MECH = re.compile(r"^(chapter|part|text|sec|section|sect|file|page|image|img|content|index|split|intro|ch)[\s_\-\.]?\d+$|^\d+[\s_\-\.]?(chapter|part|text|sec)$", re.I)

found = []
for bid in sorted(os.listdir(CH)):
    mp = os.path.join(CH, bid, "meta.json")
    if not os.path.exists(mp): continue
    meta = json.load(open(mp, encoding="utf-8"))
    title = meta.get("title", bid)
    n = meta.get("chapterCount", 0)
    bad = []
    for i in range(n):
        jp = os.path.join(CH, bid, f"{i}.json")
        if not os.path.exists(jp): continue
        j = json.load(open(jp, encoding="utf-8"))
        ct = j.get("title", "")
        if MECH.match(ct.strip()):
            # 看首段是否也是残渣
            texts = [b["value"] for b in j.get("content", []) if b.get("type") == "text"]
            first = texts[0] if texts else ""
            bad.append((i, ct, first[:50]))
    if bad:
        found.append((title, bid, bad))

print(f"机械化标题书: {len(found)} 本")
for t, bid, bad in found:
    print(f"\n【{t}】 {bid} 共{len(bad)}章:")
    for i, ct, f in bad[:12]:
        print(f"  [{i}] {ct!r} 首段: {f!r}")
    if len(bad) > 12:
        print(f"  ... 共 {len(bad)} 章")
