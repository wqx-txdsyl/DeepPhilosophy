# -*- coding: utf-8 -*-
"""《忧郁的热带》（列维-斯特劳斯，中国人民大学出版社 2009）b146b56d2718 重建（一次性，旧数据重组）
旧数据 46 章平铺：0 版权信息（331 字纯元数据）+ 1 总 序 + 2-5 插图目录 4 页
（卡都卫欧族/波洛洛族/南比克瓦拉族/吐比卡瓦希普族 = 书前插图总目录分族页，
100-279 字图题+图，h1 族名）+ 6-45 四十章正文。缺 9 部（part）层级。
EPUB 源（F:/philosophy/西方/克洛德·列维-斯特劳斯/忧郁的热带.epub）验证（spine 57 = titlepage +
目录页 + part0000-0055；ncx 55 条）:
  原书九部：第一部 结束旅行（一~五章）/第二部 行脚小注（六~八章）/第三部 新世界（九~十二章）/
  第四部 地球及其居民（十三~十七章）/第五部 卡都卫欧族（十八~二十章）/第六部 波洛洛族
  （二十一~二十三章）/第七部 南比克瓦拉族（二十四~二十九章）/第八部 吐比卡瓦希普族
  （三十~三十六章）/第九部 归返（三十七~四十章）。ncx 缺 9 个章条目（一 出发/五 回顾/
  八/十二/十七/二十一/二十四/三十/三十七），归属用 spine 位置（part0008/0013/0017/0022/0028/
  0033/0037/0044/0052 在部标题页后）确认，与旧文件序（旧 N = spine N+2）一一对应。
  卡都卫欧族等四页 = 书前插图目录（含 10/17 张图+图题），非正文附录——CHKLIST"末尾四章
  排在最前"系误判（源即置于书首），但四页平铺且与第五~八部 part 同名确需归类。
重建:
  [ch] 0 总 序（无 part）
  [ch] 1 插图目录（旧 2-5 四页拼接，图+图题原样）
  [part] ×9（ncx 部标题）
    [ch] 四十章（旧 6-45，逐 block 原样）
  删 0 版权信息（纯元数据）。cc 46 → 42 + 9 part。
用法: python _xr_yrrd_rebuild.py [--dry]
"""
import json, os, re, sys, shutil

BID = "b146b56d2718"
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
assert len(old) == 46, len(old)

# ---- 尾部剥离：旧数据各文件尾粘入下一部标题页块（spine 部标题页在上一部末章后）----
#   5(吐比卡瓦希普族插图目录)尾 = "第一部 结束旅行"；9/12/16/21/25/28/34/41 同理
STRIP_TAIL = {5: 1, 9: 1, 12: 1, 16: 1, 21: 1, 25: 1, 28: 1, 34: 1, 41: 1}
for fn, n in STRIP_TAIL.items():
    for _ in range(n):
        old[fn]["content"].pop()

# ---- 结构表 ----
STANDS = [                      # 独立章（无 part）
    ("总 序", [1]),
    ("插图目录", [2, 3, 4, 5]),  # 旧 2-5 = 书前插图目录四页（图+图题）拼接
]
VOLS = [
    ("第一部 结束旅行", [
        ("一 出发", [6]), ("二 船上", [7]), ("三 西印度群岛", [8]),
        ("四 追寻权力", [9]), ("五 回顾", [10]),
    ]),
    ("第二部 行脚小注", [
        ("六 一个人类学家的成长", [11]), ("七 日落", [12]), ("八 郁闷的赤道无风带", [13]),
    ]),
    ("第三部 新世界", [
        ("九 瓜那巴拉湾", [14]), ("十 穿越回归线", [15]), ("十一 圣保罗市", [16]),
        ("十二 城与乡", [17]),
    ]),
    ("第四部 地球及其居民", [
        ("十三 前锋地带", [18]), ("十四 魔毯", [19]), ("十五 人群", [20]),
        ("十六 市场", [21]), ("十七 帕拉那邦", [22]),
    ]),
    ("第五部 卡都卫欧族", [
        ("十八 潘塔那勒沼泽区", [23]), ("十九 首府那力客", [24]),
        ("二十 一个土著社会及其生活风格", [25]),
    ]),
    ("第六部 波洛洛族", [
        ("二十一 黄金与钻石", [26]), ("二十二 有美德的野蛮人", [27]),
        ("二十三 生者与死者", [28]),
    ]),
    ("第七部 南比克瓦拉族", [
        ("二十四 失去的世界", [29]), ("二十五 在塞尔陶", [30]), ("二十六 沿着电报线", [31]),
        ("二十七 家庭生活", [32]), ("二十八 一堂书写课", [33]),
        ("二十九 男人、女人与酋长", [34]),
    ]),
    ("第八部 吐比卡瓦希普族", [
        ("三十 独木舟之旅", [35]), ("三十一 鲁滨孙", [36]), ("三十二 在森林之中", [37]),
        ("三十三 蟋蟀的村落", [38]), ("三十四 贾宾鸟的闹剧", [39]), ("三十五 亚马孙流域", [40]),
        ("三十六 谢林葛尔", [41]),
    ]),
    ("第九部 归返", [
        ("三十七 奥古斯都封神记", [42]), ("三十八 一小杯朗姆酒[1]", [43]),
        ("三十九 塔希拉遗址", [44]), ("四十 缅甸佛寺基荣之旅", [45]),
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
assert n_part == 9, n_part
assert len(files) == 42, len(files)
used = sorted(s for _, chs in VOLS for _, srcs in chs for s in srcs) + [1, 2, 3, 4, 5]
assert len(used) == len(set(used)), "源文件重复使用"
for i in sorted(files):
    assert i == files[i]["index"], "index 连续"

total_chars = 0
for i in sorted(files):
    nc = sum(len(b.get("value", "")) for b in files[i]["content"])
    total_chars += nc
    print(f"  {i:2d} {files[i]['title'][:44]:46s} {nc:7d} 字")
print(f"总: {len(files)} 章 + {n_part} part, {total_chars} 字符（旧 46 章平级, cc 46→42）")
old_total = sum(sum(len(b.get("value", "")) for b in old[i]["content"]) for i in old)
print(f"旧数据总字数: {old_total}（删 0 版权信息 {sum(len(b.get('value','')) for b in old[0]['content'])} 字）")
for t in toc:
    ind = "  " * t.get("level", 1)
    print(f"{ind}[{t['type']}] {t['title'][:44]}")
print("首:", files[0]["title"], "| 末:", files[41]["title"])

if "--dry" in sys.argv:
    RESIDUE_NORMS = {"版权信息", "目录"}
    title_norms = {norm(t["title"]) for t in toc}
    n_res = 0
    for i, ch in files.items():
        for k, b in enumerate(ch["content"]):
            if "value" not in b or not b["value"]:
                continue
            nv = norm(b["value"])
            prev = ch["content"][k - 1] if k > 0 else {}
            if nv in RESIDUE_NORMS or re.fullmatch(r"第[一二三四五六七八九十]+部\S*", nv):
                print(f"⚠ 疑似残留 [{i} {ch['title'][:12]}]: {b['value'][:34]!r}")
                n_res += 1
            # 章标题整块重复（正文首块粘章题行）；插图目录合并后图题可能含部名——仅报短块
            elif len(nv) <= 10 and nv in title_norms and prev.get("type") != "image":
                print(f"⚠ 疑似章题残留 [{i} {ch['title'][:12]}]: {b['value'][:34]!r}")
                n_res += 1
    print(f"残留: {n_res}")
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
    "title": old_meta.get("title") or "忧郁的热带",
    "author": old_meta.get("author") or "克洛德·列维-斯特劳斯",
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
