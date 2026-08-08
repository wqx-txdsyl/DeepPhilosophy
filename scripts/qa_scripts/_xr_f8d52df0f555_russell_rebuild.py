# -*- coding: utf-8 -*-
"""#256 西方哲学史（下卷）（f8d52df0f555，伯特兰·罗素）重建
病因: 旧 78 章为 dp_pdf_import 自动切章（目录级过细，toc 标题乱取，
  出版说明/第三章/第四章/第六章科学的兴盛……/第八章/第九章——乱章）。
源: F:/philosophy/西方/伯特兰·罗素/西方哲学史（下卷）.pdf（495 页扫描版，
  商务印书馆 1981 汉译世界学术名著丛书，checkpoint OCR 495 页 fail 0）
结构（目录 p4-5，书内页码=PDF页-3）:
  p0-3 封面/CIP/版权（跳过）｜ p4-5 目录（跳过）｜ p6 正文第一章起
  31 章: 第一章总说 p6 / 第二章意大利文艺复兴 p10 / 第三章马基雅弗利 p20 /
    第四章埃拉斯摩和莫尔 p30 / 第五章宗教改革运动和反宗教改革运动 p43 /
    第六章科学的兴盛 p46 / 第七章弗兰西斯·培根 p64 / 第八章霍布士的利维坦 p69 /
    第九章笛卡尔 p82 / 第十章斯宾诺莎 p95 / 第十一章莱布尼兹 p109 /
    第十二章哲学上的自由主义 p127 / 第十三章洛克的认识论 p136 /
    第十四章洛克的政治哲学 p151 / 第十五章洛克的影响 p177 / 第十六章贝克莱 p184 /
    第十七章休谟 p199 / 第十八章浪漫主义运动 p216 / 第十九章卢梭 p228 /
    第二十章康德 p246 / 第二十一章十九世纪思潮 p266 / 第二十二章黑格尔 p278 /
    第二十三章拜伦 p297 / 第二十四章叔本华 p306 / 第二十五章尼采 p314 /
    第二十六章功利主义者 p329 / 第二十七章卡尔·马克思 p339 / 第二十八章柏格森 p349 /
    第二十九章威廉·詹姆士 p371 / 第三十章约翰·杜威 p381 / 第三十一章逻辑分析哲学 p392
  尾: 人物索引 p401-463 / 神话、文学作品人物索引 p464-471 /
    术语索引 p472-494（p472 前言页: 残字页眉+说明文字+词条；索引原样保留不清理）
⚠ 章标题嵌在正文流中（非独立标题页）: 标题行出现在前章结尾页页内
  （p266 行12 '第二十一意十九世纪思潮' 等），正文从标题行下一行续到下一页——
  章节边界必须行级切分（前段归前章，后段归新章）；p43 第五章标题 OCR 跨行
  （行8 '第五章宗教改革运动和' 切章 + 行9 '反宗教改革运动' 页内剥）。
页码噪声: 每页 2 个数字行（正确书内页码 '40'/'253' + 页边 OCR 误读怪串
  '544-'/'746'/'801='/'-857'/'774-' 等，格式同为 装饰线+2-4位数字），
  正则 ^[—\-一=\s]*\d{1,4}[—\-一=\s]*$ 任意位置剥整行
页眉: 偶页=卷名'卷三近代哲学'（变体'卷三近代暂学' p339）、奇页=篇名
  （'第一篇从文艺复兴到休X'/'第二篇从卢X到现X'，OCR 变体极多
  '卢楼/户梭/到现在/到代' 等——正则前缀 ^第[一二三四五六七八九十]{1,2}篇.{0,10}$ 剥）；
  p6 双页眉（卷名+篇名）；p216 第二篇起始页页首=篇名（无页码）
索引区页眉: 人物/神话索引='索引'残字单行（'引'/'索'/'案'/'紫'/'素'/'崇'/'务'/
  '多'/'引1'，页首 1-2 行循环剥）；术语索引='术语索引'/'术语索引1'/'大语索引'
  （'术'→'大' OCR 变体）+前言页残字'术语'
标题: 章起始页标题由行级切分剥（正则 ^第[一二三四五六七八九十]{1,3}章.{0,15}$
  含变体'第九章：笛卡尔'/'第二十六章功利主义者?'；'二十二'等3字章号；
  '意'代'章'变体 ^第二十[一二三四五六七八九十]{1,2}意.{0,10}$）；
  索引标题行 p401'人物索引'/p464'神话、文学作品人物索引' 页内剥+固定切章；
  p20 藏书章'中央社会主义学院'页内剥
修复: 重建 34 章（31 正文 + 3 索引）；段落: 每页过滤后行拼接为一段（OCR 书范式），
  跨章页按标题行拆为前后两段。
用法: python _xr_f8d52df0f555_russell_rebuild.py [--dry]
"""
import json, os, re, sys, shutil, time

BID = "f8d52df0f555"
CKPT = r"f:\program\Python\PhiAgent\backend\data\dp_pdf_import_ckpt.json"
SAFE = "西方_伯特兰_罗素_西方哲学史_下卷_.pdf"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
# ⚠ 2026-08-08 事故修正：前端本地 dev 读 app/public/backend/data/book_chapters，必须双写
DST2 = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

def norm(s):
    return re.sub(r"\s+", "", s or "")

# 34 章: 31 正文（行级切分）+ 3 索引（固定页）
CH_TITLES = [
    "第一章总说", "第二章意大利文艺复兴", "第三章马基雅弗利",
    "第四章埃拉斯摩和莫尔", "第五章宗教改革运动和反宗教改革运动",
    "第六章科学的兴盛", "第七章弗兰西斯·培根", "第八章霍布士的利维坦",
    "第九章笛卡尔", "第十章斯宾诺莎", "第十一章莱布尼兹",
    "第十二章哲学上的自由主义", "第十三章洛克的认识论",
    "第十四章洛克的政治哲学", "第十五章洛克的影响", "第十六章贝克莱",
    "第十七章休谟", "第十八章浪漫主义运动", "第十九章卢梭", "第二十章康德",
    "第二十一章十九世纪思潮", "第二十二章黑格尔", "第二十三章拜伦",
    "第二十四章叔本华", "第二十五章尼采", "第二十六章功利主义者",
    "第二十七章卡尔·马克思", "第二十八章柏格森", "第二十九章威廉·詹姆士",
    "第三十章约翰·杜威", "第三十一章逻辑分析哲学",
    "人物索引", "神话、文学作品人物索引", "术语索引",
]
N = len(CH_TITLES)
SKIP_PAGES = set(range(0, 6))   # 封面/CIP/版权 p0-3 + 目录 p4-5
# 页级章边界: 索引起始页（页首标题/残字剥后该页正文归新章）
PAGE_START = {401: 31, 464: 32, 472: 33}
# 页眉（页首第一行精确匹配；'术语'=术语索引前言页残字页眉）
HEADERS = {
    "术语", "术语索引", "术语索引1", "大语索引",   # 术语索引页眉（'术'→'大'）
}
# 索引区残字页眉（'索引'/'索' 单字 OCR 拆行，页首循环剥）
RESIDUE = {"引", "索", "案", "紫", "素", "崇", "务", "多", "引1"}
# 卷名页眉（偶页；'哲'→'暂'/'智' OCR 变体）
VOL_RE = re.compile(r"^卷三近代.{0,2}$")
# 篇名页眉（奇页；OCR 变体极多——前缀+短行限制）
PART_RE = re.compile(r"^第[一二三四五六七八九十]{1,2}篇.{0,10}$")
# 节标题行（第十四章 5 节 + 第二十章 3 节；行首独立行，
#   p246 '第一节德国唯心论一般' 标题行尾粘连正文词'一般'——前缀剥保留残词）
SEC_RE = re.compile(r"^第[一二三四五六七八九十]+节[:：]?")
SEC_NAMES = ["世袭主义", "自然状态与自然法", "社会契约", "财产", "约制与均衡说",
             "德国唯心论", "康德哲学大意", "康德的空间和时间理论"]

def strip_sec(ls):
    out = []
    for l in ls:
        if not SEC_RE.match(l):
            out.append(l)
            continue
        rest = SEC_RE.sub("", l)
        keep = None
        for s in SEC_NAMES:
            if rest == s:
                keep = ""                    # 纯标题行 → 整行剥
                break
            if rest.startswith(s) and 0 < len(rest) - len(s) <= 3:
                keep = rest[len(s):]         # 标题+正文残词（p246 '一般'）→ 保留残词
                break
        if keep is None:
            out.append(l)                    # 非节标题（正文引用）→ 保留
        elif keep:
            out.append(keep)
    return out
# 章标题行（页内任意位置；'二十二'等 3 字章号；'？'/'：' 变体在标题内）
CH_RE = re.compile(r"^第[一二三四五六七八九十]{1,3}章.{0,15}$")
CH_RE2 = re.compile(r"^第二十[一二三四五六七八九十]{1,2}意.{0,10}$")   # '意'代'章'（p266）
# 页内标题行/噪声（任意行精确匹配剔除）
STRIP_PAGES = {
    20: ["中央社会主义学院"],        # p20 藏书章 OCR
    43: ["反宗教改革运动"],          # p43 第五章标题跨行残段（标题行由 CH_RE 切章剥）
    401: ["人物索引"],
    464: ["神话、文学作品人物索引"],
}
# 页码行（书内页码 + 页边误读怪串，均带装饰线）
PAGE_RE = re.compile(r"^[—\-一=\s]*\d{1,4}[—\-一=\s]*$")

# checkpoint 读重试（OCR 队列并发写 → 瞬时截断）
ckpt = None
for _try in range(5):
    try:
        ckpt = json.load(open(CKPT, encoding="utf-8"))
        break
    except json.JSONDecodeError:
        time.sleep(2)
if ckpt is None:
    sys.exit("checkpoint 连续 5 次读失败，OCR 队列可能正在写入，稍后重试")
pages = ckpt["ocr"][SAFE]
npages = {int(k): v for k, v in pages.items() if v and v != "__FAILED__"}
fails = sorted([int(k) for k, v in pages.items() if v == "__FAILED__"])
print(f"OCR 页: {min(npages)}-{max(npages)} 共 {len(npages)} 页, fail {len(fails)} 页: {fails}")

def clean(i):
    """页 → 净化行（页码/页眉/残字/篇名/页内标题剥除; 章标题行保留作边界）"""
    t = npages.get(i, "")
    if not t:
        return []
    ls = [ln.strip() for ln in t.split("\n") if ln.strip()]
    ls = [l for l in ls if not PAGE_RE.match(l)]        # 页码行任意位置剥
    while ls and ls[0] in HEADERS:
        ls = ls[1:]                                     # 页眉（精确，循环）
    while ls and ls[0] in RESIDUE:
        ls = ls[1:]                                     # 索引残字页眉（循环）
    while ls and (VOL_RE.match(ls[0]) or PART_RE.match(ls[0])):
        ls = ls[1:]                                     # 卷名/篇名页眉（前缀+短行，p6 双页眉循环）
    if i in STRIP_PAGES:
        ls = [l for l in ls if l not in STRIP_PAGES[i]] # 页内标题行任意位置剔除
    ls = [l for l in ls if l != "I"]                    # 注释标记 OCR 残留（p113/p349）
    return strip_sec(ls)

# ---- 行级章节切分（章标题行 = 章边界） ----
paras = [[] for _ in range(N)]
cur = 0                                      # 当前章（0 第一章总说）
title_hits = 0
for i in sorted(npages):
    if i in SKIP_PAGES:
        continue
    ls = clean(i)
    if not ls:
        continue
    if i in PAGE_START:
        cur = PAGE_START[i]                  # 索引起始页固定切章
    # 找章标题行（每页至多一个）
    hit = [n for n, l in enumerate(ls) if CH_RE.match(l) or CH_RE2.match(l)]
    if hit:
        n = hit[-1]
        title_hits += 1
        pre = "".join(ls[:n])
        if pre:
            paras[cur].append(pre)           # 标题行前 → 当前章（前章尾）
        cur = title_hits - 1                 # 标题行开启的章 = 命中序-1
        if cur >= N:
            print(f"⚠ p{i} 标题行超出章数: {ls[n]!r}")
            cur = N - 1
        post = "".join(ls[n + 1:])
        if post:
            paras[cur].append(post)          # 标题行后 → 本章正文
    else:
        paras[cur].append("".join(ls))
print(f"章标题行命中: {title_hits}（应为 31）")

files = {}
for idx in range(N):
    if not paras[idx]:
        print(f"⚠ 章{idx} {CH_TITLES[idx]!r}: 无内容")
    files[idx] = {"index": idx, "title": CH_TITLES[idx],
                  "content": [{"type": "text", "value": p} for p in paras[idx]]}
    nc = sum(len(norm(p)) for p in paras[idx])
    first = paras[idx][0][:36] if paras[idx] else "(空)"
    last = paras[idx][-1][:22] if paras[idx] else ""
    print(f"[{idx}] {CH_TITLES[idx]:<34s} {nc:6d}字 {len(paras[idx]):3d}段 | {first!r} … {last!r}")
assert len(files) == N

# ---- 验证 ----
total = sum(sum(len(norm(b["value"])) for b in files[idx]["content"]) for idx in range(N))
print(f"\n新总净: {total}")
all_text = "".join(norm(b["value"]) for idx in range(N) for b in files[idx]["content"])
# 页码粘连清零: 段首不得以'汉字+2-3数字'粘连开头（学术注释中的书目页码保留段中/段尾）
bad_page = [norm(b["value"])[:8] for idx in range(N) for b in files[idx]["content"]
            if re.match(r"[一-鿿]\d{2,3}", norm(b["value"]))
            and not re.match(r"图\d{2,3}", norm(b["value"]))
            and not re.search(r"\d{2,3}岁", norm(b["value"]))
            and not re.search(r"\d{2,4}年", norm(b["value"])[:12])]   # '从1933年①以' 为年份正文
print("页码粘连清零:", "✓" if not bad_page else f"✗ {bad_page[:6]}")
# 独立页码行清零: 段不得整体为纯数字
bad_s = [norm(b["value"]) for idx in range(N) for b in files[idx]["content"]
         if re.match(r"^[—\-一=\s]*\d{1,4}[—\-一=\s]*$", norm(b["value"]))]
print("独立页码清零:", "✓" if not bad_s else f"✗ {bad_s[:5]}")
# 页眉/标题清零: 段首不得为章标题/篇名/卷名/残字（正文引用'第一章'在段中不误报）
bad_h = [f"章{idx}:{norm(b['value'])[:14]}" for idx in range(N) for b in files[idx]["content"]
         if CH_RE.match(norm(b["value"])) or CH_RE2.match(norm(b["value"]))
         or PART_RE.match(norm(b["value"])) or VOL_RE.match(norm(b["value"]))
         or norm(b["value"]) in {norm(h) for h in HEADERS} | RESIDUE
         or norm(b["value"]) in {norm(x) for v in STRIP_PAGES.values() for x in v}]
print("标题清零:", "✓" if not bad_h else f"✗ {bad_h[:6]}")
# 节标题清零: 段首不得为'第X节'（正文引用'第一节'在段中）
bad_sec = [f"章{idx}:{norm(b['value'])[:12]}" for idx in range(31) for b in files[idx]["content"]
           if SEC_RE.match(norm(b["value"]))]
print("节标题清零:", "✓" if not bad_sec else f"✗ {bad_sec[:5]}")
# 英文残留: 段内英文字符占比过高（仅正文 31 章；索引有 'A'/'B' 分区行跳过）
bad_en = [f"章{idx}段{n}" for idx in range(31) for n, b in enumerate(files[idx]["content"])
          if len(re.findall(r"[A-Za-z]", b["value"])) > len(b["value"]) * 0.4]
print("英文残留(正文):", "✓" if not bad_en else f"✗ {bad_en[:5]}")
# 关键内容验证
ch = {idx: "".join(norm(b["value"]) for b in files[idx]["content"]) for idx in range(N)}
checks = [
    (0, "第一章", "世俗"), (1, "第二章", "文艺复兴"), (2, "第三章", "马基雅弗利"),
    (3, "第四章", "乌托邦"), (4, "第五章", "宗教改革运动"), (5, "第六章", "哥白尼"),
    (6, "第七章", "培根"), (7, "第八章", "利维坦"), (8, "第九章", "笛卡尔"),
    (9, "第十章", "斯宾诺莎"), (10, "第十一章", "莱布尼兹"), (11, "第十二章", "自由主义"),
    (12, "第十三章", "认识论"), (13, "第十四章", "政治哲学"), (14, "第十五章", "洛克"),
    (15, "第十六章", "贝克莱"), (16, "第十七章", "休谟"), (17, "第十八章", "浪漫主义"),
    (18, "第十九章", "卢梭"), (19, "第二十章", "康德"), (20, "第二十一章", "费希特"),
    (21, "第二十二章", "黑格尔"), (22, "第二十三章", "拜伦"), (23, "第二十四章", "叔本华"),
    (24, "第二十五章", "尼采"), (25, "第二十六章", "功利"), (26, "第二十七章", "马克思"),
    (27, "第二十八章", "柏格森"), (28, "第二十九章", "詹姆士"), (29, "第三十章", "杜威"),
    (30, "第三十一章", "逻辑"), (31, "人物索引", "亚里士多德"),
    (32, "神话索引", "宙斯"), (33, "术语索引", "本体"),
]
print("验证:", "  ".join(f"{'✓'+t if kw in ch[i] else '✗'+t+'!'}" for i, t, kw in checks))

# ---- toc ----
toc = [{"type": "chapter", "title": files[i]["title"], "index": i, "level": 1} for i in range(N)]
print(f"\ntoc 项: {len(toc)}")

if "--dry" in sys.argv:
    sys.exit(0)

# ---- 写入（旧 78 章自动数据 → 备份 _old_bad） ----
if os.path.isdir(SRC):
    suf = "_old_bad"
    i2 = 2
    while os.path.isdir(SRC + suf):
        suf = f"_old_bad{i2}"
        i2 += 1
    os.rename(SRC, SRC + suf)
    print(f"\n备份旧数据 → {os.path.basename(SRC) + suf}")
os.makedirs(SRC)
for idx in range(N):
    f = files[idx]
    json.dump({"index": idx, "title": f["title"], "content": f["content"]},
              open(os.path.join(SRC, f"{idx}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
meta = {
    "bookId": BID, "title": "西方哲学史（下卷）", "author": "伯特兰·罗素",
    "toc": toc, "cover": None, "chapterCount": N,
    "chapterTitles": [files[i]["title"] for i in range(N)],
}
json.dump(meta, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print(f"✓ 写入 {SRC}: {N} 章 + meta.json")

shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
print("✓ 同步 DP backend chapters")
shutil.rmtree(DST2, ignore_errors=True)
shutil.copytree(SRC, DST2)
print("✓ 同步 DP app/public chapters（前端 dev 实际读取路径）")

for p in (DETAIL_SRC, DETAIL_DST):
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))
        d["toc"] = toc
        d["chapterCount"] = N
        d["chapterTitles"] = meta["chapterTitles"]
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
        print(f"✓ book_detail 更新: {p}")

if os.path.exists(BOOKS_JSON):
    bj = json.load(open(BOOKS_JSON, encoding="utf-8"))
    bl = bj if isinstance(bj, list) else bj.get("books", [])
    hit = False
    for b in bl:
        if b.get("id") == BID:
            b["chapterCount"] = N
            hit = True
    if hit:
        with open(BOOKS_JSON, "w", encoding="utf-8") as f:
            json.dump(bl if isinstance(bj, list) else {**bj, "books": bl}, f,
                      ensure_ascii=False, indent=None)
        print("✓ books.json chapterCount 更新")
    else:
        print("⚠ books.json 未找到该书")
