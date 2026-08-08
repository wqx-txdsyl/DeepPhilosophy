# -*- coding: utf-8 -*-
"""epub spine 序 + 每文件首标题 + 正文/注释块分布"""
import sys, os, re, zipfile
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ep = r"F:/philosophy/西方/让-雅克·卢梭/论人类不平等的起源和基础.epub"
z = zipfile.ZipFile(ep)
opf = z.read("OEBPS/content.opf").decode("utf-8", errors="replace")
spine = re.findall(r'<itemref idref="([^"]+)"', opf)
manifest = dict(re.findall(r'<item id="([^"]+)"[^>]*href="([^"]+)"', opf))
print("spine 序:")
for i, sid in enumerate(spine):
    href = manifest.get(sid, "?")
    p = "OEBPS/" + href
    if p in z.namelist():
        c = z.read(p).decode("utf-8", errors="replace")
        txt = re.sub(r"<[^>]+>", " ", c)
        txt = re.sub(r"\s+", " ", txt).strip()
        ttl = re.findall(r"<h[1-6][^>]*>(.*?)</h[1-6]>", c, re.S)
        print(f"[{i}] {href} 标题={[re.sub(r'<[^>]+>','',t).strip()[:30] for t in ttl]} 字={len(txt)}")
