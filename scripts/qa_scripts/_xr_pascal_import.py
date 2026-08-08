# -*- coding: utf-8 -*-
"""帕斯卡尔《最伟大的思想家-帕斯卡尔》（d036e1e712eb）主线1补录入库
OCR 已 fail0 完成（168 页，checkpoint 有文本），books.json 登记 cc=0 未入库。
结构（对照目录页 + 标题行定位）:
  页0-3 书名页与简介 | 4-8 总序 | 9-11 目录(弃) | 12-13 序 |
  14-22 一章(帕斯卡尔：盛名与神秘) 23-36 二章(生平) 37-51 三章(科学家和科学哲学家)
  52-67 四章(神学论争) 68-80 五章(《思想录》：风格与意图) 81-89 六章(上帝：可否证明？)
  90-107 七章(怀疑主义与隐匿的上帝) 108-129 八章(废的王族) 130-150 九章(上帝之赌)
  151-161 十章(基督、灵性和生命意义) | 162-165 参考书目 | 166-167 丛书书目/封底(弃)
剥除: 页眉 OnPascal/帕斯卡尔/章名、页码行（纯数字/数字+符号）、章首标题行
author 按主线2 传记规则 = 传书作者 道格拉斯·格鲁秀斯（books.json 原写'布莱兹·帕斯卡尔'错误）
用法: python _xr_pascal_import.py [--dry]
"""
import json, os, re, sys, shutil

BID = "d036e1e712eb"
CKPT = "f:/program/Python/PhiAgent/backend/data/dp_pdf_import_ckpt.json"
KEY = "西方_布莱兹_帕斯卡尔_最伟大的思想家_-_帕斯卡尔.pdf"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DST2 = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters/{BID}"
DETAIL_DA = f"f:/program/Python/PhiAgent/app/public/book_detail/{BID}.json"
DETAIL_DB = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

# (起始页, 结束页, 章名) —— 页为 checkpoint 页索引
CHS = [
    (0, 3, "书名页与简介"),
    (4, 8, "总　序"),
    (12, 13, "序"),
    (14, 22, "第一章 帕斯卡尔：盛名与神秘"),
    (23, 36, "第二章 生平"),
    (37, 51, "第三章 科学家和科学哲学家"),
    (52, 67, "第四章 神学论争"),
    (68, 80, "第五章 《思想录》：风格与意图"),
    (81, 89, "第六章 上帝：可否证明？"),
    (90, 107, "第七章 怀疑主义与隐匿的上帝"),
    (108, 129, "第八章 废的王族"),
    (130, 150, "第九章 上帝之赌"),
    (151, 161, "第十章 基督、灵性和生命意义"),
    (162, 165, "参考书目"),
]
TITLES = [t for _, _, t in CHS]

ck = json.load(open(CKPT, encoding="utf-8"))
pages = ck["ocr"][KEY]
assert len(pages) == 168, len(pages)
text_all = "\n".join(str(v) for v in pages.values())
print(f"OCR 文本: {len(pages)} 页, {len(text_all)} 字")

def clean_page(t):
    """剥页眉/页码/章首标题"""
    lines = [l.strip() for l in t.split("\n")]
    lines = [l for l in lines if l and l not in ("OnPascal", "On Pascal")]
    # 章首标题行：第一个非空行匹配 ^数字+章名
    for i, l in enumerate(lines[:4]):
        m = re.match(r"^(\d{1,2})\s*(.{2,24})$", l)
        if m:
            nm = m.group(2).strip("：:")
            if any(nm.startswith(ch[:6]) or ch[3:9] and nm.startswith(ch[3:9]) or nm in ch for ch in TITLES[3:]):
                lines = lines[i + 1:]
                break
    # 页眉（前 3 行内 任意章名/帕斯卡尔/最伟大的思想家 独立行）与页码行
    def norm(s):
        return re.sub(r"[\s　]", "", s)
    hdrs = [c for c in TITLES if c not in ("第一章 帕斯卡尔：盛名与神秘",)]
    kept = []
    for i, l in enumerate(lines):
        nl = norm(l)
        if i < 3 and (nl in ("帕斯卡尔", "最伟大的思想家")
                      or any(nl == norm(c) or (len(c) > 3 and nl.startswith(norm(c)[:6])) for c in hdrs)):
            continue
        if re.match(r"^[一二三四五六七八九十]*\d{1,4}[=—\-]?$", l):   # 页码 '一10=' '-737' '25' '150'
            continue
        kept.append(l)
    return "\n".join(kept)

chs = []
for p0, p1, title in CHS:
    body = "\n\n".join(clean_page(str(pages[str(i)])) for i in range(p0, p1 + 1))
    chs.append({"index": len(chs), "title": title, "content": [{"type": "text", "value": p} for p in body.split("\n\n") if p.strip()]})

# ---- 验证 ----
tot = 0
for c in chs:
    n = sum(len(b["value"]) for b in c["content"])
    tot += n
    print(f"[{c['index']}] {c['title'][:22]:<24s} {n:7d}字 {len(c['content']):3d}段  首: {c['content'][0]['value'][:22]!r}")
print(f"全库: {len(chs)} 章 {tot} 字（原文 {len(text_all)} 字，剥除后保留 {tot/len(text_all):.0%}）")
empty = [c["index"] for c in chs if not c["content"]]
print("空章:", empty if empty else "无")

if "--dry" in sys.argv:
    sys.exit(0)

# ---- 写入三处 ----
if os.path.isdir(SRC):
    suf = "_old_bad"
    i2 = 2
    while os.path.isdir(SRC + suf):
        suf = f"_old_bad{i2}"
        i2 += 1
    os.rename(SRC, SRC + suf)
    print(f"\n备份旧数据 → {os.path.basename(SRC) + suf}")
os.makedirs(SRC)
for c in chs:
    json.dump({"index": c["index"], "title": c["title"], "content": c["content"]},
              open(os.path.join(SRC, f"{c['index']}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
meta = {"bookId": BID, "title": "帕斯卡尔", "author": "道格拉斯·格鲁秀斯",
        "toc": [{"type": "chapter", "title": t, "index": i} for i, t in enumerate(TITLES)],
        "cover": None, "chapterCount": len(chs), "chapterTitles": TITLES}
json.dump(meta, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print(f"✓ 写入 {SRC}: {len(chs)} 章")
shutil.rmtree(DST, ignore_errors=True); shutil.copytree(SRC, DST)
shutil.rmtree(DST2, ignore_errors=True); shutil.copytree(SRC, DST2)
print("✓ 同步 DST/DST2")

# ---- detail 双端（保留原 summary/tags/cover） ----
for p in (DETAIL_DA, DETAIL_DB):
    d = json.load(open(p, encoding="utf-8"))
    d["author"] = "道格拉斯·格鲁秀斯"
    d["toc"] = meta["toc"]
    d["chapterCount"] = len(chs)
    d["chapterTitles"] = TITLES
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
    print(f"✓ detail: {p.split('/')[-2]}")

# ---- books.json（cc + author） ----
books = json.load(open(BOOKS, encoding="utf-8"))
for x in books:
    if str(x.get("id")) == BID:
        old = (x["chapterCount"], x["author"])
        x["chapterCount"] = len(chs)
        x["author"] = "道格拉斯·格鲁秀斯"
        print(f"✓ books.json {BID} cc {old[0]}→{len(chs)} author {old[1]}→道格拉斯·格鲁秀斯")
json.dump(books, open(BOOKS, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
print("✓ books.json 写入完成")
