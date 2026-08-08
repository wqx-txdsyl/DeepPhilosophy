# -*- coding: utf-8 -*-
"""看 text00015/16 + text00012 注释结构 + 库当前章节字数"""
import sys, re, zipfile, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ep = r"F:/philosophy/西方/让-雅克·卢梭/论人类不平等的起源和基础.epub"
z = zipfile.ZipFile(ep)
for fn in ("OEBPS/text00015.html", "OEBPS/text00016.html"):
    c = z.read(fn).decode("utf-8", errors="replace")
    print(f"\n========== {fn} ==========")
    for m in re.finditer(r"<(p|h[1-6])[^>]*>(.*?)</\1>", c, re.S):
        t = re.sub(r"<[^>]+>", "", m.group(2))
        t = re.sub(r"\s+", " ", t).strip()
        if t:
            print(f"  <{m.group(1)}> {t[:70]}")

# 库当前章节
j = json.load(open(r"f:\program\Python\PhiAgent\data\book_chapters\9e4f98733f0b\meta.json", encoding="utf-8"))
print("\n== 库当前 ==")
for t in j["toc"]:
    if isinstance(t, dict) and t.get("type") == "chapter":
        print(f"  {t.get('index')} {t.get('title')}")
