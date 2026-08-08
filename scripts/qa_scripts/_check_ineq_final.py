# -*- coding: utf-8 -*-
"""抽查重建后 9e4f98733f0b: 各章首/尾段 + 三端一致性"""
import sys, json, os, hashlib
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
base = r"f:\program\Python\PhiAgent\backend\data\book_chapters\9e4f98733f0b"
m = json.load(open(os.path.join(base, "meta.json"), encoding="utf-8"))
print("chapterCount:", m["chapterCount"])
for t in m["toc"]:
    print("  toc:", json.dumps(t, ensure_ascii=False))
for i in range(12):
    j = json.load(open(os.path.join(base, f"{i}.json"), encoding="utf-8"))
    blocks = [b for b in j["content"] if b.get("type") == "text"]
    first = blocks[0]["value"] if blocks else ""
    last = blocks[-1]["value"] if blocks else ""
    print(f"[{i}] {j['title']}: 段{len(blocks)} | 首: {first[:42]!r} | 尾: {last[:42]!r}")

# 三端 md5
def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()[:8]
ph = r"f:\program\Python\PhiAgent\backend\data\book_chapters\9e4f98733f0b"
dpb = r"f:\program\Python\DeepPhilosophy\DeepPhilosophy\backend\data\book_chapters\9e4f98733f0b"
dpp = r"f:\program\Python\DeepPhilosophy\DeepPhilosophy\app\public\backend\data\book_chapters\9e4f98733f0b"
for f in ["meta.json", "0.json", "6.json", "11.json"]:
    print(f"{f}: {md5(os.path.join(ph,f))} {md5(os.path.join(dpb,f))} {md5(os.path.join(dpp,f))}")
