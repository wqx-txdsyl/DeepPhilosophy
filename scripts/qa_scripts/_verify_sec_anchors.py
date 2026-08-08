# -*- coding: utf-8 -*-
"""验证 meta.toc section 条目的 sec 锚点与章文件 text 块序号一致"""
import json, sys, os
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CH = r"f:\program\Python\PhiAgent\backend\data\book_chapters\c5013f33fe01"
m = json.load(open(os.path.join(CH, "meta.json"), encoding="utf-8"))
bad = 0
total = 0
for t in m["toc"]:
    if t["type"] != "section":
        continue
    total += 1
    ch = json.load(open(os.path.join(CH, f"{t['index']}.json"), encoding="utf-8"))
    texts = [b["value"] for b in ch["content"] if b.get("type") == "text"]
    if t["sec"] >= len(texts) or texts[t["sec"]] != t["title"]:
        bad += 1
        actual = texts[t["sec"]][:24] if t["sec"] < len(texts) else "越界"
        print(f"✗ sec错位: index={t['index']} sec={t['sec']} title={t['title'][:24]!r} 实际={actual!r}")
print(f"section 条目 {total} 个, 错位 {bad} 个")
