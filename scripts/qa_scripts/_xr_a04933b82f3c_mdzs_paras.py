# -*- coding: utf-8 -*-
"""孟德斯鸠分权论研究（a04933b82f3c）抽查16修复：行级段合并为语义段
病因: #89 重建按 PDF 物理行切段（中位 30 字，87% 段尾无句读）
  → 阅读器每段 <p> 缩进 2em + 段距，视觉上"每一行在大约一半的位置换行"。
修复: 段尾无句读（。！？；：…）→ 并入上一段；标题段（短 + 序号/章题模式）独立保留。
  toc/章节结构不动，仅重排 content 段粒度。
用法: python _xr_a04933b82f3c_mdzs_paras.py [--dry]
"""
import json, os, re, sys, shutil

BID = "a04933b82f3c"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DST2 = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

END = "。！？；：…．\"”』）》]"

def norm(s):
    return re.sub(r"\s+", "", s or "")

def is_title(v):
    """标题段：短（≤14 字）且匹配序号/章题模式 → 独立保留"""
    if len(v) > 14:
        return False
    if re.match(r"^第[一二三四五六七八九十百]+[章节篇部]", v):
        return True
    if re.match(r"^[一二三四五六七八九十]+[ 、．.\n]", v):
        return True
    if re.match(r"^（[一二三四五六七八九十]+）", v):
        return True
    if re.match(r"^[（(][0-9０-９]+[)）]", v):
        return True
    if re.match(r"^[0-9０-９]+[.、．]", v):
        return True
    return False

meta0 = json.load(open(os.path.join(SRC, "meta.json"), encoding="utf-8"))
chs = [json.load(open(os.path.join(SRC, f"{i}.json"), encoding="utf-8"))
       for i in range(meta0["chapterCount"])]
assert len(chs) == 6

# ---- 跨页断句补全：导言末'…必然"一词．孟' + 第一章首'德斯鸠暗中强化…' ----
for ci, c in enumerate(chs):
    if ci == 0:
        for b in reversed(c["content"]):
            v = b.get("value") or ""
            if v.endswith("孟"):
                b["value"] = v[:-1]
                print(f"✓ 导言末段截尾'孟'（{v[-24:]!r}）")
                break
    if ci == 1:
        b0 = c["content"][0]
        if b0["value"].startswith("德斯鸠"):
            b0["value"] = "孟" + b0["value"]
            print("✓ 第一章首段补'孟' →", repr(b0["value"][:20]))

# ---- 行级段合并 ----
for c in chs:
    out, prev_title = [], False
    for b in c["content"]:
        v = (b.get("value") or "").strip()
        if not v:
            continue
        if is_title(v):
            out.append(v)
            prev_title = True
            continue
        if out and not prev_title and out[-1][-1] not in END:
            out[-1] += v                    # 行级续接（物理行尾无句读）
            prev_title = False
        else:
            out.append(v)
            prev_title = False
    c["content"] = [{"type": "text", "value": v} for v in out]

# ---- 验证 ----
tot = noend = 0
lens = []
for c in chs:
    for b in c["content"]:
        tot += 1
        v = b["value"]
        lens.append(len(v))
        if v and v[-1] not in END:
            noend += 1
lens.sort()
print(f"合并后: {tot} 段, 段尾无句读 {noend} ({100*noend/tot:.0f}%), "
      f"长度 p25 {lens[tot//4]} 中位 {lens[tot//2]} p75 {lens[tot*3//4]} max {lens[-1]}")
for i, c in enumerate(chs):
    print(f"[{c['index']}] {c['title'][:14]} {len(c['content']):5d}段  首: {c['content'][0]['value'][:28]!r}")
print("空段:", [i for i, c in enumerate(chs) if not c["content"]] or "无")

if "--dry" in sys.argv:
    sys.exit(0)

# ---- 写入（备份 _old_bad） ----
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
json.dump(meta0, open(os.path.join(SRC, "meta.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=None)
print(f"✓ 写入 {SRC}: {len(chs)} 章（meta/toc 不变）")

shutil.rmtree(DST, ignore_errors=True); shutil.copytree(SRC, DST)
shutil.rmtree(DST2, ignore_errors=True); shutil.copytree(SRC, DST2)
print("✓ 同步 DST/DST2")
