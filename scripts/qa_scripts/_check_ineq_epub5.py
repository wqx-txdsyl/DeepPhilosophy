# -*- coding: utf-8 -*-
"""看 text00007/8/10.html 的结构: 锚点/注释块/段落"""
import sys, re, zipfile
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ep = r"F:/philosophy/西方/让-雅克·卢梭/论人类不平等的起源和基础.epub"
z = zipfile.ZipFile(ep)
for fn in ("OEBPS/text00007.html", "OEBPS/text00008.html"):
    c = z.read(fn).decode("utf-8", errors="replace")
    # 锚点位置
    anchors = [(m.group(1), c[:m.start()].count("<p")) for m in re.finditer(r'<a[^>]*name="([^"]+)"|id="(sr\d+|s\d+)"', c)]
    print(f"== {fn} 长{len(c)} 锚点={anchors}")
    # 开头 800 字符的段落结构
    ps = re.findall(r"<p[^>]*>(.*?)</p>", c, re.S)
    print(f"  <p> 段落数: {len(ps)}")
    for i, p in enumerate(ps[:6]):
        t = re.sub(r"<[^>]+>", "", p)
        t = re.sub(r"\s+", " ", t).strip()
        print(f"  P{i}: {t[:60]!r}")
    print("  ...")
    for i, p in enumerate(ps[-4:]):
        t = re.sub(r"<[^>]+>", "", p)
        t = re.sub(r"\s+", " ", t).strip()
        print(f"  P{len(ps)-4+i}: {t[:60]!r}")
