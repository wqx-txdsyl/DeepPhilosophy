# -*- coding: utf-8 -*-
"""#264 最伟大的思想家-奥古斯丁（215af36cac9f，[美]沙伦·M.凯、保罗·汤姆森著）重建
病因: 已OCR未入清单补录书。旧 3 章为 dp_pdf_import 自动切章（章标题取页眉残留
  '第11卷和《上帝之城》第9卷。'/'第2章，在奥古斯丁看来…'，正文乱分）。
源: F:/philosophy/西方/奥古斯丁/最伟大的思想家_-_奥古斯丁.pdf（140 页简体扫描版，
  中华书局《最伟大的思想家》丛书第 2 版 2014，周伟驰译，checkpoint OCR 140 页 fail 0）
结构（书内页码=PDF页-12）:
  p0-3 封面/CIP（跳过）｜ p4 简介（丛书版哲学家简介页）｜ p5-9 总序（赵敦华著，
    偶页页眉'最伟大的思想家'、奇页'总序'）｜ p10 丛书书目页（跳过）｜ p11 目录（跳过）
  p12 英文扉页（跳过）｜ 正文 6 章: 1导论(p13-24)/2神正论(p25-52)/3知识(p53-80)/
    4内在的人(p81-100)/5伦理和政治理论(p101-132)/6奥古斯丁的遗产(p133-135)
  p136-139 参考书目｜ p140 不存在（139 为末页）
页眉（正文区，循环剥首行）:
  偶页: 'On Augustine'/'OnAugustine' + '奥古斯丁'（英文+中文书名两行）
  奇页: 章节号（'1'-'6'）+ 章名（'导论'/'神正论'/'知识'/'内在的人'/'伦理和政治理论'/
    '奥古斯丁的遗产'/'参考书目'）两行
章标题页: 首行 'N章名' 粘连（'1导论'/'2神正论'/'3知识'/'4内在的人'/'5伦理和政治理论'/
  '6奥古斯丁的遗产'），剥后正文直接开始
页码: 部分页末行独立行（'12.3'=123/'001'/'00.5'/'W004' 变体），末行匹配剥
小节标题: 正文页首纯汉字短行（≤12字 无句读，'恶的问题'/'奥古斯丁的生平和时代'/
  '意志的发明？'）独立成段
修复: 重建 9 章 + toc 平铺；段落: 页级拼接（OCR 书范式）。
  作者修正（主线2）: '奥古斯丁' → '沙伦·M.凯、保罗·汤姆森'（封面'[美]沙伦·M.凯保罗·
  汤姆森著'+CIP'（美)凯，(美)汤姆森著' 双印证——传书作者=传记作者非哲学家本人）
用法: python _xr_215af36cac9f_augustine_rebuild.py [--dry]
"""
import json, os, re, sys, shutil, time

BID = "215af36cac9f"
CKPT = r"f:\program\Python\PhiAgent\backend\data\dp_pdf_import_ckpt.json"
SAFE = "西方_奥古斯丁_最伟大的思想家_-_奥古斯丁.pdf"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
# ⚠ 2026-08-08 事故修正：前端本地 dev 读 app/public/backend/data/book_chapters，必须双写
DST2 = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"
AUTHOR = "沙伦·M.凯、保罗·汤姆森"

def norm(s):
    return re.sub(r"\s+", "", s or "")

# 9 章
CH_TITLES = ["总序", "简介", "导论", "神正论", "知识",
             "内在的人", "伦理和政治理论", "奥古斯丁的遗产", "参考书目"]
N = len(CH_TITLES)
# 跳过: 封面/CIP/丛书书目页/目录/英文扉页
SKIP_PAGES = {0, 1, 2, 3, 10, 11, 12}
# 章起止 PDF 页（含起止）
CH_RANGE = [(5, 9), (4, 4), (13, 24), (25, 52), (53, 80),
            (81, 100), (101, 132), (133, 135), (136, 139)]
# 章名集合（页眉奇页第 2 行）
CH_NAMES = set(CH_TITLES[2:])
# 正文页眉（循环剥）: 偶页 'On Augustine'+'奥古斯丁' / 奇页 '章节号'+'章名'
HEAD_RE = re.compile(
    r"^(?:On ?Augustine|[1-6]|奥古斯丁|导论|神正论|知识|内在的人|伦理和政治理论|奥古斯丁的遗产|参考书目)$")
# 总序区页眉（p5-9）: 偶页 '最伟大的思想家' / 奇页 '总序'
FRONT_HEAD = re.compile(r"^(?:最伟大的思想家|总序)$")
# 章标题页粘连行: '1导论'/'2神正论'/'3知识'/'4内在的人'/'5伦理和政治理论'/'6奥古斯丁的遗产'
CHTITLE_RE = re.compile(r"^[1-6](导论|神正论|知识|内在的人|伦理和政治理论|奥古斯丁的遗产)$")
# 页码（部分页末行）: '001'/'00.5'/'W004'/'12.3' 变体
PAGE_RE = re.compile(r"^W?\d{1,3}\.?\d{1,2}$")
# 小节标题: 页首纯汉字短行（≤12字 无句读）
TITLE_RE = re.compile(r"^[\u4e00-\u9fff“”？！]{1,12}$")

ckpt = None
for _try in range(5):
    try:
        ckpt = json.load(open(CKPT, encoding="utf-8"))
        break
    except json.JSONDecodeError:
        time.sleep(2)
    except MemoryError:
        time.sleep(5)
if ckpt is None:
    sys.exit("checkpoint 连续 5 次读失败，OCR 队列可能正在写入，稍后重试")
pages = ckpt["ocr"][SAFE]
npages = {int(k): v for k, v in pages.items() if v and v != "__FAILED__"}
fails = sorted([int(k) for k, v in pages.items() if v == "__FAILED__"])
print(f"OCR 页: {min(npages)}-{max(npages)} 共 {len(npages)} 页, fail {len(fails)} 页: {fails}")

def clean(ls, head_re, strip=None, first_title=None):
    """行列表 → 段列表: 页眉循环剥 + 标题精确剔 + 末行页码剥 + 页首短标题独立段"""
    if strip:
        ls = [l for l in ls if l not in strip]
    while ls and head_re.match(ls[0]):
        ls = ls[1:]
    if first_title and ls and ls[0] == first_title:
        ls = ls[1:]
    if ls and PAGE_RE.match(ls[-1]):
        ls = ls[:-1]
    out, buf = [], []
    for j, l in enumerate(ls):
        if j == 0 and TITLE_RE.match(l):
            if buf:
                out.append("".join(buf)); buf = []
            out.append(l)
        else:
            buf.append(l)
    if buf:
        out.append("".join(buf))
    return out

paras = [[] for _ in range(N)]
for ci, (p0, p1) in enumerate(CH_RANGE):
    head_re = FRONT_HEAD if ci == 0 else HEAD_RE
    for i in range(p0, p1 + 1):
        if i not in npages:
            continue
        ls = [ln.strip() for ln in npages[i].split("\n") if ln.strip()]
        if ci == 0:
            strip = {"总序", "赵敦华"} if i == p0 else None
            paras[ci].extend(clean(ls, head_re, strip))
        elif ci == 1:
            # 简介页: 剥首行 '奥古斯丁' 标题
            paras[ci].extend(clean(ls, HEAD_RE, strip={"奥古斯丁"}))
        else:
            # 章标题页（CH_RANGE 起页）: 剥粘连行; 其余页剥页眉
            if i == p0 and ls and CHTITLE_RE.match(ls[0]):
                ls = ls[1:]
            elif i == p0 and ls[0] == CH_TITLES[ci]:
                ls = ls[1:]           # 容错: 章名单独成行
            paras[ci].extend(clean(ls, head_re))
    if not paras[ci]:
        print(f"⚠ 章{ci} {CH_TITLES[ci]!r}: 无内容")

files = {}
for idx in range(N):
    files[idx] = {"index": idx, "title": CH_TITLES[idx],
                  "content": [{"type": "text", "value": p} for p in paras[idx]]}
    nc = sum(len(norm(p)) for p in paras[idx])
    first = paras[idx][0][:36] if paras[idx] else "(空)"
    last = paras[idx][-1][:24] if paras[idx] else ""
    print(f"[{idx}] {CH_TITLES[idx]:<16s} {nc:6d}字 {len(paras[idx]):3d}段 | {first!r} … {last!r}")
assert len(files) == N

# ---- 验证 ----
total = sum(sum(len(norm(b["value"])) for b in files[idx]["content"]) for idx in range(N))
print(f"\n新总净: {total}")
all_text = "".join(norm(b["value"]) for idx in range(N) for b in files[idx]["content"])
# 页码粘连清零
bad_page = [norm(b["value"])[:8] for idx in range(N) for b in files[idx]["content"]
            if re.match(r"[一-鿿]\d{2,3}", norm(b["value"]))
            and not re.search(r"\d{2,4}年", norm(b["value"])[:12])
            and not re.search(r"\d{1,2}[:：]\d{1,2}", norm(b["value"]))]
print("页码粘连清零:", "✓" if not bad_page else f"✗ {bad_page[:6]}")
# 页眉残留（'On Augustine'/'奥古斯丁'/'最伟大的思想家' 独立段）
bad_h = [f"章{idx}:{b['value'][:14]}" for idx in range(N) for b in files[idx]["content"]
         if re.search(r"On ?Augustine|最伟大的思想家$", norm(b["value"]))]
print("页眉清零:", "✓" if not bad_h else f"✗ {bad_h[:6]}")
# 章标题页粘连行残留
bad_c = [f"章{idx}:{b['value'][:10]}" for idx in range(N) for b in files[idx]["content"]
         if CHTITLE_RE.match(b["value"])]
print("章标题残留:", "✓" if not bad_c else f"✗ {bad_c[:6]}")
# 关键内容验证
ch = {idx: "".join(norm(b["value"]) for b in files[idx]["content"]) for idx in range(N)}
checks = [
    (0, "总序", "贺麟"), (0, "总序", "蓝旗营"), (1, "简介", "加尔文主义"),
    (2, "导论", "希坡"), (2, "导论", "偷梨"), (2, "导论", "西塞罗"),
    (2, "导论", "奥古斯丁的生平和时代"), (2, "导论", "新柏拉图主义"),
    (3, "神正论", "theodicy"), (3, "神正论", "恶的问题"), (3, "神正论", "自由意志论和决定论"),
    (4, "知识", "怀疑主义"), (5, "内在的人", "记忆"), (6, "伦理和政治理论", "至善"),
    (7, "奥古斯丁的遗产", "修道院制"), (8, "参考书目", "拉丁文"),
]
print("验证:", "  ".join(f"{'✓'+t if kw in ch[i] else '✗'+t+'!'}" for i, t, kw in checks))

# ---- toc（9 chapter 平铺） ----
toc = [{"type": "chapter", "title": files[i]["title"], "index": i, "level": 1}
       for i in range(N)]
print(f"\ntoc 项: {len(toc)}")

if "--dry" in sys.argv:
    sys.exit(0)

# ---- 写入（旧 3 章自动数据 → 备份 _old_bad） ----
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
    "bookId": BID, "title": "最伟大的思想家 - 奥古斯丁", "author": AUTHOR,
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
        d["author"] = AUTHOR
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
        print(f"✓ book_detail 更新: {p}")

if os.path.exists(BOOKS_JSON):
    bj = json.load(open(BOOKS_JSON, encoding="utf-8"))
    bl = bj if isinstance(bj, list) else bj.get("books", [])
    hit = False
    for b in bl:
        if b.get("id") == BID:
            b["chapterCount"] = N
            if "author" in b:
                b["author"] = AUTHOR
            hit = True
    if hit:
        with open(BOOKS_JSON, "w", encoding="utf-8") as f:
            json.dump(bl if isinstance(bj, list) else {**bj, "books": bl}, f,
                      ensure_ascii=False, indent=None)
        print("✓ books.json chapterCount/author 更新")
    else:
        print("⚠ books.json 未找到该书")
