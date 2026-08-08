# -*- coding: utf-8 -*-
"""#257 宗教经验种种（469fc9745e43，威廉·詹姆斯）重建
病因: 已OCR未入清单补录书（CHKLIST 无此条）。旧 6 章为 dp_pdf_import 自动切章
  （序言/后记/一、二、三（译者导言小节）——切章错乱，无页码清理）。
源: F:/philosophy/西方/威廉·詹姆斯/宗教经验种种.pdf（443 页扫描版，
  刘小枫主编'西方传统经典与解释'丛书（人民大学出版社？），checkpoint OCR 443 页 fail 1: p14）
结构（目录 p5-10；中译者导言独立编页 1-28，正文书内页码=PDF页-42）:
  p0-2 丛书页（跳过）｜ p3-4 缘起（p3 标题+正文同页）
  p5-10 目录（跳过）｜ p11-12 序言（p11 页首'XV'罗马页码独立行）
  p13-14 鸣谢（p13 标题+正文；⚠ p14 fail——鸣谢尾部缺失，待补 OCR）
  p15-42 中译者导言（页眉'中译者导言N'/'导盲N'变体，独立编页）
  正文 16 讲: 第一讲宗教与神经病学 p43（书内1）/第二讲论题的范围 p61（19）/
    第三讲看不见的实在 p81（39）/第四、五讲健康心灵的宗教 p99（57）/
    第六、七讲病态的灵魂 p135（93）/第八讲分裂的自我及其统一过程 p162（120）/
    第九讲皈依 p179（137）/第十讲皈依（结论） p199（157）/
    第十一、十二、十三讲圣徒性 p229（187）/第十四、十五讲圣徒性的价值 p279（237）/
    第十六、十七讲神秘主义 p313（271）/第十八讲哲学 p354（312；p353 书内311
    页眉滞后仍印'第十六、十七讲'，归第十七讲）/
    第十九讲其他特性 p375（333）/第二十讲结论 p396（354）
  尾: 后记 p421-426（书内379-384）/索引 p427-441（385-399，词条含原书页码
    原样保留）/p442 封底（'定价：39.00元'，跳过）
⚠ 页码不独立成行——粘连在页眉行首/行尾: 偶页='N宗教经验种种'
  （'宗数'/'案教' OCR 变体）、奇页='讲名N'/'后记N'/'索引N'/'中译者导言N'，
  页眉整行剥（HEAD_RE/EVEN_RE）；p11 'XV' 罗马页码独立行（ROMAN_RE 剥）。
标题: 每讲起始页=页眉（'讲名N'）+标题行（'讲名' 无页码，页首第 2 行）
  按页精确剥；OCR 变体 '第十八讲哲：学'（p354）/'第二十讲结、论'（p396）；
  页眉与标题 '健康心灵的宗教'（p99，正文用词；目录'健全'仅目录页不影响）
修复: 重建 20 章（缘起/序言/鸣谢/中译者导言+16讲+后记/索引）；
  段落: 每页过滤后行拼接为一段（OCR 书范式）。
用法: python _xr_469fc9745e43_religion_rebuild.py [--dry]
"""
import json, os, re, sys, shutil, time

BID = "469fc9745e43"
CKPT = r"f:\program\Python\PhiAgent\backend\data\dp_pdf_import_ckpt.json"
SAFE = "西方_威廉_詹姆斯_宗教经验种种.pdf"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
# ⚠ 2026-08-08 事故修正：前端本地 dev 读 app/public/backend/data/book_chapters，必须双写
DST2 = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

def norm(s):
    return re.sub(r"\s+", "", s or "")

# 20 章: (idx, 标题)
CH_TITLES = [
    "缘起", "序言", "鸣谢", "中译者导言",
    "第一讲宗教与神经病学", "第二讲论题的范围", "第三讲看不见的实在",
    "第四、五讲健康心灵的宗教", "第六、七讲病态的灵魂",
    "第八讲分裂的自我及其统一过程", "第九讲皈依", "第十讲皈依（结论）",
    "第十一、十二、十三讲圣徒性", "第十四、十五讲圣徒性的价值",
    "第十六、十七讲神秘主义", "第十八讲哲学", "第十九讲其他特性",
    "第二十讲结论", "后记", "索引",
]
N = len(CH_TITLES)
SKIP_PAGES = set(range(0, 3)) | set(range(5, 11)) | {442}   # 丛书页 + 目录 + 封底
# 页级章边界: 起始页（页眉+标题剥后该页正文归新章）
PAGE_START = {3: 0, 11: 1, 13: 2, 15: 3, 43: 4, 61: 5, 81: 6, 99: 7, 135: 8,
              162: 9, 179: 10, 199: 11, 229: 12, 279: 13, 313: 14, 354: 15,
              375: 16, 396: 17, 421: 18, 426: 19}   # ⚠ 索引实际从 p426 起始（'索引' 标题+说明+A 词条），非 p427
# 标题行（每讲起始页页眉后第 1 行，按页精确剥离）
STRIP_PAGES = {
    3: ["缘起"], 11: ["序言", "XV"], 13: ["鸣谢"], 15: ["中译者导言"],
    43: ["第一讲宗教与神经病学"], 61: ["第二讲论题的范围"],
    81: ["第三讲看不见的实在"], 99: ["第四、五讲健康心灵的宗教"],
    135: ["第六、七讲病态的灵魂"], 162: ["第八讲分裂的自我及其统一过程"],
    179: ["第九讲皈依"], 199: ["第十讲皈依（结论）"],
    229: ["第十一、十二、十三讲圣徒性"], 279: ["第十四、十五讲圣徒性的价值"],
    313: ["第十六、十七讲神秘主义"], 354: ["第十八讲哲：学"],   # '哲学' 中插冒号
    375: ["第十九讲其他特性"], 396: ["第二十讲结、论"],         # '结论' 中插逗号
    421: ["后记"],
    426: ["索引"],   # 索引标题行（p426 页眉 '384宗教经验种种' EVEN_RE 剥后露出）
}
# 页眉（页首第一行循环剥）:
# 奇页页眉 = '讲名N'/'后记N'/'索引N'/'中译者导言N'（页码粘连行尾）
HEAD_RE = re.compile(r"^(第[^，。]{1,20}讲|后记|索引|中译者导[言盲])[^，。]{0,14}\d{1,3}$")
# 偶页页眉 = 'N宗教经验种种'（页码粘连行首；'宗教'→'宗数'/'案教' 变体）
EVEN_RE = re.compile(r"^\d{1,3}[^，。]{0,4}经验种种$")
# 序言罗马页码独立行（p11 'XV'）
ROMAN_RE = re.compile(r"^[IVXLCivxlc]+$")
# 页码行（兜底: 独立数字行）
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
print(f"⚠ 待补 OCR 页（本重建后提醒用户）: {fails}")

def clean(i):
    """页 → 净化行（页眉/标题剥除后）"""
    t = npages.get(i, "")
    if not t:
        return []
    ls = [ln.strip() for ln in t.split("\n") if ln.strip()]
    ls = [l for l in ls if not PAGE_RE.match(l)]        # 独立数字行兜底
    while ls and (HEAD_RE.match(ls[0]) or EVEN_RE.match(ls[0]) or ROMAN_RE.match(ls[0])):
        ls = ls[1:]                                     # 页眉（页码粘连同行，整行剥）
    if i in STRIP_PAGES:
        ls = [l for l in ls if l not in STRIP_PAGES[i]] # 标题行任意位置精确剔除
    return ls

# ---- 逐章解析（页级段落范式 + 固定切章页） ----
files = {}
cur = 0
paras = [[] for _ in range(N)]
for i in sorted(npages):
    if i in SKIP_PAGES:
        continue
    if i in PAGE_START:
        cur = PAGE_START[i]
    ls = clean(i)
    if not ls:
        continue
    paras[cur].append("".join(ls))
for idx in range(N):
    if not paras[idx]:
        print(f"⚠ 章{idx} {CH_TITLES[idx]!r}: 无内容")
    files[idx] = {"index": idx, "title": CH_TITLES[idx],
                  "content": [{"type": "text", "value": p} for p in paras[idx]]}
    nc = sum(len(norm(p)) for p in paras[idx])
    first = paras[idx][0][:36] if paras[idx] else "(空)"
    last = paras[idx][-1][:22] if paras[idx] else ""
    print(f"[{idx}] {CH_TITLES[idx]:<26s} {nc:6d}字 {len(paras[idx]):3d}段 | {first!r} … {last!r}")
assert len(files) == N

# ---- 验证 ----
total = sum(sum(len(norm(b["value"])) for b in files[idx]["content"]) for idx in range(N))
print(f"\n新总净: {total}")
all_text = "".join(norm(b["value"]) for idx in range(N) for b in files[idx]["content"])
# 页码粘连清零: 段首不得以'汉字+2-3数字'粘连开头（索引词条页码在段中不误报）
bad_page = [norm(b["value"])[:8] for idx in range(N) for b in files[idx]["content"]
            if re.match(r"[一-鿿]\d{2,3}", norm(b["value"]))
            and not re.match(r"图\d{2,3}", norm(b["value"]))
            and not re.search(r"\d{2,3}岁", norm(b["value"]))
            and not re.search(r"\d{2,4}年", norm(b["value"])[:12])]
print("页码粘连清零:", "✓" if not bad_page else f"✗ {bad_page[:6]}")
# 独立页码行清零
bad_s = [norm(b["value"]) for idx in range(N) for b in files[idx]["content"]
         if re.match(r"^[—\-一=\s]*\d{1,4}[—\-一=\s]*$", norm(b["value"]))]
print("独立页码清零:", "✓" if not bad_s else f"✗ {bad_s[:5]}")
# 页眉/标题清零: 段首不得为页眉行/标题行
bad_h = [f"章{idx}:{norm(b['value'])[:16]}" for idx in range(N) for b in files[idx]["content"]
         if HEAD_RE.match(norm(b["value"])) or EVEN_RE.match(norm(b["value"]))
         or norm(b["value"]) in {norm(x) for v in STRIP_PAGES.values() for x in v}]
print("标题清零:", "✓" if not bad_h else f"✗ {bad_h[:6]}")
# 英文残留: 段内英文字符占比过高（正文 18 章（0-17）；后记 p425 注释含英文书名
# 误报、索引词条含英文——均跳过）
bad_en = [f"章{idx}段{n}" for idx in range(18) for n, b in enumerate(files[idx]["content"])
          if len(re.findall(r"[A-Za-z]", b["value"])) > len(b["value"]) * 0.4]
print("英文残留(正文):", "✓" if not bad_en else f"✗ {bad_en[:5]}")
# 关键内容验证（'临在感'/'片断超自然主义' 仅出现在目录页 p6/p10——已跳过，
# 正文用词替换: 第三讲='宗教生活'（首段）、后记='超自然主义'（主题词））
ch = {idx: "".join(norm(b["value"]) for b in files[idx]["content"]) for idx in range(N)}
checks = [
    (0, "缘起", "严复"), (1, "序言", "吉福德"), (2, "鸣谢", "翻译"),
    (3, "中译者导言", "斯密"), (4, "第一讲", "神经病态"), (5, "第二讲", "神圣"),
    (6, "第三讲", "宗教生活"), (7, "第四五讲", "惠特曼"), (8, "第六七讲", "托尔斯泰"),
    (9, "第八讲", "人格"), (10, "第九讲", "皈依"), (11, "第十讲", "潜意识"),
    (12, "十一~十三讲", "圣徒性"), (13, "十四十五讲", "苦行"),
    (14, "十六七讲", "神秘主义"), (15, "第十八讲", "实用主义"),
    (16, "第十九讲", "祈祷"), (17, "第二十讲", "宗教科学"),
    (18, "后记", "超自然主义"), (19, "索引", "佛教"),
]
print("验证:", "  ".join(f"{'✓'+t if kw in ch[i] else '✗'+t+'!'}" for i, t, kw in checks))

# ---- toc ----
toc = [{"type": "chapter", "title": files[i]["title"], "index": i, "level": 1} for i in range(N)]
print(f"\ntoc 项: {len(toc)}")

if "--dry" in sys.argv:
    sys.exit(0)

# ---- 写入（旧 6 章自动数据 → 备份 _old_bad） ----
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
    "bookId": BID, "title": "宗教经验种种", "author": "威廉·詹姆斯",
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
