# -*- coding: utf-8 -*-
"""全文件 h1 分布 + text00010 完整段落"""
import sys, re, zipfile
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ep = r"F:/philosophy/西方/让-雅克·卢梭/论人类不平等的起源和基础.epub"
z = zipfile.ZipFile(ep)
for fn in sorted(n for n in z.namelist() if re.match(r"OEBPS/text\d+\.html$", n)):
    c = z.read(fn).decode("utf-8", errors="replace")
    hs = [re.sub(r"<[^>]+>", "", m).strip() for m in re.findall(r"<h[1-6][^>]*>(.*?)</h[1-6]>", c, re.S)]
    ps = len(re.findall(r"<p[^>]*>", c))
    print(f"{fn}: {len(c)}字 h={hs} p={ps}")
print("\n== text00010 完整 ==")
c = z.read("OEBPS/text00010.html").decode("utf-8", errors="replace")
for m in re.finditer(r"<(p|h[1-6])[^>]*>(.*?)</\1>", c, re.S):
    t = re.sub(r"<[^>]+>", "", m.group(2))
    t = re.sub(r"\s+", " ", t).strip()
    if t:
        print(f"  <{m.group(1)}> {t[:80]}")
