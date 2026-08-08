# -*- coding: utf-8 -*-
"""删除一本书的第 0 章（纯目录串病害章）并重排 toc: python _del_first_chapter.py <bid>
备份原 0.json → PhiAgent/backend/data/book_chapters/_rebuild_bak/{bid}_first_ch/
用法: python _del_first_chapter.py cc9d0d9358a7
"""
import sys, os, json, shutil
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"f:\program\Python\PhiAgent\backend\tools")
import rebuild_auto as ra

BID = sys.argv[1]
CH = ra.CH
D = os.path.join(CH, BID)
fp0 = os.path.join(D, "0.json")
if not os.path.exists(fp0):
    print(f"✗ {BID}: 无 0.json")
    sys.exit(1)

ch0 = json.load(open(fp0, encoding="utf-8"))
n0 = sum(len(x.get("value", "")) for x in ch0.get("content", []))
print(f"待删 [0] {ch0['title']!r} 段{len(ch0['content'])} 字{n0}")

# 备份
BAK = os.path.join(CH, "_rebuild_bak", f"{BID}_first_ch")
os.makedirs(BAK, exist_ok=True)
shutil.copy2(fp0, os.path.join(BAK, "0.json"))
print(f"备份 → {BAK}")

# 前移 n.json → (n-1).json
files = sorted(int(f[:-5]) for f in os.listdir(D) if f.endswith(".json") and f != "meta.json")
n = len(files)
for i in files[1:]:
    ch = json.load(open(os.path.join(D, f"{i}.json"), encoding="utf-8"))
    ch["index"] = i - 1
    json.dump(ch, open(os.path.join(D, f"{i - 1}.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
os.remove(fp0)
print(f"删除 0.json, 前移 {n - 1} 章")

# meta 重排
meta = json.load(open(os.path.join(D, "meta.json"), encoding="utf-8"))
meta["chapterCount"] = n - 1
meta["toc"] = [c for c in meta["toc"] if c["index"] != 0]
for c in meta["toc"]:
    c["index"] -= 1
meta["chapterTitles"] = meta["chapterTitles"][1:]
json.dump(meta, open(os.path.join(D, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"meta: chapterCount={meta['chapterCount']}, toc={len(meta['toc'])}条")

ra.sync_three(BID)
print("sync_three 完成")
