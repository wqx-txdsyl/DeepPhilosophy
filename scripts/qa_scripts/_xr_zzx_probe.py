# -*- coding: utf-8 -*-
"""#126 政治学（亚里士多德，吴寿彭译，商务汉译名著本）53b09f03e24e 探针
OCR 源 = dp_pdf_import_ckpt.json['ocr']['西方_亚里士多德_政治学.pdf']（527/527 页已完成）。
结构: P0-1 书名页 / P2-17 吴恩裕《论亚里士多德的〈政治学〉》序言 /
      P18 书前目录（仅卷）/ P19-496 正文八卷（每卷"卷（X）N"卷标行 + 章一~章X）/
      P497-522 书末附录"本书章节摘要"（不入正文）。
页内行: 页眉"政治学"独立行 / 页码独立纯数字行 → 过滤。
章标题行: 行首"章[一二三四五六七八九十]+"（"章十-"=章十一），后接"。/）"为注释行（保留正文）。
输出每卷章序列 + 页范围 + 字数，人工核对后写重建脚本。
"""
import json, re, os

CK = "f:/program/Python/PhiAgent/backend/data/dp_pdf_import_ckpt.json"
BID = "53b09f03e24e"
OLD = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"

ck = json.load(open(CK, encoding="utf-8"))
v = ck["ocr"]["西方_亚里士多德_政治学.pdf"]
pages = sorted(v, key=int)

CH_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7,
          "八": 8, "九": 9, "十": 10, "十一": 11, "十二": 12, "十三": 13,
          "十四": 14, "十五": 15, "十六": 16, "十七": 17, "十八": 18}
CH_TEXT = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "七", 8: "八",
           9: "九", 10: "十", 11: "十一", 12: "十二", 13: "十三", 14: "十四",
           15: "十五", 16: "十六", 17: "十七", 18: "十八"}

def is_page_num(l):
    return re.fullmatch(r"\d{1,3}", l) is not None

def is_header(l):
    return l == "政治学"

def is_vol_line(l):
    return re.match(r"^卷[（(][^)）]*[)）][一二三四五六七八九十]*$", l) is not None

# ---- 扫描序言 ----
print("== 序言 P2-17 ==")
for p in range(2, 18):
    lines = [l.strip() for l in v[str(p)].split("\n") if l.strip()]
    body = [l for l in lines if not is_page_num(l) and not is_header(l)]
    print(f"  P{p:3d} 正文行{len(body):2d} 首: {body[0][:20] if body else ''!r}")

# ---- 扫描正文卷/章 ----
print("\n== 正文 P19-496 卷/章序列 ==")
vols = []      # (页, 卷标行, 卷序号)
chaps = []     # (页, 章序号, 标题行原文, 是否粘连正文)
for p in pages:
    pn = int(p)
    if pn < 19 or pn > 496:
        continue
    for l in [x.strip() for x in v[p].split("\n") if x.strip()]:
        if is_vol_line(l):
            vols.append((pn, l))
            continue
        m = re.match(r"^(章[一二三四五六七八九十]+-?[一二三四五六七八九十]?)\s*", l)
        if m:
            z = m.group(1)
            rest = l[len(z):]
            # 注释行: 后接阿拉伯数字/标点/括号（纯"①"是标题行注标噪音, 保留为标题）
            if rest and (rest[0] in "0123456789" or rest[0] in "。，、；：）〕」】"):
                continue
            zz = "章十一" if z == "章十-" else z
            num = CH_NUM.get(zz[1:])
            if num is None:
                continue
            chaps.append((pn, num, z, rest, l))

# 卷内章序验证（同号重复 = 注释/引用，忽略第二次起）
vol_starts = [v[0] for v in vols]
total = 0
for i, (vp, vl) in enumerate(vols):
    vn = i + 1
    v_end = vol_starts[i + 1] if i + 1 < len(vols) else 497
    vc = []
    seen = set()
    for c in chaps:
        if not (vp <= c[0] < v_end):
            continue
        if c[1] in seen:
            print(f"     ⚠ 重复章号 P{c[0]:3d} {c[2]!r} 全行: {c[4][:40]!r}")
            continue
        seen.add(c[1])
        vc.append(c)
    seq = [c[1] for c in vc]
    ok = seq == list(range(1, len(seq) + 1))
    total += len(vc)
    print(f"卷{vn} {vl!r} P{vp}~{v_end-1}: {len(vc)}章 连续:{ok} seq={seq}")
    for c in vc[:1] + vc[-1:]:
        print(f"     P{c[0]:3d} {c[2]!r} 粘连:{c[3][:14]!r}")
print(f"正文章总数: {total}")

# 旧数据字数对比
old_total = 0
for fn in os.listdir(OLD):
    if fn.endswith(".json") and fn != "meta.json":
        ch = json.load(open(os.path.join(OLD, fn), encoding="utf-8"))
        old_total += sum(len(b.get("value", "")) for b in ch["content"] if b.get("type") == "text")
print(f"\n旧数据 8 卷总字数: {old_total}")

# OCR 正文字数估算（去页眉页码卷标行）
body_total = 0
for p in pages:
    pn = int(p)
    if pn < 19 or pn > 496:
        continue
    for l in [x.strip() for x in v[p].split("\n") if x.strip()]:
        if is_page_num(l) or is_header(l) or is_vol_line(l):
            continue
        body_total += len(l)
print(f"OCR 正文(去页眉/页码/卷标)行字符: {body_total}")

# 序言字数
pre_total = 0
for p in range(2, 18):
    for l in [x.strip() for x in v[str(p)].split("\n") if x.strip()]:
        if is_page_num(l) or is_header(l):
            continue
        pre_total += len(l)
print(f"序言(去页眉/页码)行字符: {pre_total}")
print(f"合计(序言+正文): {pre_total + body_total}")
