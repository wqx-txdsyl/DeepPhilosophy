# -*- coding: utf-8 -*-
"""政治学（53b09f03e24e）抽查15修复：竖排书全量重建
病因: 竖排 PDF（每行 1-2 字逐字提取），原切章脚本把'含章标题行的整页归新章'
  → 每章首段 = 上一章尾部内容（章一'品种方面…'被切进章二），且注释内联在正文段。
修复: ① 按块流（pymupdf get_text('dict')，竖排每行一块，块序=正文→注释→页眉）
       剥页眉（'N政治学'/'卷（X）N'/纯页码）
      ② 注释区识别：块序中 prev 块底 y 与 next 块顶 y 间隙 >15 → 注释起始；
       注释块拼接为独立注释段（跳过纯注标块'①'），正文块拼接为正文段（每页一段）
      ③ 章切分：正文块首匹配 ^章[一二三四五六七八九十]+ → 新章（剥标题）；
       '卷（X）章X'标题页剥卷标题；块首 ^卷（X）N 书眉剥除
      ④ toc 结构不变（104 项：序+8 卷 part+103 章），按 cur_vol/cur_ch 映射填充
   保留: 正文内联注标（'方法①'）、原书页码结构；序章（吴恩裕序）已存在不动
用法: python _xr_53b09f03e24e_politics_rebuild.py [--dry]
"""
import json, os, re, sys, shutil

BID = "53b09f03e24e"
PDF = "F:/philosophy/西方/亚里士多德/政治学.pdf"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DST2 = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"
PAGE_FROM = 19          # PDF 页索引（页20 = 卷一章一，页19 = 目录页跳过）
PAGE_TO = 498           # 正文止于页497（'本卷和全书在这里终止'）；页498 起 = 附录一摘要 + 附录二（弃）

CN = "一二三四五六七八九十"
VNUM = "一二三四五六七八九十ＢＩⅠB"    # PDF 文本层把中文数字误识别为 B/I（半角/全角）
VOL_RE = re.compile(rf"^卷（[{VNUM}][）)]?[０-９0-9]*$")   # 书眉 '卷（一）3'
VOLTITLE_RE = re.compile(rf"^卷（[{VNUM}]）(?:章[{CN}]+)?$")  # 卷标题页 '卷（B）一'
CHAPTITLE_RE = re.compile(rf"^章[{CN}]+")                 # 章标题 '章二这样…'
PAGEHEAD_RE = re.compile(r"^[０-９0-9]*政治学$")          # 页眉 '２政治学'
PAGENO_RE = re.compile(r"^[０-９0-9]+$")                  # 页码 '２'
NOTEMARK_RE = re.compile(r"^[①②③④⑤⑥⑦⑧⑨⑩]+$")       # 纯注标块

CNMAP = {"一":1,"二":2,"三":3,"四":4,"五":5,"六":6,"七":7,"八":8,"九":9,"十":10,
         "Ｂ":1,"Ｉ":1,"Ⅰ":1,"B":1}
def num(cn):
    """'一'→1 '十'→10 '十三'→13 '二十'→20 '二十五'→25"""
    if cn in CNMAP:
        return CNMAP[cn]
    if "十" in cn:
        i = cn.index("十")
        pre = num(cn[:i]) if i > 0 else 1
        post = num(cn[i+1:]) if i + 1 < len(cn) else 0
        return pre * 10 + post
    return 0

def clean(t):
    return "".join(t.split())

def parse_ch_digits(s):
    """'一二…' 取最长有效前缀章号（'章一一切技艺' → '一'=1，贪婪会吃成'一一'=0）"""
    ch, take = 0, 0
    for k in range(1, len(s) + 1):
        v = num(s[:k])
        if v > 0:
            ch, take = v, k
    return ch, take

meta0 = json.load(open(os.path.join(SRC, "meta.json"), encoding="utf-8"))
toc = meta0["toc"]
# chapter 节点列表（type=='chapter'，排除 part；序章是 chapter 但内容已建，正文映射从卷1章1开始）
chapters = [t for t in toc if t.get("type") == "chapter"]
parts = [t for t in toc if t.get("type") == "part"]
print(f"toc: {len(toc)} 项 = {len(parts)} part + {len(chapters)} chapter（含序章）+ 序章 = 104")

import fitz
doc = fitz.open(PDF)

# 每章: 正文段列表 + 注释段列表（顺序保持：正文段+注释段交替插入）
ch_paras = {i: [] for i in range(meta0["chapterCount"])}
cur = None          # 当前章 index（toc 中 chapter 节点的顺序位置→index）
vol, ch = 1, 1
prev_ch = 0         # 上一个章号（卷内；0=初始）
chap_idx = {1: 0}   # 备用
seq = 0             # chapter 节点游标（0=序章，1=卷1章1…）
paras_in_ch = {}
verbose = {}

for pno in range(PAGE_FROM, PAGE_TO):
    d = doc[pno].get_text("dict")
    blocks = [b for b in d["blocks"] if b["type"] == 0]
    # 剥页眉/页码/书眉
    kept = []
    seen = set()
    for b in blocks:
        t = clean("".join(s["text"] for l in b["lines"] for s in l["spans"]))
        if not t:
            continue
        if PAGEHEAD_RE.match(t) or PAGENO_RE.match(t) or VOL_RE.match(t):
            continue
        if t in seen:           # PDF 文本层重复提取（页40 '①。这里' x77.7/x90.1 双份）
            continue
        seen.add(t)
        kept.append((b, t))
    if not kept:
        continue
    # 卷标题页 '卷（B）一'/'卷（E）四' 等 → 更新卷号，块剥除不入正文
    #   OCR 噪声把括号内卷号识别成 B/C/D/E/Ｅ/Z/H/I（无规律），但括号外是正确中文卷号
    kept2 = []
    for b, t in kept:
        mt = re.match(r"^卷（[^）]{1,2}）([一二三四五六七八九十])$", t)
        if mt:
            vol = num(mt.group(1))
            prev_ch = 0             # 卷切换：卷内章号重置
            print(f"  ℹ 页{pno+1} 卷标题 → 卷{vol}（{t!r}）")
        else:
            kept2.append((b, t))
    kept = kept2
    # 注释识别（竖排书特征：正文注标在行首，块首①不区分正文/注释；注释块穿插正文流）：
    #   ① gap 注释区（块序中 prev 底→next 顶 间隙>15）内、非'章X'块 → 注释
    #      —— 页21 '章二这样'(y413) / 页44 '章九'(y197) 是正文（章首块豁免）
    #   ② gap 区内'章X'块按章号连续性裁决：连续=真标题进正文（页34 '章六' y464 卷1六章标题）；
    #      不连续=注释引用进注释区（页57 '章三至七。' 页219 '章八。此节持论' 页224 '章三加删除括弧'）
    #   ③ 纯注标块 '①' → 丢；其余 → 正文（页460/466/469 正文块以①开头是常态）
    gap_start = len(kept)
    for i in range(1, len(kept)):
        if kept[i][0]["bbox"][1] - kept[i-1][0]["bbox"][3] > 15:
            # 章标题上方的空行（gap）是排版常规，不是注释区起点
            #   （页38 '章七' y238 22字 / 页44 '章九' y196 / 页34 '章六' y464 21字 / 页106 '章九' 纯标题2字）
            #   注释引用块（'章三至七。' 5字 页57）不跳过——它在注释区起点，跳过会把它放回正文区
            if re.match(r"^章[一二三四五六七八九十]+", kept[i][1]):
                mrest = re.match(r"^章[一二三四五六七八九十]+", kept[i][1])
                rest = kept[i][1][mrest.end():]
                if not rest or len(kept[i][1]) > 10:
                    continue
            gap_start = i
            break
    body_parts, note_parts = [], []
    for bi, (b, t) in enumerate(kept):
        if NOTEMARK_RE.match(t):
            continue
        mch = re.match(r"^章([一二三四五六七八九十]+)", t)
        in_gap = bi >= gap_start
        if in_gap and mch:
            ch_b, _ = parse_ch_digits(mch.group(1))
            rest = t[mch.end():]
            if rest and not re.match(r"^[一-鿿]", rest):
                note_parts.append(t)  # 章号后非中文开头 = 注释引用（页31 '章五。这里的"行为"…' 页219 '章八。此节持论' 页100 '章九２）。'）
            elif ch_b == prev_ch + 1 or (ch_b == 1 and prev_ch == 0):
                body_parts.append(t)      # 连续章号 = 真标题（页34 '章六' y464）
            else:
                note_parts.append(t)      # 不连续章号 = 注释引用块（页57 '章三至七。'）
        elif in_gap:
            note_parts.append(t)
        else:
            body_parts.append(t)          # 正文块
    body_txt = "".join(body_parts)
    note_txt = "".join(note_parts)
    if not body_txt:
        continue
    def do_switch(new_ch, t2):
        """换章：校验连续性 → 映射 toc chapter index → 更新 cur/prev_ch"""
        global cur, prev_ch
        # 8 卷章号全连续（13/12/18/16/12/8/17/7），注释引用块（'章八。此节持论…'页219、
        #   '章九至十一…'页180 等）伪装章标题——不连续（回退或跳号）一律拒绝，仅卷首章1 例外
        if cur is not None and not (new_ch == 1 and prev_ch == 0) and new_ch != (prev_ch + 1):
            print(f"  ⚠ 页{pno+1} 章号不连续? 卷{vol} 章{prev_ch}→章{new_ch}（注释引用）→ 拒绝 {t2[:20]!r}")
            return
        prev_ch = new_ch
        target = None
        n = 1
        for i, c in enumerate(toc):
            if c.get("type") == "part":
                mt = re.search(r"[一二三四五六七八九十]+", c.get("title") or "")
                n = num(mt.group(0)) if mt else 0
                continue
            if c.get("type") == "chapter" and i > 0:
                mt = re.search(r"[一二三四五六七八九十]+", c.get("title") or "")
                if n == vol and new_ch == (num(mt.group(0)) if mt else 0):
                    target = c
                    break
        if target is None:
            print(f"  ⚠ 页{pno+1} 找不到 toc 章 卷{vol}章{new_ch}（{t2[:20]!r}）")
        else:
            cur = target["index"]

    # 页内切章：正文块序列中，块首章标题 → 换章；块内'章X'（页40 '…。章八前面已经说明'）→ 切块换章
    for t in body_parts:
        t2 = t
        m = re.match(r"^章([一二三四五六七八九十]+)", t2)
        if m:                      # '章二这样…' → 剥标题，章号=卷内章号
            ch, take = parse_ch_digits(m.group(1))
            t2 = t2[1 + take:]
            if ch == prev_ch:
                prev_ch = ch            # 同章重复标题（标题页+正文首块）→ 仅剥标题，不重复映射
            else:
                do_switch(ch, t2)
        else:
            mm = re.search(r"章([一二三四五六七八九十]+)", t2)
            if mm:                 # 块内章标题（页40 卷1章八藏块中）
                ch2, take = parse_ch_digits(mm.group(1))
                if ch2 == prev_ch + 1 and cur is not None:   # 连续性校验：真标题才切（防正文引用误切）
                    head, tail = t2[:mm.start()], t2[mm.start() + 1 + take:]
                    if head:
                        ch_paras[cur].append(("p", pno + 1, head))
                    do_switch(ch2, tail)
                    t2 = tail
        if t2 and cur is not None:
            ch_paras[cur].append(("p", pno + 1, t2))
    # 注释段归属：本页最后正文块所属章
    if note_txt and cur is not None:
        ch_paras[cur].append(("n", pno + 1, note_txt))

# 按 toc chapter 顺序重建 content
missing = []
for c in toc:
    if c.get("type") != "chapter":
        continue
    i = c["index"]
    if i == 0:
        continue  # 序章不动
    ps = ch_paras.get(i, [])
    if not ps:
        missing.append(i)
    n = sum(len(t) for _k, _p, t in ps if _k == "p")
    print(f"[{i}] {c['title'][:6]} {n:6d}字 {len(ps):3d}段 ({len([1 for _ in ps if _[0]=='n'])}注释)")
print("空章:", missing if missing else "无")

if "--dry" in sys.argv:
    import tempfile
    tgt = os.path.join(tempfile.gettempdir(), "politics_new.json")
    json.dump({str(i): [(k, pn, t) for k, pn, t in ch_paras[i]] for i in ch_paras},
              open(tgt, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"dry dump → {tgt}")
    sys.exit(0)

# 写入
if os.path.isdir(SRC):
    suf = "_old_bad"
    i2 = 2
    while os.path.isdir(SRC + suf):
        suf = f"_old_bad{i2}"
        i2 += 1
    os.rename(SRC, SRC + suf)
    print(f"\n备份 → {os.path.basename(SRC) + suf}")
os.makedirs(SRC)
for c in toc:
    if c.get("type") != "chapter":
        continue
    i = c["index"]
    content = [{"type": "text", "value": t} for _, _, t in ch_paras.get(i, [])]
    json.dump({"index": i, "title": c["title"], "content": content},
              open(os.path.join(SRC, f"{i}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
json.dump(meta0, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print(f"✓ 写入 {SRC}: {meta0['chapterCount']} 章（toc 不变）")

shutil.rmtree(DST, ignore_errors=True); shutil.copytree(SRC, DST)
shutil.rmtree(DST2, ignore_errors=True); shutil.copytree(SRC, DST2)
print("✓ 同步 DST/DST2")
