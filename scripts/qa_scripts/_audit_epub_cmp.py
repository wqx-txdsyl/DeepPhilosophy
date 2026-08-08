# -*- coding: utf-8 -*-
"""epub 源 vs 库 全文字数比对 (去空白)
找 内容丢失/混入 类损坏: 库字数显著少于/多于 epub 源。
"""
import sys, os, re, json, zipfile
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"F:/philosophy"
CH = r"f:\program\Python\PhiAgent\backend\data\book_chapters"
DD = r"f:\program\Python\PhiAgent\backend\data\book_detail"

def norm_title(t):
    t = re.sub(r"[（(].*?[)）]", "", t)          # 去括号(包括嵌套副标题)
    t = re.sub(r"[（(][^（()）]*[)）]", "", t)     # 再一遍
    t = t.split("|")[0].split("：")[0].split(":")[0]  # 去 冒号/竖线 后副标题
    t = t.replace("《", "").replace("》", "")
    t = t.replace("（", "(").replace("）", ")")
    t = re.sub(r"[\s\u3000]", "", t)
    return t.lower()

# 库书名(规范化) -> bid
lib = {}
lib_detail = {}
for f in os.listdir(DD):
    if not f.endswith(".json"): continue
    bid = f[:-5]
    j = json.load(open(os.path.join(DD, f), encoding="utf-8"))
    lib_detail[bid] = j
    lib[norm_title(j.get("title", ""))] = bid
    # 也注册部分标题(去括号后主名已覆盖)

def epub_all_text(path):
    """epub 全部正文文本(所有 xhtml 文件, 按 spine 序)"""
    z = zipfile.ZipFile(path)
    files = [n for n in z.namelist() if n.lower().endswith((".xhtml", ".html")) and not n.lower().endswith("toc.ncx")]
    # 用 spine 序
    opf = [n for n in z.namelist() if n.lower().endswith(".opf")]
    order = files
    if opf:
        c = z.read(opf[0]).decode("utf-8", errors="replace")
        hrefs = re.findall(r'<item\s+id="[^"]*"[^>]*href="([^"]+)"', c)
        spine = re.findall(r'<itemref\s+idref="([^"]+)"', c)
        id2href = {}
        for m in re.finditer(r'<item\s+id="([^"]+)"[^>]*href="([^"]+)"', c):
            id2href[m.group(1)] = m.group(2)
        order = [id2href.get(s) for s in spine if id2href.get(s)]
    txt = []
    for href in order:
        if not href: continue
        p = href if href.startswith("OEBPS") else "OEBPS/" + href
        if p not in z.namelist():
            p = href
        try:
            c = z.read(p).decode("utf-8", errors="replace")
        except KeyError:
            continue
        body = re.sub(r"<style.*?</style>|<script.*?</script>", "", c, flags=re.S)
        body = re.sub(r"<[^>]+>", "", body)
        txt.append(body)
    return "".join(txt)

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

def epub_chars(path):
    t = epub_all_text(path)
    return len(re.sub(r"\s", "", t))

# 收集所有 epub
epubs = []
for dp, dn, fn in os.walk(ROOT):
    for f in fn:
        if f.lower().endswith(".epub"):
            epubs.append(os.path.join(dp, f))

rows = []
no_match = []
for p in sorted(epubs):
    try:
        z = zipfile.ZipFile(p)
        opf = [n for n in z.namelist() if n.lower().endswith(".opf")]
        c = z.read(opf[0]).decode("utf-8", errors="replace")
        m = re.search(r"<dc:title[^>]*>(.*?)</dc:title>", c, re.S)
        t = re.sub(r"<[^>]+>", "", m.group(1)) if m else os.path.splitext(os.path.basename(p))[0]
    except Exception:
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
    ratio = lc / ec if ec else 0
    rows.append((ratio, t, bid, lc, ec))

print(f"匹配 {len(rows)} 本, 未匹配 {len(no_match)}")
print(f"\n== 字数比对 (库/epub 比例 <70% 或 >140% 可疑) ==")
for ratio, t, bid, lc, ec in sorted(rows):
    flag = ""
    if ratio < 0.7 or ratio > 1.4:
        flag = "  <<<< 可疑"
    print(f"{ratio*100:6.0f}%  {lc:>8,} / {ec:>8,}  [{t}] {flag}")
