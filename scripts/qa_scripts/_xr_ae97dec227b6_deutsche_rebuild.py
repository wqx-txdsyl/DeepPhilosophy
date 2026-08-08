# -*- coding: utf-8 -*-
"""#258 德意志意识形态（节选本）（ae97dec227b6，马克思/恩格斯）重建
病因: 已OCR未入清单补录书（CHKLIST 无此条）。旧 10 章为 dp_pdf_import 自动切章
  （toc 乱取: '第1部分第5卷…'/'第182节…' 等正文句被当章名）。
源: F:/philosophy/西方/卡尔·马克思/德意志意识形态_节选本_.pdf（168 页扫描版，
  人民出版社 2018 纪念马克思诞辰 200 周年《马克思恩格斯著作特辑》，
  checkpoint OCR 168 页 fail 1: p25（书名页后空白/版权页，无损失））
结构（书内页码 = PDF页-23；前言区罗马编页）:
  p0-2 特辑封面/CIP/版权（跳过）｜ p3-5 编辑说明（p3 标题+正文，p5 署名 2018年2月）
  p6-21 编者引言（p6 标题+正文；双页眉 偶='编者引言'/奇='德意志意识形态（节选本）'）
  p22 摘编目次页（19 小节列表，跳过）｜ p23 全书目录（跳过）
  p24 书名页（跳过）｜ p25 FAIL（书内 2 空白/版权页，跳过）
  p26 第一卷标题页+序言（'第一卷/对费尔巴哈…/所代表的现代德国哲学的批判/序言'+正文）
  p27 序言续｜ p28 第一卷序言（标题+正文）｜ p29 第一章标题页
    （'第一章/费尔巴哈/唯物主义观点和唯心主义观点的对立/[1]'+正文）
  p30-105 第一章费尔巴哈正文（双页眉 偶='第一卷第一章费尔巴哈'/奇='德意志意识形态（节选本）'，
    p105 尾出处注 '卡·马克思和弗·恩格斯写于 1845年秋—1846年5月…'）
  p106-151 第一卷和第二卷重要论述摘编（双页眉 偶='第一卷和第二卷重要论述摘编'/
    奇='德意志意识形态（节选本）'；19 小节：6 节标题在页首（106/113/118/125/126/142）、
    13 节标题嵌页内正文流（行级切分点 109/114/115/119/122/132/134/138/139/145/147/149/150，
    119/138/145/149 为双行标题；每节标题前/正文段间有编者来源注
    '（《马克思恩格斯全集》中文第1版第3卷第NNN页）' 单行或跨行两行——剥除）
  p152-159 注释（页眉 '注释'/'注 释' 变体；p152 起始页）｜ p160-166 人名索引
    （页眉 '人名索引'；p160 'A'/'p166 'T' 字母分组行保留）｜ p167 封底（跳过）
页码: 独立行带 '·' 装饰（'·3'/'·5·'/'·82·'/'·83。'/'·109·'/'·124?'/'·127'/'·128。'，
  '·' 偶被 OCR 成 '?'/'。'）——PAGE_RE 含 '·?。' 字符类任意位置剥
标题: 非摘编区标题页按页 STRIP（p3/p26/p28/p29）；摘编区 19 节标题统一行级切分
  （ONE_LINE_TITLES/TWO_LINE_TITLES 精确匹配，命中序 → 章 5..23）
修复: 重建 26 章；段落: 每页过滤后行拼接为一段（OCR 书范式）。
用法: python _xr_ae97dec227b6_deutsche_rebuild.py [--dry]
"""
import json, os, re, sys, shutil, time

BID = "ae97dec227b6"
CKPT = r"f:\program\Python\PhiAgent\backend\data\dp_pdf_import_ckpt.json"
SAFE = "西方_卡尔_马克思_德意志意识形态_节选本_.pdf"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
# ⚠ 2026-08-08 事故修正：前端本地 dev 读 app/public/backend/data/book_chapters，必须双写
DST2 = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

def norm(s):
    return re.sub(r"\s+", "", s or "")

# 26 章: (idx, 标题)
CH_TITLES = [
    "编辑说明", "编者引言", "序言", "第一卷序言", "第一章费尔巴哈",
    # 摘编 19 小节（目次用词）
    "青年黑格尔派的唯心主义历史观", "“真正的社会主义”",
    "空想共产主义的社会现实基础", "私有制与生产力的发展", "生产和消费的关系",
    "生产力发展水平对自由的制约", "私人利益与共同利益相互对立和统一的物质根源",
    "法律是统治阶级意志的表现", "资产阶级与国家", "资产阶级功利论",
    "资产阶级享乐哲学", "德国市民等级的历史及其典型特征",
    "共产主义是用实践手段来追求实践目标的最具有实践性的运动",
    "共产主义与消灭私有制", "共产主义与人的自由全面的发展",
    "共产主义的社会组织将消除由旧的分工造成的弊端", "无产者的阶级地位和历史使命",
    "在革命活动中无产者改变自身和改变环境是同步的",
    "思想和语言都只是现实生活的表现", "注释", "人名索引",
]
N = len(CH_TITLES)
SKIP_PAGES = {0, 1, 2, 22, 23, 24, 25, 167}   # 特辑页 + 摘编目次 + 全书目录 + 书名页 + fail页 + 封底
# 非摘编区页级章边界（标题行剥后该页正文归新章）
PAGE_START = {3: 0, 6: 1, 26: 2, 28: 3, 29: 4, 152: 24, 160: 25}
# 非摘编区标题页标题行（按页精确剥离）
STRIP_PAGES = {
    3: ["编辑说明"],
    26: ["第一卷", "对费尔巴哈、布·鲍威尔和施蒂纳", "所代表的现代德国哲学的批判", "序言"],
    28: ["第一卷序言"],
    29: ["第一章", "费尔巴哈", "唯物主义观点和唯心主义观点的对立", "[1]"],
}
# 页眉（页首第一行循环剥）: 双页眉系统 + 注释/索引区
HEADERS = {
    "德意志意识形态（节选本）",          # 奇页书名页眉
    "编者引言",                          # 编者引言区偶页页眉（p6 标题同串）
    "第一卷第一章费尔巴哈",              # 第一章区偶页页眉
    "第一卷和第二卷重要论述摘编",        # 摘编区偶页页眉
    "注释", "注 释",                     # 注释区（'注 释' OCR 变体 p154/p158）
    "人名索引",                          # 索引区（p160 标题同串）
}
# 摘编区行级切章标题（页内任意位置精确匹配；页首标题也在其中，统一行级切分）
# 单行标题
ONE_LINE_TITLES = {
    109: "“真正的社会主义”",
    113: "空想共产主义的社会现实基础",
    114: "私有制与生产力的发展",
    115: "生产和消费的关系",
    118: "生产力发展水平对自由的制约",
    122: "法律是统治阶级意志的表现",
    125: "资产阶级与国家",
    126: "资产阶级功利论",
    132: "资产阶级享乐哲学",
    134: "德国市民等级的历史及其典型特征",
    139: "共产主义与消灭私有制",
    142: "共产主义与人的自由全面的发展",
    147: "无产者的阶级地位和历史使命",
    150: "思想和语言都只是现实生活的表现",
}
# 双行标题（连续两行）
TWO_LINE_TITLES = {
    106: ("青年黑格尔派的", "唯心主义历史观"),
    119: ("私人利益与共同利益", "相互对立和统一的物质根源"),
    138: ("共产主义是用实践手段来追求", "实践目标的最具有实践性的运动"),
    145: ("共产主义的社会组织将消除", "由旧的分工造成的弊端"),
    149: ("在革命活动中无产者改变", "自身和改变环境是同步的"),
}
# 命中序 → 章号（19 个命中 → 章 5..23，按页序）
LINE_HIT_CH = list(range(5, 24))
# 编者来源注（摘编区每节标题前/正文段间）: 单行 '（《马克思恩格斯全集》中文第1版第3卷第234页）'
# 或跨行 '（…第331一' + '332页）'
SRC_ONE_RE = re.compile(r"^（《马克思恩格斯全集》中文第1版第3卷第\d+页）$")
SRC_L1_RE = re.compile(r"^（《马克思恩格斯全集》中文第1版第3卷第\d+[一\-－]\d*$")
SRC_L2_RE = re.compile(r"^\d+页）$")
# 页码行（带 '·'/'?'/'。' 装饰，任意位置）
PAGE_RE = re.compile(r"^[·?—\-一=\s。]*\d{1,4}[·?—\-一=\s。]*$")

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
print(f"⚠ 待补 OCR 页（p25=书名页后空白/版权页，跳过无损失）: {fails}")

def clean(i):
    """页 → 净化行（页眉/标题/来源注/页码剥除后）"""
    t = npages.get(i, "")
    if not t:
        return []
    ls = [ln.strip() for ln in t.split("\n") if ln.strip()]
    while ls and ls[0] in HEADERS:
        ls = ls[1:]                          # 页眉
    if i in STRIP_PAGES:
        ls = [l for l in ls if l not in STRIP_PAGES[i]]   # 标题行任意位置剔除
    out = []
    skip_next = False
    for l in ls:
        if skip_next:
            skip_next = False
            continue
        if PAGE_RE.match(l):
            continue
        if SRC_L1_RE.match(l):
            skip_next = True                 # 跨行来源注（第一行 + 下一行 'NNN页）'）
            continue
        if SRC_ONE_RE.match(l) or SRC_L2_RE.match(l):
            continue
        out.append(l)
    return out

# ---- 逐章解析（固定页 + 摘编区行级切分） ----
paras = [[] for _ in range(N)]
cur = 0
hit_count = 0
for i in sorted(npages):
    if i in SKIP_PAGES:
        continue
    if i in PAGE_START:
        cur = PAGE_START[i]
    ls = clean(i)
    if not ls:
        continue
    # 摘编区行级标题命中（该页至多一个；双行优先）
    n_hit, span = None, 0
    if i in TWO_LINE_TITLES:
        a, b = TWO_LINE_TITLES[i]
        for n in range(len(ls) - 1):
            if ls[n] == a and ls[n + 1] == b:
                n_hit, span = n, 2
                break
    if n_hit is None and i in ONE_LINE_TITLES:
        t = ONE_LINE_TITLES[i]
        for n, l in enumerate(ls):
            if l == t:
                n_hit, span = n, 1
                break
    if n_hit is not None:
        pre = "".join(ls[:n_hit])
        if pre:
            paras[cur].append(pre)           # 标题行前 → 当前章
        if hit_count >= len(LINE_HIT_CH):
            print(f"⚠ p{i} 标题命中超出 19 个: {ls[n_hit]!r}")
        else:
            cur = LINE_HIT_CH[hit_count]     # 标题行 → 切到新章
        hit_count += 1
        post = "".join(ls[n_hit + span:])
        if post:
            paras[cur].append(post)          # 标题行后 → 新章
    else:
        paras[cur].append("".join(ls))
if hit_count != 19:
    print(f"⚠⚠ 摘编标题命中数 {hit_count} != 19，章节错位风险！")

files = {}
for idx in range(N):
    if not paras[idx]:
        print(f"⚠ 章{idx} {CH_TITLES[idx]!r}: 无内容")
    files[idx] = {"index": idx, "title": CH_TITLES[idx],
                  "content": [{"type": "text", "value": p} for p in paras[idx]]}
    nc = sum(len(norm(p)) for p in paras[idx])
    first = paras[idx][0][:36] if paras[idx] else "(空)"
    last = paras[idx][-1][:22] if paras[idx] else ""
    print(f"[{idx}] {CH_TITLES[idx]:<36s} {nc:6d}字 {len(paras[idx]):3d}段 | {first!r} … {last!r}")
assert len(files) == N

# ---- 验证 ----
total = sum(sum(len(norm(b["value"])) for b in files[idx]["content"]) for idx in range(N))
print(f"\n新总净: {total}")
all_text = "".join(norm(b["value"]) for idx in range(N) for b in files[idx]["content"])
# 页码粘连清零: 段首不得以'汉字+2-3数字'粘连开头（'1845年' 等年份排除）
bad_page = [norm(b["value"])[:8] for idx in range(N) for b in files[idx]["content"]
            if re.match(r"[一-鿿]\d{2,3}", norm(b["value"]))
            and not re.match(r"图\d{2,3}", norm(b["value"]))
            and not re.search(r"\d{2,3}岁", norm(b["value"]))
            and not re.search(r"\d{2,4}年", norm(b["value"])[:12])
            and not re.search(r"第\d{1,4}页", norm(b["value"]))]   # '第277页：' 引用页码为正文
print("页码粘连清零:", "✓" if not bad_page else f"✗ {bad_page[:6]}")
# 独立页码行清零
bad_s = [norm(b["value"]) for idx in range(N) for b in files[idx]["content"]
         if re.match(r"^[·?—\-一=\s。]*\d{1,4}[·?—\-一=\s。]*$", norm(b["value"]))]
print("独立页码清零:", "✓" if not bad_s else f"✗ {bad_s[:5]}")
# 页眉/标题清零
bad_h = [f"章{idx}:{norm(b['value'])[:16]}" for idx in range(N) for b in files[idx]["content"]
         if norm(b["value"]) in {norm(h) for h in HEADERS}
         or norm(b["value"]) in {norm(x) for v in STRIP_PAGES.values() for x in v}
         or norm(b["value"]) in {norm(x) for x in ONE_LINE_TITLES.values()}
         or norm(b["value"]) in {norm(x) for p in TWO_LINE_TITLES.values() for x in p}
         or SRC_ONE_RE.match(norm(b["value"]))]
print("标题/来源注清零:", "✓" if not bad_h else f"✗ {bad_h[:6]}")
# 英文残留: 段内英文字符占比过高（正文 24 章（0-23）；注释/索引含英文跳过）
bad_en = [f"章{idx}段{n}" for idx in range(24) for n, b in enumerate(files[idx]["content"])
          if len(re.findall(r"[A-Za-z]", b["value"])) > len(b["value"]) * 0.4]
print("英文残留(正文):", "✓" if not bad_en else f"✗ {bad_en[:5]}")
# 关键内容验证
ch = {idx: "".join(norm(b["value"]) for b in files[idx]["content"]) for idx in range(N)}
checks = [
    (0, "编辑说明", "特辑"), (1, "编者引言", "意识形态"), (2, "序言", "虚假观念"),
    (3, "第一卷序言", "固定思想"), (4, "第一章", "意识形态家"),
    (5, "青年黑格尔派", "布鲁诺"), (6, "真正的社会主义", "自由主义"),
    (7, "空想共产主义", "体系"), (8, "私有制与生产力", "私有制"),
    (9, "生产和消费", "矛盾"), (10, "生产力发展水平", "桑乔本人"),
    (11, "私人利益", "阶级利益"), (12, "法律是统治", "理论家"),
    (13, "资产阶级与国家", "国家"), (14, "资产阶级功利论", "功利"),
    (15, "享乐哲学", "享乐"), (16, "德国市民等级", "康德"),
    (17, "共产主义是用实践", "施蒂纳"), (18, "共产主义与消灭私有制", "消灭"),
    (19, "人的自由全面发展", "自由"), (20, "社会组织", "劳动组织"),
    (21, "无产者", "需要"), (22, "革命活动", "改变"),
    (23, "思想和语言", "哲学幻想"), (24, "注释", "施特劳斯"), (25, "人名索引", "马克思"),
]
print("验证:", "  ".join(f"{'✓'+t if kw in ch[i] else '✗'+t+'!'}" for i, t, kw in checks))

# ---- toc ----
toc = [{"type": "chapter", "title": files[i]["title"], "index": i, "level": 1} for i in range(N)]
print(f"\ntoc 项: {len(toc)}")

if "--dry" in sys.argv:
    sys.exit(0)

# ---- 写入（旧 10 章自动数据 → 备份 _old_bad） ----
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
    "bookId": BID, "title": "德意志意识形态（节选本）", "author": "卡尔·马克思、弗里德里希·恩格斯",
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
