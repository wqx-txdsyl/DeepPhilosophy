# -*- coding: utf-8 -*-
"""dump text00004-00010 全部段落(带标签类型), 找标题段"""
import sys, re, zipfile
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ep = r"F:/philosophy/西方/让-雅克·卢梭/论人类不平等的起源和基础.epub"
z = zipfile.ZipFile(ep)
for fn in [f"OEBPS/text{i:05d}.html" for i in range(4, 11)]:
    c = z.read(fn).decode("utf-8", errors="replace")
    print(f"\n========== {fn} ==========")
    # 段落/标题/div 全结构, 只打文本行
    for m in re.finditer(r"<(p|h[1-6]|div|li)[^>]*>(.*?)</\1>", c, re.S):
        tag, body = m.group(1), m.group(2)
        t = re.sub(r"<[^>]+>", "", body)
        t = re.sub(r"\s+", " ", t).strip()
        if t:
            print(f"  <{tag}> {t[:70]}")
