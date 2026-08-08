# -*- coding: utf-8 -*-
"""2026-08-08 事故二：book_detail 全量回同步（PhiAgent 为权威） + books.json chapterCount 修正
病因: 5173 详情页目录/分级全乱。修复工作流持续更新 PhiAgent
  backend/data/book_detail（修复源头），但 DP app/public/book_detail
  大量未同步（105 本不一致：81 本 CHKLIST已修书 DP 侧是旧 toc，10 本已修
  但 DP 空，23 本 OCR 新书 DP 空，1 本 extract 字段差异），且 books.json
  chapterCount 有 60 本与修复结果不符 → 详情页"分级"乱。
  另: 0d31135f957d（公共领域的新结构转型）章节 meta 三处不同步
  （Phi cc=2 修复版 vs DP cc=6 旧版含'七星哲人文库学术委员会'垃圾章）。
修复: 全量以 PhiAgent 侧为权威:
  1) backend/data/book_detail/*.json → app/public/book_detail/（覆盖）
  2) books.json chapterCount ← Phi detail chapterCount（60 本修正）
  3) 0d31135f957d 章节目录（Phi → DP backend + DP app/public）
用法: python _xr_book_detail_resync.py [--dry]
"""
import json, os, re, sys, shutil

PHI_DETAIL = r"f:\program\Python\PhiAgent\backend\data\book_detail"
DP_DETAIL  = r"f:\program\Python\DeepPhilosophy\DeepPhilosophy\app\public\book_detail"
PHI_CH     = r"f:\program\Python\PhiAgent\backend\data\book_chapters"
DP_CH      = r"f:\program\Python\DeepPhilosophy\DeepPhilosophy\backend\data\book_chapters"
DP_CH_PUB  = r"f:\program\Python\DeepPhilosophy\DeepPhilosophy\app\public\backend\data\book_chapters"
BOOKS_JSON = r"f:\program\Python\DeepPhilosophy\DeepPhilosophy\app\public\books.json"
BID_ODD = "0d31135f957d"   # 章节 meta 不同步的书

# ---- 1. book_detail 差异统计 ----
def sig(p):
    j = json.load(open(p, encoding="utf-8"))
    return (j.get("chapterCount"), j.get("extract"),
            json.dumps(j.get("toc"), ensure_ascii=False))
phi_files = sorted(f[:-5] for f in os.listdir(PHI_DETAIL) if f.endswith(".json"))
changed, added, same, skip = [], [], 0, 0
field_lost = {}
for k in phi_files:
    p1 = os.path.join(PHI_DETAIL, k + ".json")
    p2 = os.path.join(DP_DETAIL, k + ".json")
    if not os.path.exists(p2):
        added.append(k)
        continue
    if sig(p1) == sig(p2):
        same += 1
        continue
    # 字段集差异检查（Phi 覆盖是否会丢字段）
    f1, f2 = set(json.load(open(p1, encoding="utf-8"))), set(json.load(open(p2, encoding="utf-8")))
    lost = f2 - f1
    if lost:
        field_lost[k] = lost
        skip += 1
        continue
    changed.append(k)
extra_in_dp = [f[:-5] for f in os.listdir(DP_DETAIL) if f.endswith(".json") and f[:-5] not in phi_files]
print(f"book_detail: 总 {len(phi_files)} 本 | 一致 {same} | 将覆盖 {len(changed)} | 新增 {len(added)} | "
      f"跳过(Phi会丢字段) {skip} | DP独有文件 {len(extra_in_dp)}")
if field_lost:
    print("⚠ 丢字段样本:")
    for k, lost in list(field_lost.items())[:5]:
        print(f"  {k}: 缺 {sorted(lost)}")
if extra_in_dp:
    print("⚠ DP 独有 detail:", extra_in_dp[:10])

# ---- 2. books.json cc 差异 ----
bj = json.load(open(BOOKS_JSON, encoding="utf-8"))
bl = bj if isinstance(bj, list) else bj.get("books", [])
cc_fix = []
for b in bl:
    p = os.path.join(PHI_DETAIL, b.get("id", "") + ".json")
    if not os.path.exists(p):
        continue
    j = json.load(open(p, encoding="utf-8"))
    if j.get("chapterCount") != b.get("chapterCount"):
        cc_fix.append((b.get("id"), b.get("title"), b.get("chapterCount"), j.get("chapterCount")))
print(f"\nbooks.json chapterCount 待修正: {len(cc_fix)} 本")
for x in cc_fix[:15]:
    print(f"  {x[0]} {str(x[1])[:18]}  cc {x[2]} → {x[3]}")

# ---- 3. 0d31135f957d 章节 meta ----
odd_p = os.path.join(PHI_CH, BID_ODD)
odd_dp = os.path.join(DP_CH, BID_ODD)
odd_pub = os.path.join(DP_CH_PUB, BID_ODD)
def mdir(p):
    if not os.path.isdir(p):
        return "(无)"
    return " ".join(sorted(f for f in os.listdir(p) if f.endswith(".json")))
print(f"\n{BID_ODD} 章节: Phi[{mdir(odd_p)}] DP[{mdir(odd_dp)}] Pub[{mdir(odd_pub)}]")
# Phi 侧编号错位检查: toc idx 集合 vs 文件编号集合（排除 meta）
def idx_mismatch(p):
    if not os.path.isdir(p):
        return None
    m = json.load(open(os.path.join(p, "meta.json"), encoding="utf-8"))
    toc_idx = set(t.get("index") for t in m.get("toc") or [])
    file_idx = set(int(f[:-5]) for f in os.listdir(p)
                   if f.endswith(".json") and f != "meta.json" and f[:-5].isdigit())
    return toc_idx, file_idx
im = idx_mismatch(odd_p)
if im and im[0] != im[1]:
    print(f"  ⚠ Phi 侧编号错位: toc idx {sorted(im[0])} vs 文件 idx {sorted(im[1])} → 执行时重排为 0..N-1")

if "--dry" in sys.argv:
    sys.exit(0)

# ---- 执行 ----
# 1) book_detail 覆盖/新增
for k in changed + added:
    shutil.copyfile(os.path.join(PHI_DETAIL, k + ".json"),
                    os.path.join(DP_DETAIL, k + ".json"))
# 1b) 2 本缺字段书合并（Phi 基础 + DP summary/tags）
for k in field_lost:
    p1 = os.path.join(PHI_DETAIL, k + ".json")
    p2 = os.path.join(DP_DETAIL, k + ".json")
    j1 = json.load(open(p1, encoding="utf-8"))
    j2 = json.load(open(p2, encoding="utf-8"))
    for fld in j2:
        if fld not in j1:
            j1[fld] = j2[fld]
    json.dump(j1, open(p2, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
    print(f"✓ book_detail 合并(补 summary/tags): {k}")
print(f"✓ book_detail 同步 {len(changed) + len(added)} 本 + 合并 {len(field_lost)} 本")

# 2) books.json cc
for b in bl:
    p = os.path.join(PHI_DETAIL, b.get("id", "") + ".json")
    if not os.path.exists(p):
        continue
    j = json.load(open(p, encoding="utf-8"))
    if j.get("chapterCount") != b.get("chapterCount"):
        b["chapterCount"] = j.get("chapterCount")
with open(BOOKS_JSON, "w", encoding="utf-8") as f:
    json.dump(bl if isinstance(bj, list) else {**bj, "books": bl}, f,
              ensure_ascii=False, indent=None)
print(f"✓ books.json chapterCount 修正 {len(cc_fix)} 本")

# 3) 0d31135f957d 章节: 按 toc 顺序重排编号（文件/内容 index → 0..N-1）后三处同步
#   Phi 侧现状: toc idx 0-4, 文件 index 1-5（差 1, 缺 0.json → '前言' 404）→ 顺序 zip 重排
files = sorted(f for f in os.listdir(odd_p) if f.endswith(".json") and f != "meta.json")
if files:
    m = json.load(open(os.path.join(odd_p, "meta.json"), encoding="utf-8"))
    toc = sorted(m.get("toc") or [], key=lambda x: x.get("index", 0))
    assert len(files) == len(toc), f"文件数 {len(files)} != toc 项 {len(toc)}"
    tmp = os.path.join(odd_p, "_old_idx")
    os.makedirs(tmp, exist_ok=True)
    for f in files:
        shutil.move(os.path.join(odd_p, f), os.path.join(tmp, f))
    for i, (t, f) in enumerate(zip(toc, sorted(files, key=lambda f: int(f[:-5])))):
        j = json.load(open(os.path.join(tmp, f), encoding="utf-8"))
        j["index"] = i
        t["index"] = i
        json.dump(j, open(os.path.join(odd_p, f"{i}.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=None)
    shutil.rmtree(tmp)
    m["toc"] = toc
    m["chapterCount"] = len([t for t in toc if t.get("type") == "chapter"])
    m["chapterTitles"] = [t["title"] for t in toc if t.get("type") == "chapter"]
    json.dump(m, open(os.path.join(odd_p, "meta.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=None)
    for d in (odd_dp, odd_pub):
        shutil.rmtree(d, ignore_errors=True)
        shutil.copytree(odd_p, d)
    print(f"✓ {BID_ODD} 章节重排 0..{len(toc)-1}（cc={m['chapterCount']}）并同步 DP 两处")
else:
    print(f"⚠ {BID_ODD} 无章节文件，跳过")
