# -*- coding: utf-8 -*-
"""找库内容的真实 epub 来源: 搜含库 ch3 首段句子的 epub"""
import sys, os, re, glob, zipfile
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

QUERY = "奥德修斯的忠实猎犬"
hits = glob.glob(r"F:/philosophy/**/*.epub", recursive=True)
for p in sorted(hits):
    bn = os.path.basename(p)
    if "狗狗" not in bn and "十二次哲学漫步" not in p:
        continue
    try:
        z = zipfile.ZipFile(p)
    except Exception:
        continue
    found = []
    for n in z.namelist():
        if not n.lower().endswith((".xhtml", ".html")):
            continue
        try:
            c = z.read(n).decode("utf-8", errors="replace")
        except Exception:
            continue
        if QUERY in c:
            found.append(n)
    if found:
        print(f"✓ {p}")
        print(f"    含查询句的文件: {found}")
    else:
        print(f"✗ {p} (不含)")
