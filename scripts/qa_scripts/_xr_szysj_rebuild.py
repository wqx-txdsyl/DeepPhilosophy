# -*- coding: utf-8 -*-
"""《存在与时间》释义（张汝伦）32bcb0d7a466 重建（一次性，ncx 平铺无层级 + 文件边界）
epub: F:/philosophy/西方/张汝伦/《存在与时间》释义.epub（120 万字，含每节释义长文）
ncx 23 条全平铺（无层级）→ 旧数据 23 章全平铺："导论/第一篇/第二篇"被压成 chapter（✗B）。
真实层级（原书结构 + part0011 标题页证"第一部"）:
  [ch] 引言/发凡/缘起/破题
  [part] 导论 阐述存在的意义问题（含 2 章）
  [ch] 第一部 依时间性解释此在和将时间解说为存在问题的超越境域（2711 字标题页释义）
  [part] 第一篇 准备性的对此在的基本分析（含 6 章）
  [part] 第二篇 此在与时间性（含 6 章）
  [ch] 结语 / 征引书目
  SKIP: part0000-0002 卷首、part0007 "释义"孤标题页、part0028 版权页、part0029 广告页
part 导读内容（导论 604/第一篇 1801/第二篇 39715）并入所属 part 首章开头（part 无内容通道）。
节 = 正文"^第X节"块（72 个，释义书删节 42/45/46/52/61/63/66/67/77/80 属原书体例，不补），按文件归属章。
节标题修正: "第一节明确…"补空格、"第七十节 …时间性367"剥尾页码、"第十一节 …解释。"剥尾句号。
剥除: 章/part 标题块（norm 命中 toc 标题）+ 节标题块（norm 命中）。
用法: python _xr_szysj_rebuild.py [--dry]
"""
import zipfile, re, json, os, sys, html as H, shutil

EP = 'F:/philosophy/西方/张汝伦/《存在与时间》释义.epub'
BID = "32bcb0d7a466"
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

def fix_sec_title(v):
    """节标题修正: 补空格（第一节明确→第一节 明确）、剥尾页码（…时间性367→…时间性）、剥尾句号"""
    v = re.sub(r'^(第[一二三四五六七八九十百零]+节)([^\s])', r'\1 \2', v)
    v = re.sub(r'\d+$', '', v)
    v = v.rstrip('。')
    return v

# ---- 章节表（title, part 标题或 None, 文件前缀列表） ----
P = "text/"
CHS = [
    ("引言", None, ["part0003.html"]),
    ("发凡", None, ["part0004.html"]),
    ("《存在与时间》的缘起", None, ["part0005.html"]),
    ("破题", None, ["part0006.html"]),
    ("导论 阐述存在的意义问题", "PART", ["part0008.html", "part0009.html", "part0010.html"]),
    ("第一章 存在问题的必要性、结构和优先性", "导论 阐述存在的意义问题", ["part0008.html", "part0009.html"]),
    ("第二章 阐明存在问题的双重任务；研究的方法及其轮廓", "导论 阐述存在的意义问题", ["part0010.html"]),
    ("第一部 依时间性解释此在和将时间解说为存在问题的超越境域", None, ["part0011.html"]),
    ("第一篇 准备性的对此在的基本分析", "PART", ["part0012.html", "part0013.html", "part0014.html", "part0015_split_000.html", "part0015_split_001.html", "part0016.html", "part0017_split_000.html", "part0017_split_001.html", "part0018_split_000.html", "part0018_split_001.html"]),
    ("第一章 此在的准备性分析之任务的说明", "第一篇 准备性的对此在的基本分析", ["part0012.html", "part0013.html"]),
    ("第二章 作为此在基本状况的一般在世界中存在[1]", "第一篇 准备性的对此在的基本分析", ["part0014.html"]),
    ("第三章 世界的世界性", "第一篇 准备性的对此在的基本分析", ["part0015_split_000.html", "part0015_split_001.html"]),
    ("第四章 作为共在和自我存在的在世存在。“常人”", "第一篇 准备性的对此在的基本分析", ["part0016.html"]),
    ("第五章 在之中本身", "第一篇 准备性的对此在的基本分析", ["part0017_split_000.html", "part0017_split_001.html"]),
    ("第六章 作为此在之存在的操心", "第一篇 准备性的对此在的基本分析", ["part0018_split_000.html", "part0018_split_001.html"]),
    ("第二篇 此在与时间性", "PART", ["part0019.html", "part0020.html", "part0021_split_000.html", "part0021_split_001.html", "part0022.html", "part0023.html", "part0024.html", "part0025.html"]),
    ("第一章 此在可能的整体存在和向死存在", "第二篇 此在与时间性", ["part0019.html", "part0020.html"]),
    ("第二章 此在对本己的能在的证明与决断", "第二篇 此在与时间性", ["part0021_split_000.html", "part0021_split_001.html"]),
    ("第三章 此在本己的整体能在和作为操心的存在论意义的时间性", "第二篇 此在与时间性", ["part0022.html"]),
    ("第四章 时间性与日常性", "第二篇 此在与时间性", ["part0023.html"]),
    ("第五章 时间性和历史性", "第二篇 此在与时间性", ["part0024.html"]),
    ("第六章 时间性和作为流俗时间起源的时间内状态", "第二篇 此在与时间性", ["part0025.html"]),
    ("结语: 《存在与时间》为什么没有完成？", None, ["part0026.html"]),
    ("征引书目", None, ["part0027.html"]),
]

# 预提取所有文件块
blk_cache = {}
def get_blocks(f):
    if f not in blk_cache:
        blk_cache[f] = extract_blocks(P + f)
    return blk_cache[f]

# 章标题/part 标题 norm 集
ch_norm = {}
part_norm = {}
for title, pt, _ in CHS:
    if pt == "PART":
        part_norm[norm(title)] = title
    elif pt is None:
        ch_norm[norm(title)] = title

# 每章节标题提取（正文 ^第X节 块 + 修正）
SEC_PAT = re.compile(r'^第[一二三四五六七八九十百零]+节')
sec_by_ch = {}
for title, pt, files in CHS:
    if pt in (None, "PART"):
        continue
    seen, out = set(), []
    for f in files:
        for v in get_blocks(f):
            if SEC_PAT.match(v) and len(norm(v)) <= 50:
                fv = fix_sec_title(v)
                nv = norm(fv)
                if nv not in seen:
                    seen.add(nv)
                    out.append(fv)
    sec_by_ch[title] = out
sec_norm_all = {norm(t): t for secs in sec_by_ch.values() for t in secs}

toc = []
files = {}
warns = []
junk_count = 0
total_chars = 0
ch_index = 0
pending_part = None
for title, pt, files_list in CHS:
    if pt == "PART":
        toc.append({"type": "part", "title": title, "index": ch_index, "level": 0})
        pending_part = title
        continue
    blocks = []
    junk = 0
    stripped_t = False
    tnorm = norm(title)
    pt_norm = norm(pt) if pt not in (None, "PART") else None
    for f in files_list:
        for v in get_blocks(f):
            nv = norm(v)
            if pt_norm and nv == pt_norm:
                junk += 1
                pt_norm = None
                continue
            if not stripped_t and nv == tnorm:
                junk += 1
                stripped_t = True
                continue
            if SEC_PAT.match(v) and norm(fix_sec_title(v)) in sec_norm_all:
                junk += 1
                continue
            blocks.append({"type": "text", "value": v})
    if not stripped_t:
        warns.append(f"!! 未剥章标题: {title}")
    junk_count += junk
    if not blocks:
        warns.append(f"!! 空章节: {title}")
        continue
    toc.append({"type": "chapter", "title": title, "index": ch_index, "level": 1})
    for si, s in enumerate(sec_by_ch.get(title, []), 1):
        toc.append({"type": "section", "title": s, "index": ch_index, "sec": si, "level": 2})
    files[ch_index] = {"index": ch_index, "title": title, "content": blocks}
    ch_index += 1

print(f"章节总数: {len(files)} | part: {sum(1 for t in toc if t['type']=='part')} | "
      f"section: {sum(1 for t in toc if t['type']=='section')} | 剥除: {junk_count} | 警告: {len(warns)}")
for w in warns:
    print("⚠", w)
for idx in sorted(files):
    ch = files[idx]
    nc = sum(len(b['value']) for b in ch['content'])
    total_chars += nc
    print(f"  {idx:2d} {ch['title'][:38]:40s} {nc:7d} 字")
print(f"\n总: {len(files)} 章, {total_chars} 字符（旧 23 章 1197487）")
# 各章节号检查
for tt in toc:
    ind = '  ' * tt.get('level', 1)
    print(f"{ind}[{tt['type']} {tt.get('sec','')}] {tt['title'][:44]}")
# 节号连续性检查
for title, secs in sec_by_ch.items():
    nums = []
    for s in secs:
        m = re.match(r'^第([一二三四五六七八九十百零]+)节', s)
        if m:
            CN = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,
                  '十':10,'二十':20,'三十':30,'四十':40,'五十':50,'六十':60,'七十':70,'八十':80,'九十':90,
                  '百':100,'二十一':21,'二十二':22,'二十三':23,'二十四':24,'二十五':25,'二十六':26,'二十七':27,
                  '二十八':28,'二十九':29,'三十一':31,'三十二':32,'三十三':33,'三十四':34,'三十五':35,'三十六':36,
                  '三十七':37,'三十八':38,'三十九':39,'四十一':41,'四十二':42,'四十三':43,'四十四':44,'四十五':45,
                  '四十六':46,'四十七':47,'四十八':48,'四十九':49,'五十一':51,'五十二':52,'五十三':53,'五十四':54,
                  '五十五':55,'五十六':56,'五十七':57,'五十八':58,'五十九':59,'六十一':61,'六十二':62,'六十三':63,
                  '六十四':64,'六十五':65,'六十六':66,'六十七':67,'六十八':68,'六十九':69,'七十一':71,'七十二':72,
                  '七十三':73,'七十四':74,'七十五':75,'七十六':76,'七十七':77,'七十八':78,'七十九':79,'八十一':81,
                  '八十二':82,'八十三':83}
            nums.append(CN.get(m.group(1), 0))
    if nums:
        print(f"  节[{title[:24]}]: {nums}")

if '--dry' in sys.argv:
    for idx, ch in files.items():
        for b in ch['content']:
            v = b['value']
            if re.match(r'^第[一二三四五六七八九十百零]+节', v) and len(norm(v)) <= 50:
                print(f"⚠ 残留节标题 [{idx} {ch['title'][:10]}]: {v[:40]}")
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
    "title": old_meta.get("title") or "《存在与时间》释义",
    "author": old_meta.get("author") or "张汝伦",
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
