# -*- coding: utf-8 -*-
"""扫描 F:/philosophy 下全部 epub 文件, 解析 dc:title, 匹配库 bid"""
import sys, os, re, json, zipfile
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

root = r"F:/philosophy"
epubs = []
for dp, dn, fn in os.walk(root):
    for f in fn:
        if f.lower().endswith(".epub"):
            epubs.append(os.path.join(dp, f))
print(f"epub 文件总数: {len(epubs)}")

# 解析每本 epub 的 dc:title (content.opf)
def epub_title(path):
    try:
        z = zipfile.ZipFile(path)
    except Exception:
        return None
    for cand in ("OEBPS/content.opf", "content.opf", "OEBPS/package.opf", "META-INF/package.opf"):
        if cand in z.namelist():
            c = z.read(cand).decode("utf-8", errors="replace")
            m = re.search(r"<dc:title[^>]*>(.*?)</dc:title>", c, re.S)
            if m:
                t = re.sub(r"<[^>]+>", "", m.group(1))
                t = re.sub(r"\s+", " ", t).strip()
                return t
    # fallback: 文件名
    return os.path.splitext(os.path.basename(path))[0]

# 库书名 -> bid
DD = r"f:\program\Python\PhiAgent\backend\data\book_detail"
lib = {}
for f in os.listdir(DD):
    if not f.endswith(".json"): continue
    bid = f[:-5]
    try:
        j = json.load(open(os.path.join(DD, f), encoding="utf-8"))
    except Exception:
        continue
    lib[j.get("title", "")] = bid

matched = 0
for p in sorted(epubs):
    t = epub_title(p)
    bid = lib.get(t)
    if bid:
        matched += 1
        print(f"MATCH: {t} -> {bid}")
    else:
        print(f"??:    {t} | {p}")
print(f"\n匹配 {matched}/{len(epubs)}")
