# -*- coding: utf-8 -*-
"""形而上学 f11f1b13c278 全量重构 (2026-08-08)
问题: 68 章 = 6 目录残留 + 62 正文, 章名被 OCR 页眉污染(第X卷(X)1第X章/京=章/希腊字母错),
      整卷压一文件(A/B/E/H/I/K/N 卷各并 1 文件), 切半章 6 对, B 卷章6 段序错乱, 索引残留混入 N 卷尾
方案: 14 卷 part + 131 章 chapter(卷内"第X章") + 2 索引章
      章边界来自 Bekker 页码 + 内嵌标题行定位(逐段人工核对)
内容零丢失: 旧目录全备份; 仅剔除: [0]-[5] 书前目录残留 + 卷首目录段 + 纯页眉短行 + 章首段标题前缀
"""
import sys, json, os, re, shutil
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"f:\program\Python\PhiAgent\backend\tools")
import rebuild_auto as ra

BID = "f11f1b13c278"
D = os.path.join(ra.CH, BID)
BAK = os.path.join(r"f:\program\Python\PhiAgent\backend\data\_rebuild_bak", f"{BID}_v1")
if not os.path.exists(BAK):
    shutil.copytree(D, BAK)
    print(f"备份 → {BAK}")

# 旧文件全部缓存到内存(新文件编号与旧重叠, 必须先读完再写)
OLD = {}
for f in os.listdir(D):
    if f.endswith(".json") and f != "meta.json":
        OLD[int(f[:-5])] = json.load(open(os.path.join(D, f), encoding="utf-8"))

def load(idx):
    return OLD[idx]

def texts(idx):
    return [b["value"] for b in load(idx)["content"] if b.get("type") == "text"]

def segs(idx, rng):
    ts = texts(idx)
    return ts[rng[0]:rng[1] + 1] if isinstance(rng, tuple) else [ts[i] for i in rng]

# 纯页眉短行: "第一卷（A）"/"第五卷（）"/"第十—卷（K）" 等
HEADER = re.compile(r"^[1丨|]*第[一二三四五六七八九十百—]+[卷章园][（(]?[A-Za-zΔ△ΓγΘθΛΞΠΣΦΨΩαβγδεζηθικλμνξοπρστυφχψω]?[）)]?[1丨|]*$")
# 段内页眉+标题前缀: "第八卷（H）1第四章锯。但是…" → 剥到"第四章"后
PRE = re.compile(r"^(?:[1丨|]*第[一二三四五六七八九十百—]+[卷章园][（(]?[A-Za-zΔ△ΓγΘθΛΞΠΣΦΨΩαβγδεζηθικλμνξοπρστυφχψω]?[）)]?[1丨|]*)*[1丨|]*第[一二三四五六七八九十百]+[章京](?=[^\s，。、的是也在中有和及与])")
# 卷首目录串: "第五卷（△)第一章第二章…第三十章" / "第七卷 (Z)第一章…第十七章*正文" → 剥离目录串(保留尾部正文)
TOCCHAIN = re.compile(r"^(?:第[一二三四五六七八九十百]+[卷章园]\s*[（(]?[^\s（(）)]{0,3}?[）)]?)?(?:第[一二三四五六七八九十百]+[章京]){3,}")

def strip_head(head, ch_title):
    """章首段剥离页眉/标题前缀. 规则依次尝试:
    1. 页眉卷章+标题 (PRE)
    2. 去空白以 toc 章名开头 (合并章拆名)
    3. 前导脚注(≤10字符)+'第X章'+页码标记 → 保留脚注
    4. 前导分隔符(≤4字符)+'第X章' (如 '）1第二章')
    """
    m = PRE.match(head)
    if m and head[m.end():].strip():
        return head[m.end():]
    dw = re.sub(r"\s+", "", head)
    for nm in ch_title.split("、"):
        dp = re.sub(r"\s+", "", nm)
        if dp and dw.startswith(dp) and len(dw) > len(dp):
            cnt = 0
            for k, ch in enumerate(head):
                if not ch.isspace():
                    if cnt == len(dp):
                        return head[k:]
                    cnt += 1
    m3 = re.match(r"^([^\s]{0,10}?)第[一二三四五六七八九十百]+[章京](?=[0-9°*])", head)
    if m3 and head[m3.end():].strip():
        return m3.group(1) + head[m3.end():]
    m4 = re.match(r"^[1丨|）)\]】>·,:：;；．。]{0,4}?第[一二三四五六七八九十百]+[章京]", head)
    if m4 and head[m4.end():].strip():
        return head[m4.end():]
    return head

def clean(paras, chapter_title):
    """页眉短行剔除 + 目录串剥离 + 段内页眉/标题前缀剥离(防误伤'第九章是空谈'式正文)"""
    out = []
    for t in paras:
        # 1. 卷首目录串(整段是目录 → 删; 目录+正文 → 留正文)
        m = TOCCHAIN.match(t)
        if m and len(t[m.end():].strip()) < 10:
            continue
        if m:
            t = t[m.end():]
        # 2. 纯页眉短行
        if HEADER.match(t.strip()):
            continue
        # 3. 段内页眉+标题前缀(非首段也可能有: '第七卷（Z)1第一章物的话…')
        m = PRE.match(t)
        if m:
            t = t[m.end():]
            if not t.strip():
                continue
        out.append(t)
    return out

# ============ 卷结构 ============
# 每卷: (part名, [(目标章名, [(源文件, 段范围/列表)...])...])
V = {}

# 第一卷（A）: [6] 9 章 + [7] 并章9
V["第一卷（A）"] = [
    (f"第{i}章", []) for i in range(1, 9)
]
V["第一卷（A）"] = [
    ("第一章", [(6, (0, 12))]),
    ("第二章", [(6, (13, 19))]),
    ("第三章", [(6, (20, 38))]),
    ("第四章", [(6, (39, 56))]),
    ("第五章", [(6, (57, 63))]),
    ("第六章", [(6, (64, 75))]),
    ("第七章", [(6, (76, 81))]),
    ("第八章", [(6, (82, 99))]),
    ("第九章", [(6, (100, 125)), (7, (0, 16))]),
]
# 第二卷（α）: [8] 3 章
V["第二卷（α）"] = [
    ("第一章", [(8, (0, 10))]),
    ("第二章", [(8, (11, 19))]),
    ("第三章", [(8, (20, 21))]),
]
# 第三卷（B）: [9] 6 章(章6 段序重排: 36-52, 60, 61, 59, 53-58)
V["第三卷（B）"] = [
    ("第一章", [(9, (0, 6))]),
    ("第二章", [(9, (7, 13))]),
    ("第三章", [(9, (14, 20))]),
    ("第四章", [(9, (21, 28))]),
    ("第五章", [(9, (29, 35))]),
    ("第六章", [(9, list(range(36, 53)) + [60, 61, 59] + list(range(53, 59)))]),
]
# 第四卷（Γ）: [10]-[16]
V["第四卷（Γ）"] = [
    ("第一章", [(10, (0, 6))]),
    ("第二章", [(11, (0, 12))]),
    ("第三章", [(12, (0, 5))]),
    ("第四章", [(13, (0, 40))]),
    ("第五章", [(14, (0, 16)), (15, (0, 4))]),
    ("第六章", [(16, (0, 2))]),
    ("第七章", [(16, (3, 4))]),
    ("第八章", [(16, (5, 10))]),
]
# 第五卷（Δ）: [18]-[25]
V["第五卷（Δ）"] = [
    ("第一章", [(18, (0, 4))]),
    ("第二章", [(19, (0, 5))]),
    ("第三章", [(19, (6, 7))]),
    ("第四章", [(19, (8, 16))]),
    ("第五章", [(20, (0, 3))]),
    ("第六章", [(21, (0, 13))]),
    ("第七章", [(21, (14, 23))]),
    ("第八章", [(21, (24, 29))]),
    ("第九章", [(21, (30, 39))]),
    ("第十章", [(21, (40, 48))]),
    ("第十一章", [(21, (49, 56))]),
    ("第十二章", [(21, (57, 58)), (22, (0, 9))]),
    ("第十三章", [(22, (10, 12))]),
    ("第十四章", [(22, (13, 17))]),
    ("第十五章", [(22, (18, 23)), (23, (0, 2))]),
    ("第十六章", [(23, (3, 4)), (24, (0, 0))]),
    ("第十七章", [(24, (1, 2))]),
    ("第十八章", [(24, (3, 5))]),
    ("第十九章", [(24, (6, 6))]),
    ("第二十章、第二十一章", [(24, (7, 8))]),
    ("第二十二章", [(24, (9, 10)), (25, (0, 0))]),
    ("第二十三章、第二十四章", [(25, (1, 6))]),
    ("第二十五章", [(25, (7, 8))]),
    ("第二十六章", [(25, (9, 13))]),
    ("第二十七章", [(25, (14, 19))]),
    ("第二十八章", [(25, (20, 26))]),
    ("第二十九章", [(25, (27, 33))]),
    ("第三十章", [(25, (34, 37))]),
]
# 第六卷（E）: [26] 4 章
V["第六卷（E）"] = [
    ("第一章", [(26, (0, 8))]),
    ("第二章", [(26, (9, 13))]),
    ("第三章", [(26, (14, 15))]),
    ("第四章", [(26, (16, 18))]),
]
# 第七卷（Z）: [27]-[41] (章1 含段0: 目录串剥离后为正文首段)
V["第七卷（Z）"] = [
    ("第一章", [(27, (0, 15))]),
    ("第二章", [(27, (16, 17))]),
    ("第三章", [(28, (0, 10))]),
    ("第四章、第五章", [(29, (0, 22))]),
    ("第六章", [(30, (0, 8))]),
    ("第七章", [(31, (0, 17))]),
    ("第八章", [(32, (0, 17))]),
    ("第九章", [(33, (0, 2))]),
    ("第十章", [(34, (0, 12))]),
    ("第十一章", [(35, (0, 12))]),
    ("第十二章", [(36, (0, 7))]),
    ("第十三章", [(37, (0, 20))]),
    ("第十四章", [(38, (0, 8)), (39, (0, 4))]),
    ("第十五章", [(40, (0, 8))]),
    ("第十六章", [(40, (9, 11))]),
    ("第十七章", [(40, (12, 17)), (41, (0, 1))]),
]
# 第八卷（H）: [42] 6 章
V["第八卷（H）"] = [
    ("第一章", [(42, (0, 12))]),
    ("第二章", [(42, (13, 27))]),
    ("第三章", [(42, (28, 32))]),
    ("第四章", [(42, (33, 38))]),
    ("第五章", [(42, (39, 46))]),
    ("第六章", [(42, (47, 48))]),
]
# 第九卷（Θ）: [43]-[49]
V["第九卷（Θ）"] = [
    ("第一章", [(43, (0, 4)), (44, (0, 6))]),
    ("第二章", [(44, (7, 11))]),
    ("第三章", [(44, (12, 17))]),
    ("第四章", [(45, (0, 2))]),
    ("第五章", [(46, (0, 4))]),
    ("第六章", [(44, (18, 22)), (47, (0, 9))]),
    ("第七章", [(47, (10, 14))]),
    ("第八章、第九章", [(48, (0, 39))]),
    ("第十章", [(49, (0, 0))]),
]
# 第十卷（I）: [50]
V["第十卷（I）"] = [
    ("第一章", [(50, (0, 31))]),
    ("第二章", [(50, (32, 41))]),
    ("第三章", [(50, (42, 61))]),
    ("第四章", [(50, (62, 76))]),
    ("第五章", [(50, (77, 83))]),
    ("第六章", [(50, (84, 96))]),
    ("第七章", [(50, (97, 101))]),
    ("第八章、第九章", [(50, (102, 111))]),
    ("第十章", [(50, (112, 113))]),
]
# 第十一卷（K）: [51]+[52]
V["第十一卷（K）"] = [
    ("第一章", [(51, (0, 13))]),
    ("第二章", [(51, (14, 25))]),
    ("第三章、第四章", [(51, (26, 28))]),
    ("第五章", [(51, (29, 42))]),
    ("第六章", [(51, (43, 57))]),
    ("第七章", [(51, (58, 59))]),
    ("第八章", [(51, (60, 78))]),
    ("第九章", [(51, (79, 88))]),
    ("第十章", [(51, (89, 91))]),
    ("第十一章", [(51, (92, 103))]),
    ("第十二章", [(52, (0, 4))]),
]
# 第十二卷（Λ）: [53]-[61]
V["第十二卷（Λ）"] = [
    ("第一章", [(53, (0, 1)), (54, (0, 7))]),
    ("第二章", [(54, (8, 13))]),
    ("第三章", [(54, (14, 17))]),
    ("第四章", [(54, (18, 30))]),
    ("第五章", [(55, (0, 17))]),
    ("第六章", [(56, (0, 6))]),
    ("第七章", [(57, (0, 11)), (58, (0, 3))]),
    ("第八章、第九章", [(59, (0, 15)), (60, (0, 17))]),
    ("第十章", [(60, (18, 24)), (61, (0, 8))]),
]
# 第十三卷（M）: [62]-[64]
V["第十三卷（M）"] = [
    ("第一章", [(62, (0, 9))]),
    ("第二章", [(62, (10, 25))]),
    ("第三章", [(62, (26, 41))]),
    ("第四章", [(62, (42, 46))]),
    ("第五章", [(63, (0, 11))]),
    ("第六章、第七章、第八章", [(64, (0, 52))]),
    ("第九章、第十章", [(64, (53, 66))]),
]
# 第十四卷（N）: [65] 6 章(段99-101 索引残留移入术语索引)
V["第十四卷（N）"] = [
    ("第一章", [(65, (0, 16))]),
    ("第二章", [(65, (17, 44))]),
    ("第三章", [(65, (45, 52))]),
    ("第四章", [(65, (53, 72))]),
    ("第五章", [(65, (73, 79))]),
    ("第六章", [(65, (80, 98))]),
]

# ============ 索引残留迁移: [65] 段99-101 → [66] 头部 ============
idx_j = load(66)
idx_texts = texts(66)
residual = texts(65)[99:102]
new_idx = residual + idx_texts
idx_j["content"] = [{"type": "text", "value": t} for t in new_idx]
print(f"术语索引: 头部加入 N 卷尾残留 {len(residual)} 段, 共 {len(new_idx)} 段")
# 清理索引章首段前缀
m2 = PRE.match(new_idx[0])
if m2:
    idx_j["content"][0]["value"] = new_idx[0][m2.end():]

# ============ 生成章文件 ============
total_chars = 0
new_toc = []
idx = 0
for part_name, chs in V.items():
    new_toc.append({"type": "part", "title": part_name, "level": 0})
    for ch_title, srcs in chs:
        paras = []
        for fn, rng in srcs:
            paras += segs(fn, rng)
        cleaned = clean(paras, ch_title)
        n_chars = sum(len(t) for t in cleaned)
        total_chars += n_chars
        # 章首段剥离页眉/标题前缀(剥后为空则弃该段, 循环处理后续段)
        while cleaned and not cleaned[0].strip():
            cleaned.pop(0)
        if cleaned:
            head = strip_head(cleaned[0], ch_title)
            if not head.strip():
                cleaned.pop(0)
            else:
                cleaned[0] = head
        content = [{"type": "text", "value": t} for t in cleaned]
        json.dump({"title": ch_title, "content": content, "index": idx},
                  open(os.path.join(D, f"{idx}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        new_toc.append({"type": "chapter", "title": ch_title, "index": idx, "level": 1})
        print(f"  [{idx}] {part_name} {ch_title}: 段{len(cleaned)} 字{n_chars}")
        idx += 1

# 索引 2 章
for t, jf in [("术语索引", idx_j), ("人名地名索引", load(67))]:
    paras = [b["value"] for b in jf["content"] if b.get("type") == "text"]
    n_chars = sum(len(t) for t in paras)
    total_chars += n_chars
    content = [{"type": "text", "value": t} for t in paras]
    json.dump({"title": t, "content": content, "index": idx},
              open(os.path.join(D, f"{idx}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    new_toc.append({"type": "chapter", "title": t, "index": idx, "level": 1})
    print(f"  [{idx}] {t}: 段{len(paras)} 字{n_chars}")
    idx += 1

# ============ 删除旧编号文件(备份已做) ============
for f in os.listdir(D):
    if f.endswith(".json") and f != "meta.json":
        try:
            n = int(f[:-5])
        except ValueError:
            continue
        if n >= idx:
            os.remove(os.path.join(D, f))
print(f"删除旧编号文件完成 (新章数 {idx})")

# ============ meta.json ============
m = json.load(open(os.path.join(D, "meta.json"), encoding="utf-8"))
m["chapterCount"] = idx
m["chapterTitles"] = [t["title"] for t in new_toc if t.get("type") == "chapter"]
m["toc"] = new_toc
json.dump(m, open(os.path.join(D, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"\nmeta: chapterCount={idx}, toc part={sum(1 for t in new_toc if t.get('type')=='part')} chapter={sum(1 for t in new_toc if t.get('type')=='chapter')}")
print(f"总字数: {total_chars}")
ra.sync_three(BID)
print("sync_three 完成")
