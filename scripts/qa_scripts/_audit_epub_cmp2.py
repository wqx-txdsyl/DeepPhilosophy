# -*- coding: utf-8 -*-
"""epub 源 vs 库 字数比对 v2: 修 spine 解析
- item 标签属性顺序任意, href 可能相对 manifest 目录
- 找不到 spine 就按文件名序
"""
import sys, os, re, json, zipfile
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"F:/philosophy"
CH = r"f:\program\Python\PhiAgent\backend\data\book_chapters"
DD = r"f:\program\Python\PhiAgent\backend\data\book_detail"

def norm_title(t):
    t = re.sub(r"[（(][^（()）]*[)）]", "", t)
    t = t.split("|")[0]
    t = t.replace("《", "").replace("》", "")
    t = re.sub(r"[\s\u3000]", "", t)
    return t.lower()

lib = {}
for f in os.listdir(DD):
    if not f.endswith(".json"): continue
    bid = f[:-5]
    j = json.load(open(os.path.join(DD, f), encoding="utf-8"))
    lib[norm_title(j.get("title", ""))] = bid

def epub_blocks(path):
    """返回 [(file, text)] 按 spine 序"""
    z = zipfile.ZipFile(path)
    names = z.namelist()
    opf = [n for n in names if n.lower().endswith(".opf")]
    order = []
    if opf:
        c = z.read(opf[0]).decode("utf-8", errors="replace")
        # manifest: 任意属性顺序
        items = {}
        for m in re.finditer(r'<item\b([^>]*)/?>', c):
            attrs = dict(re.findall(r'(\w+)\s*=\s*"([^"]*)"', m.group(1)))
            if attrs.get("href"):
                items[attrs.get("id", "")] = attrs["href"]
        spine = re.findall(r'<itemref\b[^>]*?idref="([^"]+)"', c)
        order = [items.get(s) for s in spine if s in items]
        base = os.path.dirname(opf[0])
    # fallback: 文件名序
    if not order:
        order = sorted(n for n in names if n.lower().endswith((".xhtml", ".html")) and "toc" not in n.lower())
        base = ""
    blocks = []
    for href in order:
        if not href:
            continue
        p = href
        if base and not href.startswith(base):
            p = base + "/" + href
        if p not in names:
            # 再试直接名
            cand = [n for n in names if n.endswith("/" + href.split("/")[-1])]
            if not cand:
                continue
            p = cand[0]
        c = z.read(p).decode("utf-8", errors="replace")
        body = re.sub(r"<style.*?</style>|<script.*?</script>", "", c, flags=re.S)
        body = re.sub(r"<[^>]+>", "", body)
        blocks.append((p, body))
    return blocks

def epub_chars(path):
    total = 0
    for p, t in epub_blocks(path):
        total += len(re.sub(r"\s", "", t))
    return total

def lib_chars(bid):
    total = 0
    meta = json.load(open(os.path.join(CH, bid, "meta.json"), encoding="utf-8"))
    for i in range(meta.get("chapterCount", 0)):
        p = os.path.join(CH, bid, f"{i}.json")
        if not os.path.exists(p): continue
        j = json.load(open(p, encoding="utf-8"))
        for b in j.get("content", []):
            if b.get("type") == "text":
                total += len(re.sub(r"\s", "", b["value"]))
    return total

epubs = []
for dp, dn, fn in os.walk(ROOT):
    for f in fn:
        if f.lower().endswith(".epub"):
            epubs.append(os.path.join(dp, f))

rows, no_match, errs = [], [], []
for p in sorted(epubs):
    try:
        z = zipfile.ZipFile(p)
        opf = [n for n in z.namelist() if n.lower().endswith(".opf")]
        c = z.read(opf[0]).decode("utf-8", errors="replace")
        m = re.search(r"<dc:title[^>]*>(.*?)</dc:title>", c, re.S)
        t = re.sub(r"<[^>]+>", "", m.group(1)) if m else os.path.splitext(os.path.basename(p))[0]
    except Exception as e:
        errs.append((os.path.basename(p), str(e)))
        continue
    bid = lib.get(norm_title(t))
    if not bid:
        no_match.append((t, p))
        continue
    try:
        ec = epub_chars(p)
        lc = lib_chars(bid)
    except Exception as e:
        print(f"ERR {t}: {e}")
        continue
    rows.append((lc / ec if ec else 0, t, bid, lc, ec))

print(f"匹配 {len(rows)}, 未匹配 {len(no_match)}, 读取错误 {len(errs)}")
if errs:
    print("错误:", errs[:10])
print(f"\n== 全部有效比对 (按比例排序) ==")
for ratio, t, bid, lc, ec in sorted(rows):
    flag = ""
    if ratio < 0.7 or ratio > 1.4:
        flag = "  <<<< 可疑"
    print(f"{ratio*100:6.0f}%  {lc:>8,} / {ec:>8,}  [{t}] {flag}")
