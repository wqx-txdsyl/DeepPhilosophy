# -*- coding: utf-8 -*-
"""#261 语词和对象（e9b084a9320b，威拉德·范·奥曼·蒯因）重建
病因: 已OCR未入清单补录书。旧 10 章为 dp_pdf_import 自动切章（按目录页取的章名），
  第一章+第二章全部正文被错误塞进最后一章'后记'（9.json 76KB），
  2-8 章空壳（240-352B）。
源: F:/philosophy/西方/威拉德·范·奥曼·蒯因/语词和对象.pdf（46 页简体扫描版，
  中国人民大学出版社 2011 '当代世界学术名著'，陈启伟、朱锐、张学广译，
  checkpoint OCR 46 页 fail 0）
结构（书内页码=PDF页-12）:
  p0-3 封面/版权/CIP（跳过）｜ p4 出版说明｜ p5 献辞（献给 我的老师和朋友 鲁道夫·卡尔纳普）
  p6 扉页引文两条（诺伊拉特/米勒）｜ p7-9 前言（p9 尾落款 W.V.O.蒯因 1959年6月3日）
  p10-12 目录（跳过）｜ p13-36 第一章语言与真理（节1-6: 从日常的事物着手/客观的引力/
    句子的互动/语词的学习方式/证据/设定物与真理）｜ p37-45 第二章翻译和意义
    （节7-8: 彻底翻译的先期步骤/刺激与刺激意义，PDF 截断于书内 33 页，8 节后缺失——
    源文件本身不完整，如实保留）
页眉: 偶页书名'语词和对象'、奇页章名（'第一章语言与真理'/'第二章翻译和意义'）页首循环剥
页码: 每页末行（'2一'/'-5'/'一9'/'10—'/'16_'/'B-' 等变体，B=8 误读），仅末行剥——
  正文中间有独立数字行（'11'/'12'/'18'/'21'/'3' 等脚注标记），绝不能全行通剥
节标题: '^\d{1,2}\.……' 独立成段（行内含'。'/'）'即正文行，不切）
修复: 重建 5 章；段落: 节标题独立段 + 其余行拼接为段（OCR 书范式）。
用法: python _xr_e9b084a9320b_quine_rebuild.py [--dry]
"""
import json, os, re, sys, shutil, time

BID = "e9b084a9320b"
CKPT = r"f:\program\Python\PhiAgent\backend\data\dp_pdf_import_ckpt.json"
SAFE = "西方_威拉德_范_奥曼_蒯因_语词和对象.pdf"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
# ⚠ 2026-08-08 事故修正：前端本地 dev 读 app/public/backend/data/book_chapters，必须双写
DST2 = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

def norm(s):
    return re.sub(r"\s+", "", s or "")

CH_TITLES = [
    "出版说明", "献辞", "前言",
    "第一章 语言与真理", "第二章 翻译和意义",
]
N = len(CH_TITLES)
# 跳过: 封面/版权/CIP/目录
SKIP_PAGES = {0, 1, 2, 3, 10, 11, 12}
# 标题行（按页精确剔除；p9 '前'+'言' 拆行）
STRIP_PAGES = {
    4: ["“当代世界学术名著”", "出版说明"], 7: ["前言"],
    9: ["前", "言"], 13: ["第一章语言与真理"], 37: ["第二章翻译和意义"],
}
# 页眉（页首循环剥）: 偶页书名/奇页章名
HEAD_RE = re.compile(r"^(语词和对象|第一章语言与真理|第二章翻译和意义)$")
# 页码（仅页末行剥）: '2一' '-5' '一9' '10—' '16_' 'B-' '12 —' 等变体
PAGE_RE = re.compile(r"^[B一—\-_ ]{0,2}\d{1,2}[一—\-_ ]{0,2}$")
# 节标题（独立成段）: '1.从日常的事物着手' 等；含'。'/'）'即正文行
SEC_RE = re.compile(r"^\d{1,2}\.[^。）]{1,24}$")

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

# ---- 分章页: 0出版说明(p4) 1献辞(p5-6) 2前言(p7-9) 3第一章(p13-36) 4第二章(p37-45) ----
PAGE_CH = {4: 0, 5: 1, 6: 1, 7: 2, 8: 2, 9: 2}

def ch_of(i):
    if i in PAGE_CH:
        return PAGE_CH[i]
    if 13 <= i <= 36:
        return 3
    if 37 <= i <= 45:
        return 4
    raise KeyError(i)

def page_paras(i):
    ls = [ln.strip() for ln in npages[i].split("\n") if ln.strip()]
    while ls and HEAD_RE.match(ls[0]):
        ls = ls[1:]                              # 页眉（页首循环剥）
    if i in STRIP_PAGES:
        ls = [l for l in ls if l not in STRIP_PAGES[i]]  # 标题行精确剔
    if ls and PAGE_RE.match(ls[-1]):
        ls = ls[:-1]                             # 页码（仅末行剥）
    out, buf = [], []
    for l in ls:
        if SEC_RE.match(l):
            if buf:
                out.append("".join(buf)); buf = []
            out.append(l)                        # 节标题独立段
        else:
            buf.append(l)
    if buf:
        out.append("".join(buf))
    return out

paras = [[] for _ in range(N)]
for i in sorted(npages):
    if i in SKIP_PAGES:
        continue
    cur = ch_of(i)
    ps = page_paras(i)
    if not ps:
        print(f"⚠ p{i}: 净化后为空")
    paras[cur].extend(ps)

files = {}
for idx in range(N):
    if not paras[idx]:
        print(f"⚠ 章{idx} {CH_TITLES[idx]!r}: 无内容")
    files[idx] = {"index": idx, "title": CH_TITLES[idx],
                  "content": [{"type": "text", "value": p} for p in paras[idx]]}
    nc = sum(len(norm(p)) for p in paras[idx])
    first = paras[idx][0][:36] if paras[idx] else "(空)"
    last = paras[idx][-1][:24] if paras[idx] else ""
    print(f"[{idx}] {CH_TITLES[idx]:<22s} {nc:6d}字 {len(paras[idx]):3d}段 | {first!r} … {last!r}")
assert len(files) == N

# ---- 验证 ----
total = sum(sum(len(norm(b["value"])) for b in files[idx]["content"]) for idx in range(N))
print(f"\n新总净: {total}")
all_text = "".join(norm(b["value"]) for idx in range(N) for b in files[idx]["content"])
# 页码粘连清零（段首不得汉字+数字粘连，排除 '年'/'岁' 等）
bad_page = [norm(b["value"])[:8] for idx in range(N) for b in files[idx]["content"]
            if re.match(r"[一-鿿]\d{1,2}", norm(b["value"]))
            and not re.search(r"\d{2,4}年", norm(b["value"])[:12])
            and not re.match(r"第\d{1,4}页", norm(b["value"]))]
print("页码粘连清零:", "✓" if not bad_page else f"✗ {bad_page[:6]}")
# 页眉/标题残留
bad_h = [f"章{idx}:{norm(b['value'])[:14]}" for idx in range(N) for b in files[idx]["content"]
         if HEAD_RE.match(norm(b["value"]))
         or norm(b["value"]) in {norm(x) for v in STRIP_PAGES.values() for x in v}]
print("标题清零:", "✓" if not bad_h else f"✗ {bad_h[:6]}")
# 节标题保留（独立段存在）
secs = [b["value"][:20] for idx in range(N) for b in files[idx]["content"]
        if SEC_RE.match(b["value"])]
print(f"节标题段: {len(secs)} 个:", " ".join(secs))
# 关键内容验证
ch = {idx: "".join(norm(b["value"]) for b in files[idx]["content"]) for idx in range(N)}
checks = [
    (0, "出版说明", "中华民族"), (1, "献辞", "鲁道夫·卡尔纳普"),
    (2, "前言", "语言是一种社会性的技能"), (2, "前言", "1959年6月3日"),
    (3, "第一章", "从日常的事物着手"), (3, "第一章", "相对主义"),
    (4, "第二章", "彻底翻译的先期步骤"), (4, "第二章", "刺激意义"),
]
print("验证:", "  ".join(f"{'✓'+t if kw in ch[i] else '✗'+t+'!'}" for i, t, kw in checks))
# 目录页内容不得混入
print("目录泄漏:", "✓" if "ENTIA NON GRATA" not in all_text else "✗ 目录混入正文!")

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
    "bookId": BID, "title": "语词和对象", "author": "威拉德·范·奥曼·蒯因",
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
