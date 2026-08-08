# -*- coding: utf-8 -*-
"""《反杜林论》导读 62c5caa0bfde 重建（一次性，ncx 完整 + 文件边界）
epub: F:/philosophy/西方/弗里德里希·恩格斯/《反杜林论》导读.epub
旧数据 5 章缺第二章（第一章→第三章跳号，part0005 未被收入）。
ncx 结构（playOrder 重排后）: 扉页/目录/版权页/总序(SKIP 丛书总序 艾四林)/
  第一章(part0004×4, 3 节)/第二章(part0005×1, 无节)/第三章(part0006×13, 12 节)/
  第四章(part0007×11, 10 节)/第五章(part0008×6, 5 节)/第六章(part0009×3, 2 节)/参考文献(part0010×1)
章节边界 = 文件边界（ncx src 一一对应）; 节边界 = split 文件边界。
剥除: 章标题块（norm == ncx 章标题）/ 节标题块（norm == ncx 节标题, 每节文件首块）。
保留: 章导语块/【本章注释】列表/参考文献。
用法: python _xr_fandulin_rebuild.py [--dry]
"""
import zipfile, re, json, os, sys, html as H, shutil

EP = 'F:/philosophy/西方/弗里德里希·恩格斯/《反杜林论》导读.epub'
BID = "62c5caa0bfde"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"

z = zipfile.ZipFile(EP)

def norm(s):
    return re.sub(r"\s+", "", s or "")

_TAG = re.compile(r'<[^>]+>')

def el_text(seg):
    seg = re.sub(r'<br\s*/?>', '\n', seg, flags=re.I)
    seg = _TAG.sub('', seg)
    seg = H.unescape(seg)
    seg = re.sub(r'[ \t\xa0]+', ' ', seg)
    return seg.strip()

def extract_blocks(fname):
    h = z.read(fname).decode('utf-8')
    raw = []
    for m in re.finditer(r'<(p|table|h[1-6]|blockquote)[^>]*>(.*?)</\1>', h, re.S):
        tag, inner = m.group(1), m.group(2)
        if tag == 'table':
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', inner, re.S)
            text = '  '.join(
                '  '.join(el_text(c) for c in re.findall(r'<t[hd][^>]*>(.*?)</t[hd]>', r, re.S))
                for r in rows)
        else:
            text = el_text(inner)
        if text:
            raw.append([m.start(), m.end(), text])
    raw.sort(key=lambda x: x[0])
    drop = set()
    for i in range(len(raw)):
        for j in range(i + 1, len(raw)):
            if raw[j][0] >= raw[i][1]:
                break
            if raw[j][1] <= raw[i][1] and raw[j][2] == raw[i][2]:
                drop.add(i)
                break
    return [raw[k][2] for k in range(len(raw)) if k not in drop]

# ---- 章节表（title, 文件列表, 节标题列表） ----
CHS = [
    ("第一章 《反杜林论》的由来", [f"text/part0004_split_{i:03d}.html" for i in range(4)],
     ["一、写作背景", "二、成书过程", "三、文本结构与核心思想"]),
    ("第二章 《反杜林论》的方法论原则——《序言》和《引论》", ["text/part0005.html"], []),
    ("第三章 马克思主义哲学观——哲学编", [f"text/part0006_split_{i:03d}.html" for i in range(13)],
     ["一、先验主义批判：体系哲学的破产", "二、世界模式论批判：世界统一于物质而非存在",
      "三、时间和空间与物质的辩证运动", "四、世界的物质演化", "五、进化论的科学意义",
      "六、关于生命本质的科学说明", "七、关于道德、正义观念的真理性认识及其辩证规律",
      "八、关于平等观念的科学认识", "九、自由是对必然的认识", "十、矛盾是辩证法的核心",
      "十一、辩证法是现实规律的逻辑表现", "十二、辩证唯物主义的科学结论"]),
    ("第四章 马克思主义政治经济学——政治经济学编", [f"text/part0007_split_{i:03d}.html" for i in range(11)],
     ["一、经济学是关于生产、分配和交换的学问", "二、暴力的本质在于社会经济关系",
      "三、暴力的基础在于社会经济关系", "四、暴力的社会基础在于阶级关系",
      "五、商品的价值是由体现在商品中的社会必要劳动决定的",
      "六、商品的价值是由包含在商品中的人的劳动决定的",
      "七、剩余价值论揭露了资本主义生产方式的秘密", "八、剩余价值揭露了资本剥削的秘密",
      "九、认识经济规律的客观基础", "十、批判经济思想史中的虚无主义"]),
    ("第五章 社会主义从空想到科学——社会主义编", [f"text/part0008_split_{i:03d}.html" for i in range(6)],
     ["一、现代社会主义必须走出空想", "二、社会主义社会的基本特征", "三、认清现代大工业的实质",
      "四、单纯改良分配形式没有出路", "五、以科学社会主义为原则为未来社会的发展指明方向"]),
    ("第六章 《反杜林论》的历史影响和现实意义", [f"text/part0009_split_{i:03d}.html" for i in range(3)],
     ["一、历史影响", "二、现实意义"]),
    ("参考文献", ["text/part0010.html"], []),
]

# 章/节标题 norm 集（剥除用）
ch_norm = {norm(t): t for t, _, _ in CHS}
sec_norm_all = {}
for ch_title, files, secs in CHS:
    for s in secs:
        sec_norm_all[norm(s)] = s

toc = []
files = {}
warns = []
junk_count = 0
total_chars = 0
for idx, (title, fnames, secs) in enumerate(CHS):
    blocks = []
    junk = 0
    stripped_ch = False
    for fn in fnames:
        for v in extract_blocks(fn):
            nv = norm(v)
            if not stripped_ch and nv in ch_norm:
                junk += 1
                stripped_ch = True
                continue
            if nv in sec_norm_all:
                junk += 1
                continue
            blocks.append({"type": "text", "value": v})
    if not stripped_ch:
        warns.append(f"!! 未剥章标题: {title}")
    junk_count += junk
    if not blocks:
        warns.append(f"!! 空章节: {title}")
        continue
    toc.append({"type": "chapter", "title": title, "index": idx, "level": 1})
    for si, s in enumerate(secs, 1):
        toc.append({"type": "section", "title": s, "index": idx, "sec": si, "level": 2})
    files[idx] = {"index": idx, "title": title, "content": blocks}

print(f"章节总数: {len(files)} | toc: {len(toc)} | 剥除块: {junk_count} | 警告: {len(warns)}")
for w in warns:
    print("⚠", w)
for idx in sorted(files):
    ch = files[idx]
    nc = sum(len(b['value']) for b in ch['content'])
    total_chars += nc
    print(f"  {idx:2d} {ch['title'][:40]:42s} {nc:7d} 字")
print(f"\n总: {len(files)} 章, {total_chars} 字符")
old_total = 0
if os.path.isdir(SRC):
    for fn in os.listdir(SRC):
        if fn.endswith('.json') and fn != 'meta.json':
            ch = json.load(open(os.path.join(SRC, fn), encoding='utf-8'))
            old_total += sum(len(b.get('value', '')) for b in ch.get('content', []))
print(f"旧数据总字数: {old_total}（缺第二章）")
for tt in toc:
    ind = '  ' * tt.get('level', 1)
    print(f"{ind}[{tt['type']} {tt.get('sec','')}] {tt['title'][:44]}")
# 残留检查
if '--dry' in sys.argv:
    for idx, ch in files.items():
        for b in ch['content']:
            v = b['value']
            if re.match(r'^第[一二三四五六]章', v) or re.match(r'^[一二三四五六七八九十]+、', v):
                print(f"⚠ 残留标题 [{idx} {ch['title'][:12]}]: {v[:40]}")
    sys.exit(0)

if os.path.isdir(SRC):
    suf = "_old_bad"
    i2 = 2
    while os.path.isdir(SRC + suf):
        suf = f"_old_bad{i2}"
        i2 += 1
    os.rename(SRC, SRC + suf)
    print(f"备份旧数据 → {os.path.basename(SRC) + suf}")
os.makedirs(SRC)
old_meta = {}
old_bid = SRC + "_old_bad"
if os.path.isdir(old_bid) and os.path.exists(os.path.join(old_bid, "meta.json")):
    old_meta = json.load(open(os.path.join(old_bid, "meta.json"), encoding="utf-8"))
for idx, ch in files.items():
    json.dump(ch, open(os.path.join(SRC, f"{idx}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
meta = {
    "bookId": old_meta.get("bookId") or BID,
    "title": old_meta.get("title") or "《反杜林论》导读",
    "author": old_meta.get("author") or "艾四林",
    "toc": toc,
    "cover": old_meta.get("cover"),
    "chapterCount": len(files),
    "chapterTitles": [ch["title"] for ch in files.values()],
}
json.dump(meta, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print(f"✓ 写入 {SRC}: {len(files)} 章 + meta.json")

shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
print("✓ 同步 DP")
