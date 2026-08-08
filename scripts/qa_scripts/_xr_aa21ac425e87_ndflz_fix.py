# -*- coding: utf-8 -*-
"""自然辩证法（aa21ac425e87）抽查14修复：段落切分错位
病因: OCR 文本层切章时章边界劈在页级拼接段中间 → 一个段被切到两章。
修复: ① 13 处边界断句合并（后章首段并入前章末段）
      ② 2 处标题串行删除（章8 末段'［札记和片断］'=章9 标题、章9 首段'［规律和范畴］'=章10 标题）
         —— 页级拼接下 '［X］' 标题行被当段收进错误章
      ③ 其余边界（'［NN］'注释号段/编者注/书信开头）为正常结构，不动
  章结构/toc 36 章 43 项不变（保守方案，无空章无平移）
用法: python _xr_aa21ac425e87_ndflz_fix.py [--dry]
"""
import json, os, re, sys, shutil

BID = "aa21ac425e87"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DST2 = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"
BOOKS_JSON = "f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/books.json"

def norm(s):
    return re.sub(r"\s+", "", s or "")

# (前章, 后章) 断句合并——后章首段并入前章末段
MERGE = [(2, 3), (3, 4), (5, 6), (9, 10), (10, 11), (11, 12),
         (13, 14), (15, 16), (16, 17), (17, 18), (20, 21), (22, 23), (23, 24)]
# 标题串行段（值精确匹配）→ 删除：原书下一章标题行被 OCR 排进当前章
#   （章3/6/8/14/16/21/25 尾部'［札记和片断］' = 章4/7/9/15/17/22 标题；章9 首'［规律和范畴］' = 章10 标题）
DEL_VALUES = {"［札记和片断］", "［规律和范畴］"}

meta0 = json.load(open(os.path.join(SRC, "meta.json"), encoding="utf-8"))
chs = [json.load(open(os.path.join(SRC, f"{i}.json"), encoding="utf-8"))
       for i in range(meta0["chapterCount"])]
assert len(chs) == 36

# ---- 验证 ----
for a, b in MERGE:
    la = norm(chs[a]["content"][-1]["value"])
    fb = norm(chs[b]["content"][0]["value"])
    print(f"合并 [{a}]→[{b}]: …{la[-16:]!r} + {fb[:16]!r}")
    assert la[-1] not in "。！？…\"”" or a in (9, 20), (a, la[-1])  # 9→10 引号内 / 20→21 句中断
# ---- 修复 ----
for a, b in MERGE:
    la = chs[a]["content"][-1]
    fb = chs[b]["content"][0]
    la["value"] = la["value"] + fb["value"]          # 拼接（值内已无换行——页级拼接）
    chs[b]["content"] = chs[b]["content"][1:]
    print(f"✓ 合并 [{a}] 末段 + [{b}] 首段 → [{a}] 末段")

# 删除索引须在合并**之后**重算（合并 pop 首段改变了章内段索引）
dels = [(i, j) for i, c in enumerate(chs) for j, b in enumerate(c["content"])
        if norm(b.get("value", "")) in DEL_VALUES]
print(f"待删标题串行段: {len(dels)} 处")
for ci, j in sorted(dels, reverse=True):
    got = chs[ci]["content"].pop(j)
    print(f"✓ 删 [{ci}] 段{j} {norm(got['value'])[:16]!r}（标题串行）")

# ---- 统计 ----
print()
for c in chs:
    n = sum(len(norm(b["value"])) for b in c["content"])
    first = norm(c["content"][0]["value"])[:26] if c["content"] else "(空!)"
    last = norm(c["content"][-1]["value"])[:20] if c["content"] else ""
    print(f"[{c['index']}] {c['title'][:14]:<14s} {n:6d}字 {len(c['content']):3d}段 | {first!r} … {last!r}")

# ---- 验证: 边界断句清零 + 标题段不残留 ----
END_OK = "。！？；：…\"』》)”]"
bad = []
for i in range(len(chs) - 1):
    c0, c1 = chs[i], chs[i + 1]
    if not c0["content"] or not c1["content"]:
        continue
    la, fb = norm(c0["content"][-1]["value"]), norm(c1["content"][0]["value"])
    if la and fb and la[-1] not in END_OK:
        bad.append(f"[{i}] 末{la[-12:]!r} → [{i+1}] 首{fb[:12]!r}")
print("边界断句:", "✓ 清零" if not bad else f"✗ {bad[:8]}")
left = [(i, j) for i, c in enumerate(chs) for j, b in enumerate(c["content"])
        if norm(b.get("value", "")) in ("［札记和片断］", "［规律和范畴］")]
print("标题段残留:", "✓ 无" if not left else f"✗ {left}")

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
# detail 的 toc 也要同步（内容变了但结构没变——只同步 toc 引用一致性）
for p in (DETAIL_SRC, DETAIL_DST):
    d = json.load(open(p, encoding="utf-8"))
    d["toc"] = meta0["toc"]
    d["chapterCount"] = meta0["chapterCount"]
    d["chapterTitles"] = meta0["chapterTitles"]
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
    print(f"✓ detail 同步: {p}")
