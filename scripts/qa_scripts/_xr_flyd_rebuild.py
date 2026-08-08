# -*- coding: utf-8 -*-
"""《弗洛伊德文集》（12卷本，九州出版社）a9955bc4ee64 重建（一次性，旧数据重组）
旧数据 79 章全平级：10 个"《弗洛伊德文集》编委会"页（255字×10 相同名单）+ 11 个
"新版编译说明"（6644字×11 相同）+ 58 作品。卷标题（12 卷）在导入时丢失。
EPUB 源（F:/philosophy/西方/西格蒙德·弗洛伊德/弗洛伊德文集.epub）验证（spine 103 文件）:
  h1 = 12 卷标题页（爱情心理学/达·芬达的童年回忆[EPUB错字]/诙谐及其与潜意识/精神分析导论/
  精神分析新论/日常生活心理病理学/释梦（上）/释梦（下）/图腾与禁忌/文明及其缺憾/
  癔症研究/自我与本），卷首页含 h2 编委会（10 卷）或新版编译说明（B 卷）。
  编译说明"三、卷次划分"官方确认：卷1癔症研究（含导论+略传）/卷2 日常生活心理病理学/
  卷3 释梦（上）/卷4 释梦（下）/…与 spine 卷分组一致。
  ncx 80 条 = 版权 + 12 卷标 + 10 编译说明 + 57 作品（ncx 漏"第六章 梦的工作"，
  B 卷编译说明无条目）；旧数据 79 = 10 编委会 + 11 编译说明 + 58 作品（含第六章）。
  旧数据 30.json 标题"（在巴黎城的盾形徽章上[190]）"= EPUB h2 被脚注残片顶替，
  实际作品为《精神分析运动史》（按语"对精神分析产生、发展和分裂过程的历史总结"+
  末块"1914年2月"确认）。
重建:
  [ch]  0 新版编译说明（保留 1 份为独立章，无 part）
  [part] 12 卷（part 标题 = EPUB 卷标题原样；B 卷"达·芬达"为 EPUB 错字，保留）
    [ch] 58 作品（卷内，源 = 旧数据文件，逐 block 原样）
  删 10 编委会页（纯名单无正文价值）+ 10 重复编译说明。cc 79 → 59。
用法: python _xr_flyd_rebuild.py [--dry]
"""
import json, os, re, sys, shutil

BID = "a9955bc4ee64"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

def norm(s):
    return re.sub(r"\s+", "", s or "")

old = {}
for fn in os.listdir(SRC):
    if not fn.endswith(".json") or fn == "meta.json":
        continue
    ch = json.load(open(os.path.join(SRC, fn), encoding="utf-8"))
    old[int(fn[:-5])] = ch
assert len(old) == 79, len(old)

# ---- 尾部剥离：旧数据各卷末作品文件尾粘入下一卷卷首页 h1 标题块 ----
#   9(力比多类型)尾 = B 卷首页"达·芬达的童年回忆"
#   17(非专业者)尾 = C 卷首页"诙谐及其与潜意识"
#   34(日常生活心理病理学)尾 = G上 首页"释梦（上）"
#   51(第五章)尾 = G下 首页"释梦（下）" + 空块 + 书名页 3 行（吕 俊 高申春 译/修订）
#   72(癔症研究)尾 = K 卷首页"自我与本"
STRIP_TAIL = {9: 1, 17: 1, 34: 1, 51: 5, 72: 1}  # 源文件号: 尾部删块数
stripped_chars = 0
for fn, n in STRIP_TAIL.items():
    for _ in range(n):
        stripped_chars += len(old[fn]["content"].pop().get("value", ""))
print(f"剥离卷首页残块 {len(STRIP_TAIL)} 处 {stripped_chars} 字")

# ---- 结构表 ----
# (part 卷标题, [(章标题, [源文件...]), ...])
STANDS = [("新版编译说明", [1])]   # 独立章（无 part），11 份重复编译说明只保留 A 卷这份

VOLS = [
    ("爱情心理学", [
        ("性学三论", [2]),
        ("儿童性理论", [3]),
        ("“文明的”性道德与现代神经症", [4]),
        ("爱情心理学", [5]),
        ("论自恋：导论", [6]),
        ("本能及其变化", [7]),
        ("压抑", [8]),
        ("力比多类型", [9]),
    ]),
    ("达·芬达的童年回忆", [   # EPUB 卷标题错字（应"达·芬奇"），忠实源保留
        ("戏剧中的变态人物", [11]),
        ("詹森的《格拉迪沃》中的幻觉与梦", [12]),
        ("作家与白日梦", [13]),
        ("达·芬奇的童年回忆", [14]),
        ("米开朗基罗的摩西[149]", [15]),
        ("陀思妥耶夫斯基与弑父者", [16]),
        ("非专业者的分析问题——与无偏见的人的谈话", [17]),
    ]),
    ("诙谐及其与潜意识", [
        ("诙谐及其与潜意识的关系", [20]),
        ("精神分析中潜意识的注释", [21]),
        ("论潜意识", [22]),
    ]),
    ("精神分析导论", [
        ("精神分析导论", [25]),
    ]),
    ("精神分析新论", [
        ("精神分析新论", [28]),
        ("精神分析五讲", [29]),
        ("精神分析运动史", [30]),  # 旧标题"（在巴黎城的盾形徽章上[190]）"= 脚注残片
        ("精神分析纲要", [31]),
    ]),
    ("日常生活心理病理学", [
        ("日常生活心理病理学", [34]),
    ]),
    ("释梦（上）", [
        ("按语", [37]),
        ("英文版编者导言", [38]),
        ("第一版序言", [39]),
        ("第二版序言", [40]),
        ("第三版序言", [41]),
        ("第四版序言", [42]),
        ("第五版序言", [43]),
        ("第六版序言", [44]),
        ("第八版序言", [45]),
        ("英文第三版（修订版）序言[7]", [46]),
        ("第一章 有关梦的问题的科学文献[8]", [47]),
        ("第二章 释梦的方法：一个梦例的分析", [48]),
        ("第三章 梦是愿望的满足", [49]),
        ("第四章 梦的伪装", [50]),
        ("第五章 梦的材料与来源", [51]),
    ]),
    ("释梦（下）", [
        ("第六章 梦的工作[1]", [52]),
        ("第七章 梦的过程的心理学[243]", [53]),
        ("论梦", [54]),
        ("释梦在精神分析中的运用", [55]),
        ("论释梦的理论与实践", [56]),
    ]),
    ("图腾与禁忌", [
        ("图腾与禁忌", [59]),
        ("摩西与一神教", [60]),
    ]),
    ("文明及其缺憾", [
        ("一个幻觉的未来", [63]),
        ("文明及其缺憾", [64]),
        ("为什么有战争？", [65]),
        ("弗洛伊德自传", [66]),
        ("补记", [67]),
    ]),
    ("癔症研究", [
        ("导论", [70]),
        ("弗洛伊德略传", [71]),
        ("癔症研究", [72]),
    ]),
    ("自我与本", [
        ("超越快乐原则", [75]),
        ("群体心理学与自我的分析", [76]),
        ("自我与本我", [77]),
        ("抑制、症状与焦虑", [78]),
    ]),
]

# ---- 组装 ----
toc = []
files = {}
idx = 0

def push_ch(title, srcs):
    global idx
    blocks = []
    for s in srcs:
        blocks.extend(old[s]["content"])
    files[idx] = {"index": idx, "title": title, "content": blocks}
    toc.append({"type": "chapter", "title": title, "index": idx, "level": 1})
    idx += 1

for t, srcs in STANDS:
    push_ch(t, srcs)
for pt, chs in VOLS:
    toc.append({"type": "part", "title": pt, "index": idx, "level": 0})
    for t, srcs in chs:
        push_ch(t, srcs)

# ---- 校验 ----
n_part = sum(1 for t in toc if t["type"] == "part")
assert n_part == 12, n_part
assert len(files) == 59, len(files)
used = sorted(s for _, chs in VOLS for _, srcs in chs for s in srcs) + [1]
assert len(used) == len(set(used)), "源文件重复使用"
for i in sorted(files):
    assert i == files[i]["index"], "index 连续"

total_chars = 0
for i in sorted(files):
    nc = sum(len(b.get("value", "")) for b in files[i]["content"])
    total_chars += nc
    print(f"  {i:2d} {files[i]['title'][:44]:46s} {nc:7d} 字")
print(f"总: {len(files)} 章 + {n_part} part, {total_chars} 字符（旧 79 章平级, cc 79→59）")
old_total = sum(sum(len(b.get("value", "")) for b in old[i]["content"]) for i in old)
dropped = sorted(set(old) - set(used))
dropped_total = sum(sum(len(b.get("value", "")) for b in old[i]["content"]) for i in dropped)
print(f"旧数据总字数: {old_total} | 删 {len(dropped)} 个重复页（编委会×10 + 编译说明×10）: {dropped_total} 字")
for t in toc:
    ind = "  " * t.get("level", 1)
    print(f"{ind}[{t['type']}] {t['title'][:44]}")
print("首:", files[0]["title"], "| 末:", files[58]["title"])

if "--dry" in sys.argv:
    # 卷标题残块（旧数据导入时粘入的下一卷卷首页 h1）——剥离后应为 0
    RESIDUE_NORMS = {"达·芬达的童年回忆", "诙谐及其与潜意识", "释梦（上）", "释梦（下）",
                     "自我与本", "新版编译说明"}
    n_res = 0
    for i, ch in files.items():
        for b in ch["content"]:
            if "value" not in b:
                continue
            nv = norm(b["value"])
            if nv in RESIDUE_NORMS or (i != 0 and nv == "《弗洛伊德文集》编委会") \
                    or nv in {"未知", "目录"}:
                print(f"⚠ 卷标题残块 [{i} {ch['title'][:14]}]: {b['value'][:40]!r}")
                n_res += 1
    print(f"卷标题残块: {n_res}")
    sys.exit(0)

# ---- 写入 ----
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
for i, ch in files.items():
    json.dump(ch, open(os.path.join(SRC, f"{i}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
meta = {
    "bookId": old_meta.get("bookId") or BID,
    "title": old_meta.get("title") or "弗洛伊德文集",
    "author": old_meta.get("author") or "西格蒙德·弗洛伊德",
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
print("✓ 同步 DP chapters")

for p in (DETAIL_SRC, DETAIL_DST):
    if os.path.exists(p):
        d = json.load(open(p, encoding="utf-8"))
        d["toc"] = toc
        d["chapterCount"] = len(files)
        d["chapterTitles"] = [ch["title"] for ch in files.values()]
        json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
        print(f"✓ book_detail 更新: {p}")

if os.path.exists(BOOKS_JSON):
    bj = json.load(open(BOOKS_JSON, encoding="utf-8"))
    bl = bj if isinstance(bj, list) else bj.get("books", [])
    hit = False
    for b in bl:
        if b.get("id") == BID:
            b["chapterCount"] = len(files)
            hit = True
    if hit:
        with open(BOOKS_JSON, "w", encoding="utf-8") as f:
            json.dump(bl if isinstance(bj, list) else {**bj, "books": bl}, f, ensure_ascii=False, indent=None)
        print("✓ books.json chapterCount 更新")
    else:
        print("⚠ books.json 未找到该书")
