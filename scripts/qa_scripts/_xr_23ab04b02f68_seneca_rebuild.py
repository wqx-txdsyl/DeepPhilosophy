# -*- coding: utf-8 -*-
"""#263 塞涅卡道德书简（23ab04b02f68，卢修斯·阿奈乌斯·塞涅卡）重建
病因: 已OCR未入清单补录书。旧 2 章为 dp_pdf_import 自动切章（几乎未分）。
源: F:/philosophy/西方/塞涅卡/塞涅卡道德书简_致鲁基里乌斯书信集.pdf（684 页简体扫描版，
  塞涅卡著，124 封致鲁基里乌斯的书信，checkpoint OCR 683 页 fail 1（p2 封面区））
结构（书内页码 = 页眉 3 位数字；PDF 页序与书内页码有 4 处错位，必须按书内页码排序）:
  p0-5 封面/CIP（跳过）｜ p6-9 中文序（p7/p8 重复页去重）｜ p10-16 英文版序（p12/p13 重复页去重）
  p17-22 目录（跳过）｜ 正文 124 封信（书内 1-641）｜ 附录名称索引（书内 642-657 = p664-680）
  p681-683 CIP/版权/封底（跳过）
信边界 = 缺失位序列（书内 1-641 无页码页的位置，升序第 N 个 = 第 N 封信起始页，
  与目录页码一一吻合: 信12=036/信13=040/信14=045 等）；乱序区（信 12/13/14 标题页
  = PDF 58/101/59）由标题页序号行自报序号解决
页眉 3 类（页首剥）:
  h1 书名页眉: 'NNN塞涅卡道德书筒'（'001塞涅卡道德书筒'/'644塞涅卡道德书筒'/'658塞湿卡莲德书第'）
  h2 信标题页眉: 'X论标题NNN'（'九十九论安慰丧失亲友的人496'/'十六论哲学，生活的指南055'/
    '二十二：论半途而废079'）
  VAR 页码变体: '4%塞湿卡道德书筒'/'59%塞湿卡道德书筒'（=495/596 误读，页码=前后页中间值）
信标题页（无页码，124 个）: 首行序号（'一'~'一百二十四'，变体 '+'=十/'区金人'=六十五）+
  次行标题（'论XXX'）+ 偶有问候行（信 1 '塞涅卡（Seneca）向他的朋友鲁基里乌斯问好。'）
修复: 重建 127 章（序/英文版序/书信一~一百二十四/附录名称索引）；段落: 页级拼接
  （OCR 书范式）。繁体无（简体扫描版）。
用法: python _xr_23ab04b02f68_seneca_rebuild.py [--dry]
"""
import json, os, re, sys, shutil, time

BID = "23ab04b02f68"
CKPT = r"f:\program\Python\PhiAgent\backend\data\dp_pdf_import_ckpt.json"
SAFE = "西方_塞涅卡_塞涅卡道德书简_致鲁基里乌斯书信集.pdf"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
# ⚠ 2026-08-08 事故修正：前端本地 dev 读 app/public/backend/data/book_chapters，必须双写
DST2 = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

def norm(s):
    return re.sub(r"\s+", "", s or "")

_CN = ["一", "二", "三", "四", "五", "六", "七", "八", "九"]
def num2cn(n):
    """1-124 → 中文数字"""
    if n <= 10:
        return _CN[n - 1] if n < 10 else "十"
    if n < 20:
        return "十" + _CN[n - 11]
    if n < 100:
        t, o = divmod(n, 10)
        return _CN[t - 1] + "十" + (_CN[o - 1] if o else "")
    if n < 110:
        return "一百" + ("零" + _CN[n - 101] if n > 100 else "")
    t, o = divmod(n - 100, 10)
    return "一百" + _CN[t - 1] + "十" + (_CN[o - 1] if o else "")

def cn2num(s):
    """中文数字 1-124 → int（'六十五'/'一百二十四'/'一百零一'/'十'；'+'=10）"""
    if s == "+":
        return 10
    d = {"零": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
         "六": 6, "七": 7, "八": 8, "九": 9}
    if "百" in s:
        h, r = s.split("百")
        v = 100 * (d[h] if h else 1)
        if not r:
            return v
        if r.startswith("零"):
            r = r[1:]
        if "十" in r:
            t, o = r.split("十")
            v += 10 * (d[t] if t else 1)
            if o:
                v += d[o]
        else:
            v += d[r]
        return v
    if "十" in s:
        t, o = s.split("十")
        return 10 * (d[t] if t else 1) + (d[o] if o else 0)
    return d[s]

# 跳过: 封面/CIP/目录/书末 CIP 版权封底
SKIP_PAGES = {0, 1, 2, 3, 4, 5, 17, 18, 19, 20, 21, 22, 681, 682, 683}
# 附录区（PDF p664-680 起；信区 = 书内 1-641）
APPENDIX = (664, 680)
# 页眉: h1 书名页眉 / h2 信标题页眉（含 3 位页码） / VAR 页码变体
H1 = re.compile(r"^(\d{3})[\u4e00-\u9fff]{2,9}")
H2 = re.compile(r"^([一二三四五六七八九十百]{1,5})[：]?论?([\u4e00-\u9fff，、。：]{2,30})(\d{3})")
VAR = re.compile(r"^[\d%]{1,4}塞[涅湿温]卡道德书[筒简]$")
# 内容页页眉（h1 书名页眉 / h2 信标题页眉 / VAR 页码变体）
BODY_HEAD = re.compile(
    r"^(?:\d{3}[一-鿿]{2,9}"
    r"|[一二三四五六七八九十百]{1,5}[：]?论?[一-鿿，、。：]{2,30}\d{3}"
    r"|[\d%]{1,4}塞[涅湿温]卡道德书[筒简])")
# 前置页眉: 'i塞涅卡道德书简'/'VI塞涅卡道德书筒'/'序Ⅲ'/'英文版序V'/'英文版序i区'
FRONT_HEAD = re.compile(r"^(?:[iIvVxX]+塞[涅湿温]卡道德书[筒简]|序.{0,3}|英文版序.{0,4})$")
# 附录页眉: '附录名称索引643'（奇数页）/ 偶数页 'NNN塞涅卡道德书筒' 由 H1 剥
APX_HEAD = re.compile(r"^(?:附录名称索引\d{3}|\d{3}[\u4e00-\u9fff]{2,9})$")
# 信标题页序号行
SEQ_RE = re.compile(r"^[一二三四五六七八九十百零]{1,5}$")

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

# ---- 第一步: 正文区（书内 1-641）每页页码 ----
page_pn = {}   # pdf_i -> 书内页码（含 VAR 变体页，页码=前后页中间值）
var_pages = []
for i in sorted(npages):
    if i in SKIP_PAGES or i <= 22 or i >= APPENDIX[0]:
        continue
    ls = [ln.strip() for ln in npages[i].split("\n") if ln.strip()]
    if not ls:
        continue
    m1 = H1.match(ls[0])
    m2 = H2.match(ls[0])
    if m1:
        page_pn[i] = int(m1.group(1))
    elif m2:
        page_pn[i] = int(m2.group(3))
    elif VAR.match(ls[0]):
        var_pages.append(i)

# VAR 变体页页码（OCR '9'/'6' → '%' 误读）: 已内容验证——
#   p518 '4%塞湿卡道德书筒' = 495（夹在书内 494(p516)/496(p517) 之间，PDF 扫描位置错位到 496 后）
#   p618 '59%塞湿卡道德书筒' = 596（夹在 595(p617)/597(p619) 之间，同理错位）
VAR_PN = {"4%塞湿卡道德书筒": 495, "59%塞湿卡道德书筒": 596}
for i in var_pages:
    head = npages[i].splitlines()[0].strip()
    pn = VAR_PN.get(head)
    if pn is None or pn in page_pn.values():
        sys.exit(f"VAR 变体页 p{i} 页码无法确认: {head!r}")
    page_pn[i] = pn
    print(f"  变体页 p{i}: 页码 = {pn}（首行 {head!r}）")
print(f"有页码页: {len(page_pn)}（含 VAR {len(var_pages)}）")

# ---- 第二步: 缺失位序列 → 信起始页 ----
missing = [p for p in range(1, 642) if p not in page_pn.values()]
starts = missing[:124]
assert len(starts) == 124, f"信起始页期望 124 个，实际 {len(starts)}: {missing[:8]}...{missing[-8:]}"
print(f"信起始页(书内): {starts[:8]} ... {starts[-4:]}")

# ---- 第三步: 无页码页（书内 1-641）= 信标题页，序号自报 ----
no_pn = [(i, npages[i].splitlines()[0].strip() if npages[i].strip() else "")
         for i in sorted(npages)
         if i > 22 and i < APPENDIX[0] and i not in SKIP_PAGES and i not in page_pn]
print(f"信标题页候选: {len(no_pn)}（期望 124）")
assert len(no_pn) == 124

letter_pdf = {}
unresolved = []
for idx, (i, head) in enumerate(no_pn):
    seq = cn2num(head) if SEQ_RE.match(head) else None
    if seq is None:
        prev_l = None
        for j in range(idx - 1, -1, -1):
            prev_l = letter_pdf.get(no_pn[j][0])
            if prev_l:
                break
        seq = prev_l + 1 if prev_l else None
    if seq is None or not (1 <= seq <= 124):
        unresolved.append((i, head))
        continue
    letter_pdf[i] = seq
print(f"序号解析: {len(letter_pdf)}/124")
if unresolved:
    sys.exit(f"⚠ 标题页序号未解析: {unresolved}")

# ---- 第四步: 分章构建 ----
N = 2 + 124 + 1  # 序 + 英文版序 + 124 信 + 附录
CH_TITLES = ["序", "英文版序"] + [f"书信{num2cn(n)}" for n in range(1, 125)] + ["附录 名称索引"]
paras = [[] for _ in range(N)]

def clean_para(ls, head_re):
    while ls and head_re.match(ls[0]):
        ls = ls[1:]
    return ["".join(ls)] if ls else []

# 前置区: 序 p6-9 / 英文版序 p10-16（相邻重复页去重）
prev_text = None
for ci, (p0, p1) in enumerate(((6, 10), (10, 17))):
    for i in range(p0, p1):
        if i not in npages:
            continue
        if npages[i] == prev_text:
            print(f"  ⚠ 前置重复页 p{i} 去重")
            continue
        prev_text = npages[i]
        ls = [ln.strip() for ln in npages[i].split("\n") if ln.strip()]
        paras[ci].extend(clean_para(ls, FRONT_HEAD))

# 书信一~一百二十四
for n in range(1, 125):
    ci = 1 + n
    s, end = starts[n - 1], (starts[n] if n < 124 else 642)
    # 标题页
    tp = next(i for i, l in letter_pdf.items() if l == n)
    ls = [ln.strip() for ln in npages[tp].split("\n") if ln.strip()]
    while ls and (SEQ_RE.match(ls[0]) or ls[0] in ("+", "区金人") or VAR.match(ls[0])):
        ls = ls[1:]
    title_line = None
    if ls and not ls[0].startswith("（"):
        title_line = ls[0]          # 标题行 = 序号行后第一个非正文行（'论XXX'/'再论美德'）
        ls = ls[1:]
    if title_line is None:
        print(f"⚠ 信{n} 标题页未找到标题行: {npages[tp][:100]!r}")
        title_line = "(标题缺失)"
        ls = []
    CH_TITLES[ci] = f"书信{num2cn(n)} {title_line}"
    # 问候行（含 '问好' 非 '（1）' 开头）独立段
    if ls and "问好" in ls[0] and not ls[0].startswith("（1）"):
        paras[ci].append(ls[0])
        ls = ls[1:]
    if ls:
        paras[ci].append("".join(ls))
    # 内容页（书内 [s+1, end-1]，按书内页码排序）
    for i in sorted((i for i, pn in page_pn.items() if s < pn < end), key=lambda x: page_pn[x]):
        l2 = [ln.strip() for ln in npages[i].split("\n") if ln.strip()]
        paras[ci].extend(clean_para(l2, BODY_HEAD))
    if not paras[ci]:
        print(f"⚠ 信{n} 无内容")

# 附录（p664-680）
for i in range(APPENDIX[0], APPENDIX[1] + 1):
    if i not in npages:
        continue
    ls = [ln.strip() for ln in npages[i].split("\n") if ln.strip()]
    if i == APPENDIX[0]:
        ls = [l for l in ls if l not in ("附录", "名称索引")]
    paras[N - 1].extend(clean_para(ls, APX_HEAD))

files = {}
for idx in range(N):
    if not paras[idx]:
        print(f"⚠ 章{idx} {CH_TITLES[idx]!r}: 无内容")
    files[idx] = {"index": idx, "title": CH_TITLES[idx],
                  "content": [{"type": "text", "value": p} for p in paras[idx]]}
    nc = sum(len(norm(p)) for p in paras[idx])
    first = paras[idx][0][:34] if paras[idx] else "(空)"
    last = paras[idx][-1][:22] if paras[idx] else ""
    print(f"[{idx:3d}] {CH_TITLES[idx]:<34s} {nc:6d}字 {len(paras[idx]):3d}段 | {first!r} … {last!r}")
assert len(files) == N

# ---- 验证 ----
total = sum(sum(len(norm(b["value"])) for b in files[idx]["content"]) for idx in range(N))
print(f"\n新总净: {total}")
all_text = "".join(norm(b["value"]) for idx in range(N) for b in files[idx]["content"])
# 页码粘连清零（段首汉字+数字，排除 年/：）
bad_page = [norm(b["value"])[:8] for idx in range(N) for b in files[idx]["content"]
            if re.match(r"[一-鿿]\d{2,3}", norm(b["value"]))
            and not re.search(r"\d{2,4}年", norm(b["value"])[:12])
            and not re.search(r"\d{1,2}[:：]\d{1,2}", norm(b["value"]))]
print("页码粘连清零:", "✓" if not bad_page else f"✗ {bad_page[:6]}")
# 页眉残留（书名页眉）
bad_h = [f"章{idx}:{norm(b['value'])[:16]}" for idx in range(N) for b in files[idx]["content"]
         if re.search(r"塞涅卡道德书[筒简]|塞湿卡道德书[筒简第]|附录名称索引\d", norm(b["value"]))
         and not re.search(r"\d{2,4}年", norm(b["value"])[:12])]
print("页眉清零:", "✓" if not bad_h else f"✗ {bad_h[:6]}")
# 序号残留（段首 'X论' 无页码 = 标题页序号粘连）
bad_n = [f"章{idx}:{b['value'][:12]}" for idx in range(N) for b in files[idx]["content"]
         if re.match(r"^[一二三四五六七八九十百]{1,4}论", b["value"])]
print("序号残留:", "✓" if not bad_n else f"✗ {bad_n[:6]}")
# 关键内容验证
ch = {idx: "".join(norm(b["value"]) for b in files[idx]["content"]) for idx in range(N)}
checks = [
    (0, "序", "马可·奥勒留"), (1, "英文版序", "卢修斯"),
    (2, "书信一", "问好"), (2, "书信一", "继续这样做"),
    (13, "书信十二", "梧桐树"), (13, "书信十二", "费利西奥"),
    (66, "书信六十五", "起因和物质"), (66, "书信六十五", "斯多葛哲学家"),
    (118, "书信一百一十七", "折磨是邪恶的"),
    (118, "书信一百一十七", "小加图"),
    (121, "书信一百二十", "既美好又尊荣"),
    (126, "附录", "芝诺"), (126, "附录", "奥菲狄乌斯"),
]
print("验证:", "  ".join(f"{'✓'+t if kw in ch[i] else '✗'+t+'!'}" for i, t, kw in checks))

# ---- toc（127 chapter 平铺） ----
toc = [{"type": "chapter", "title": files[i]["title"], "index": i, "level": 1}
       for i in range(N)]
print(f"\ntoc 项: {len(toc)}")

if "--dry" in sys.argv:
    sys.exit(0)

# ---- 写入（旧 2 章自动数据 → 备份 _old_bad） ----
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
    "bookId": BID, "title": "塞涅卡道德书简", "author": "卢修斯·阿奈乌斯·塞涅卡",
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
