# -*- coding: utf-8 -*-
"""检查: epub 各文件 img 标签 + 库 0.json 完整结构 + text00012 前几段"""
import sys, re, json, zipfile
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ep = r"F:/philosophy/西方/让-雅克·卢梭/论人类不平等的起源和基础.epub"
z = zipfile.ZipFile(ep)
for fn in sorted(n for n in z.namelist() if re.match(r"OEBPS/text\d+\.html$", n)):
    c = z.read(fn).decode("utf-8", errors="replace")
    imgs = re.findall(r'<img[^>]*src="([^"]+)"', c)
    if imgs:
        print(f"{fn}: {imgs}")

print("\n== 库 0.json 完整 ==")
j = json.load(open(r"f:\program\Python\PhiAgent\backend\data\book_chapters\9e4f98733f0b\0.json", encoding="utf-8"))
print(json.dumps(j, ensure_ascii=False, indent=1)[:1500])

print("\n== text00012 前 8 段 ==")
c = z.read("OEBPS/text00012.html").decode("utf-8", errors="replace")
k = 0
for m in re.finditer(r"<(p|h[1-6])[^>]*>(.*?)</\1>", c, re.S):
    t = re.sub(r"<[^>]+>", "", m.group(2))
    t = re.sub(r"\s+", " ", t).strip()
    if t and k < 8:
        print(f"  <{m.group(1)}> {t[:70]}")
        k += 1
