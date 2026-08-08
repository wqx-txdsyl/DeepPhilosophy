# -*- coding: utf-8 -*-
"""逻辑哲学论（5d906139d1b2）抽查17修复：正文错位
病因: 切章把献词页（'谨以此书纪念我的朋友大卫·平逊特'）归入正文章[5]，而全部命题正文
  （1.-7. 526 条编号）被塞进'前言'章[6] → 用户翻开'逻辑哲学论'只见献词一行。
修复: 交换 [5]/[6] 语义（chapterCount 9 不变）：
  [5] 标题改'前　言' ← 前言 10 段（'这本书也许只有…' + 署名'路・维' + '1918年，维也纳'）
  [6] 标题改'逻辑哲学论' ← 献词 4 段 + 正文全部（段10起：'1 [1] 世界是一切发生的事情。'→'[10] modus ponens…'）
  toc/chapterTitles 同步交换；正文编号 1.-7. 完整（1:7 2:79 3:74 4:109 5:151 6:105 7:1）
用法: python _xr_5d906139d1b2_tractatus_fix.py
"""
import json, os, shutil

BID = "5d906139d1b2"
SRC = f"f:/program/Python/PhiAgent/backend/data/book_chapters/{BID}"
DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/backend/data/book_chapters/{BID}"
DST2 = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/backend/data/book_chapters/{BID}"
DETAIL_SRC = f"f:/program/Python/PhiAgent/backend/data/book_detail/{BID}.json"
DETAIL_DST = f"f:/program/Python/DeepPhilosophy/DeepPhilosophy/app/public/book_detail/{BID}.json"

meta0 = json.load(open(os.path.join(SRC, "meta.json"), encoding="utf-8"))
chs = [json.load(open(os.path.join(SRC, f"{i}.json"), encoding="utf-8"))
       for i in range(meta0["chapterCount"])]
assert len(chs) == 9

# ---- 诊断校验 ----
v5 = [b.get("value", "") for b in chs[5]["content"]]
v6 = [b.get("value", "") for b in chs[6]["content"]]
assert len(v5) == 4 and v5[0].startswith("谨以此书纪念"), v5            # [5] = 献词页
assert v6[0].startswith("这本书也许只有"), v6[0][:30]                   # [6] 开头 = 前言
assert v6[10].startswith("1 "), v6[10][:30]                             # [6] 段10 = 命题1
assert v6[-1].startswith("[10] modus"), v6[-1][:30]                     # [6] 末 = 译者注
assert len(v6) == 967, len(v6)

# ---- 交换语义 ----
qianyan = [{"type": "text", "value": v} for v in v6[:10]]               # 前言 10 段（段0-9）
zhengwen = ([{"type": "text", "value": v} for v in v5] +                # 献词 4 段
            [{"type": "text", "value": v} for v in v6[10:]])            # 正文 957 段
chs[5]["title"] = "前\u3000言"
chs[5]["content"] = qianyan
chs[6]["title"] = "逻辑哲学论"
chs[6]["content"] = zhengwen
# toc 同步交换
for t in meta0["toc"]:
    if t["index"] == 5:
        t["title"] = "前\u3000言"
    elif t["index"] == 6:
        t["title"] = "逻辑哲学论"
meta0["chapterTitles"] = [t["title"] for t in meta0["toc"]]

# ---- 验证 ----
n5 = sum(len(v) for v in qianyan)
n6 = sum(len(v) for v in zhengwen)
print(f"[5] 前　言: {len(qianyan)} 段 {n5} 字  首: {qianyan[0]['value'][:20]!r}")
print(f"[6] 逻辑哲学论: {len(zhengwen)} 段 {n6} 字  首: {zhengwen[0]['value'][:20]!r} … 末: {zhengwen[-1]['value'][:30]!r}")
assert chs[6]["content"][0]["value"].startswith("谨以此书")
assert chs[6]["content"][4]["value"].startswith("1 ")
import re
big = {n: 0 for n in range(1, 8)}
for v in zhengwen:
    m = re.match(r"^([1-7])[\s\.　]", v.get("value", ""))
    if m:
        big[int(m.group(1))] += 1
print("编号覆盖:", big)
assert big == {1: 7, 2: 79, 3: 74, 4: 109, 5: 151, 6: 105, 7: 1}, big

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
print(f"✓ 写入 {SRC}: {len(chs)} 章（toc 交换 [5]/[6]）")

shutil.rmtree(DST, ignore_errors=True); shutil.copytree(SRC, DST)
shutil.rmtree(DST2, ignore_errors=True); shutil.copytree(SRC, DST2)
print("✓ 同步 DST/DST2")

# ---- detail 同步（chapterTitles/toc 交换） ----
for p in (DETAIL_SRC, DETAIL_DST):
    d = json.load(open(p, encoding="utf-8"))
    d["toc"] = meta0["toc"]
    d["chapterCount"] = meta0["chapterCount"]
    d["chapterTitles"] = meta0["chapterTitles"]
    json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=None)
    print(f"✓ detail 同步: {p}")
