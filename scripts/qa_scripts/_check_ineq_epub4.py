# -*- coding: utf-8 -*-
"""按 spine idref 顺序列每文件标题/字数 + toc.ncx 章节映射"""
import sys, re, zipfile
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ep = r"F:/philosophy/西方/让-雅克·卢梭/论人类不平等的起源和基础.epub"
z = zipfile.ZipFile(ep)
opf = z.read("OEBPS/content.opf").decode("utf-8", errors="replace")
manifest = {}
for m in re.finditer(r'<item\s+id="([^"]+)"[^>]*href="([^"]+)"', opf):
    manifest[m.group(1)] = m.group(2)
spine = re.findall(r'<itemref\s+idref="([^"]+)"', opf)
print("== spine 顺序 ==")
for i, sid in enumerate(spine):
    href = manifest.get(sid)
    if not href:
        print(f"[{i}] {sid} 无 href")
        continue
    p = "OEBPS/" + href
    c = z.read(p).decode("utf-8", errors="replace")
    ttl = re.findall(r"<h[1-6][^>]*>(.*?)</h[1-6]>", c, re.S)
    ttl = [re.sub(r"<[^>]+>", "", t).strip()[:36] for t in ttl]
    txt = re.sub(r"<[^>]+>", " ", c)
    txt = re.sub(r"\s+", " ", txt).strip()
    print(f"[{i}] {href} {len(txt)}字 标题={ttl}")
print("\n== toc.ncx ==")
ncx = z.read("OEBPS/toc.ncx").decode("utf-8", errors="replace")
for m in re.finditer(r'<navPoint[^>]*>.*?<text>(.*?)</text>.*?src="([^"]+)"', ncx, re.S):
    print(f"  {re.sub(r'<[^>]+>','',m.group(1)).strip()[:40]} → {m.group(2)}")
