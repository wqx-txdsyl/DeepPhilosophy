# -*- coding: utf-8 -*-
"""PDF 书机械修复批次 1 (2026-08-08, 基于 _ocr_batch_check 结果)
1. 论选择的艺术 1282e86cd93b: [0]==[1] 内容完全相同(整本复制2遍) → 删 [1]
2. 哲学书简 5f838ef64e5e: 同上 → 删 [1]
3. 新弗雷格主义 64056c6623ee: [15]+[16] 后记被切两半 → 合并为 1 章
4. 君主论 2e66606c2854: 全量核对 toc vs 章文件 title vs 内容(目录残留诊断, 只读)
"""
import sys, json, os, re, hashlib, shutil
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"f:\program\Python\PhiAgent\backend\tools")
import rebuild_auto as ra

def dw(t):
    return re.sub(r"\s+", "", t)

def get_ch(D, i):
    j = json.load(open(os.path.join(D, f"{i}.json"), encoding="utf-8"))
    return j

def dedup_two(bid, name):
    """[0]==[1] 完全重复 → 删 [1]"""
    D = os.path.join(ra.CH, bid)
    j0 = get_ch(D, 0); j1 = get_ch(D, 1)
    t0 = [b["value"] for b in j0["content"] if b.get("type") == "text"]
    t1 = [b["value"] for b in j1["content"] if b.get("type") == "text"]
    same = len(t0) == len(t1) and all(dw(a) == dw(b) for a, b in zip(t0, t1))
    print(f"{name}: [0] 段{len(t0)} 字{sum(len(x) for x in t0)} | [1] 段{len(t1)} 字{sum(len(x) for x in t1)} | 相同={same}")
    if not same:
        print(f"  !! 两章不同, 跳过")
        return
    # 备份
    bak = os.path.join(r"f:\program\Python\PhiAgent\backend\data\_rebuild_bak", f"{bid}_dedup")
    os.makedirs(bak, exist_ok=True)
    shutil.copy(os.path.join(D, "1.json"), os.path.join(bak, "1.json"))
    shutil.copy(os.path.join(D, "meta.json"), os.path.join(bak, "meta.json"))
    os.remove(os.path.join(D, "1.json"))
    m = json.load(open(os.path.join(D, "meta.json"), encoding="utf-8"))
    m["chapterCount"] = 1
    m["chapterTitles"] = [m["chapterTitles"][0]]
    m["toc"] = [{"type": "chapter", "title": m["toc"][0]["title"], "index": 0, "level": 1}]
    json.dump(m, open(os.path.join(D, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"  已删 [1], chapterCount=1")
    ra.sync_three(bid)
    print(f"  sync_three 完成")

def merge_parts(bid, name, idxs, new_title):
    """[15]+[16] 合并为 1 章"""
    D = os.path.join(ra.CH, bid)
    m = json.load(open(os.path.join(D, "meta.json"), encoding="utf-8"))
    content = []
    for i in idxs:
        j = get_ch(D, i)
        content += [b for b in j["content"] if b.get("type") == "text"]
    # 备份
    bak = os.path.join(r"f:\program\Python\PhiAgent\backend\data\_rebuild_bak", f"{bid}_merge")
    os.makedirs(bak, exist_ok=True)
    for i in idxs:
        shutil.copy(os.path.join(D, f"{i}.json"), os.path.join(bak, f"{i}.json"))
    # 重写首章, 删后续
    json.dump({"title": new_title, "content": [{"type": "text", "value": t} for t in content], "index": idxs[0]},
              open(os.path.join(D, f"{idxs[0]}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for i in idxs[1:]:
        os.remove(os.path.join(D, f"{i}.json"))
    m["chapterCount"] -= len(idxs) - 1
    toc = []
    for t in m.get("toc") or []:
        if t.get("type") == "chapter" and t.get("index") == idxs[1]:
            t["title"] = new_title
        if t.get("type") == "chapter" and t.get("index") in idxs[1:]:
            continue
        toc.append(t)
    m["toc"] = toc
    m["chapterTitles"] = [t["title"] for t in toc if t.get("type") == "chapter"]
    json.dump(m, open(os.path.join(D, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{name}: 合并章 {idxs} → [{idxs[0]}] {new_title} 段={len(content)} 字={sum(len(x) for x in content)}, chapterCount={m['chapterCount']}")
    ra.sync_three(bid)
    print(f"  sync_three 完成")

# 1+2. 去重
dedup_two("1282e86cd93b", "论选择的艺术")
dedup_two("5f838ef64e5e", "哲学书简")

# 3. 合并后记
merge_parts("64056c6623ee", "新弗雷格主义", [15, 16], "后记")

# 4. 君主论诊断(只读)
print("\n===== 君主论 全量诊断 =====")
D = os.path.join(ra.CH, "2e66606c2854")
m = json.load(open(os.path.join(D, "meta.json"), encoding="utf-8"))
for i, t in enumerate(m.get("toc") or []):
    fp = os.path.join(D, f"{t.get('index')}.json")
    if not os.path.exists(fp):
        print(f"  toc[{i}] {t.get('title')[:30]} → 文件缺失!")
        continue
    j = json.load(open(fp, encoding="utf-8"))
    ts = [b["value"] for b in j["content"] if b.get("type") == "text"]
    head = ts[0][:36].replace("\n", " ") if ts else "(空)"
    mark = " ✓" if j["title"] == t.get("title") else f" ← 文件标题={j['title'][:24]!r}"
    print(f"  [{t.get('index')}] {t.get('title')[:26]:<28} 段{len(ts)} 首段: {head!r}{mark}")
