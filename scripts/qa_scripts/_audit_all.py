# -*- coding: utf-8 -*-
"""全库入库质量核查: 结构完整性/污染节/三端一致/book_detail 一致"""
import sys, os, json, hashlib
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
BASE = r"f:/program/Python/PhiAgent/backend"
CH = os.path.join(BASE, "data", "book_chapters")
PHI_DET = os.path.join(BASE, "data", "book_detail")
DP_BACKEND = r"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend"
DP_PUBLIC = r"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public"

def words_of_ch(c):
    return sum(len(x.get("value", "")) for x in c.get("content", []) if x.get("type") == "text")

bad = []
one_chap = []
short_sec = []
for bid in sorted(os.listdir(CH)):
    bd = os.path.join(CH, bid)
    if not os.path.isdir(bd):
        continue
    mfp = os.path.join(bd, "meta.json")
    if not os.path.exists(mfp):
        bad.append((bid, "缺 meta.json")); continue
    meta = json.load(open(mfp, encoding="utf-8"))
    title = meta.get("title", "")[:18]
    n = meta.get("chapterCount", -1)
    # 1. 文件连续性
    files = [f for f in os.listdir(bd) if f.endswith(".json") and f != "meta.json"]
    idxs = sorted(int(f[:-5]) for f in files)
    if idxs != list(range(max(idxs) + 1)) or len(idxs) != n:
        bad.append((bid, title, f"index 不连续/数量不符 meta={n} 实际={len(idxs)}"))
        continue
    # 1.5 toc 一致性（chapter 条目数 == chapterCount, index 连续; part 分组合法）
    toc = meta.get("toc", [])
    ch_toc = [t for t in toc if (t.get("type") if isinstance(t, dict) else "chapter") == "chapter"]
    ch_idx = [t.get("index") if isinstance(t, dict) else None for t in ch_toc]
    if all(i is None for i in ch_idx):
        ch_idx = list(range(len(ch_toc)))
    if len(ch_idx) != n or ch_idx != list(range(len(ch_idx))):
        bad.append((bid, title, f"toc chapter 条目 {len(ch_idx)} != chapterCount {n} 或 index 不连续"))
    # 2. 每章字数
    total = 0
    for i in idxs:
        c = json.load(open(os.path.join(bd, f"{i}.json"), encoding="utf-8"))
        w = words_of_ch(c)
        total += w
        if w < 80 and n > 1:
            short_sec.append((bid, title, i, c.get("title"), w))
    if n < 2:
        one_chap.append((bid, title, total))
    # 3. 三端一致（对比 DP backend + public 的 meta chapterCount + 各章 index）
    for tag, base in (("DP后端", DP_BACKEND), ("DPpublic", os.path.join(DP_PUBLIC, "backend"))):
        dbd = os.path.join(base, "data", "book_chapters", bid)
        if not os.path.isdir(dbd):
            bad.append((bid, title, f"{tag} 缺 book_chapters"))
            continue
        dmeta = json.load(open(os.path.join(dbd, "meta.json"), encoding="utf-8"))
        if dmeta.get("chapterCount") != n:
            bad.append((bid, title, f"{tag} chapterCount {dmeta.get('chapterCount')} != {n}"))
            continue
        # 抽样比 3 章内容 md5
        for i in (0, n // 2, n - 1):
            a = json.dumps(json.load(open(os.path.join(bd, f"{i}.json"), encoding="utf-8")), ensure_ascii=False)
            b = json.dumps(json.load(open(os.path.join(dbd, f"{i}.json"), encoding="utf-8")), ensure_ascii=False)
            if a != b:
                bad.append((bid, title, f"{tag} 第{i}章内容不一致")); break
    # 4. book_detail 一致性
    det_found = False
    for detp in (os.path.join(PHI_DET, f"{bid}.json"),
                 os.path.join(DP_BACKEND, "data", "book_detail", f"{bid}.json"),
                 os.path.join(DP_PUBLIC, "book_detail", f"{bid}.json")):
        if os.path.exists(detp):
            det_found = True
            det = json.load(open(detp, encoding="utf-8"))
            if det.get("chapterCount") != n:
                bad.append((bid, title, f"{os.path.basename(os.path.dirname(os.path.dirname(detp)))} book_detail chapterCount {det.get('chapterCount')} != {n}"))
            if det.get("chapterTitles") != meta.get("chapterTitles"):
                bad.append((bid, title, f"book_detail chapterTitles 与 meta 不符 ({os.path.basename(detp)})"))
    if not det_found:
        bad.append((bid, title, "三端均无 book_detail"))

print("== 结构/一致性问题 ==")
for b in bad:
    print("✗", b)
print(f"共 {len(bad)} 个问题")
print("\n== 1 章未切分 ==")
for bid, t, w in one_chap:
    print(f"· {bid} {t!r} {w}字")
print(f"共 {len(one_chap)} 本")
print("\n== 短节(<80字) 污染候选 ==")
for bid, t, i, ct, w in short_sec:
    print(f"· {bid} {t!r} 第{i}章 {ct!r} {w}字")
print(f"共 {len(short_sec)} 个")
