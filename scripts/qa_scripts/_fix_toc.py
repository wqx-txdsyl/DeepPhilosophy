# -*- coding: utf-8 -*-
"""修复柏拉图/增广贤文 meta.toc 残留: chapter 条目从文件重建, part 保留"""
import sys, os, json, shutil
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"f:/program/Python/PhiAgent/backend/tools")
import rebuild_auto as ra

CH = ra.CH
for bid in ("e74dc59d508e", "e863b4cca50d"):
    bd = os.path.join(CH, bid)
    mfp = os.path.join(bd, "meta.json")
    m = json.load(open(mfp, encoding="utf-8"))
    n = m["chapterCount"]
    old_toc = m["toc"]
    # 备份
    bak = os.path.join(ra.BAK, f"{bid}_tocfix")
    shutil.copy2(mfp, bak + ".json")
    # 从文件重建 chapter 条目; 保留旧 toc 中 part 顺序（part 后接其章节）
    new_toc = []
    file_titles = []
    for i in range(n):
        c = json.load(open(os.path.join(bd, f"{i}.json"), encoding="utf-8"))
        file_titles.append(c["title"])
    # 重建: 遍历旧 toc, part 原样; chapter 按文件序替换
    ci = 0
    for t in old_toc:
        if isinstance(t, dict) and t.get("type") == "part":
            new_toc.append({"type": "part", "title": t.get("title")})
        else:
            if ci < n:
                new_toc.append({"type": "chapter", "title": file_titles[ci], "index": ci})
                ci += 1
    if ci < n:  # 旧 toc 缺章（part 后章节不足）
        for i in range(ci, n):
            new_toc.append({"type": "chapter", "title": file_titles[i], "index": i})
    m["toc"] = new_toc
    m["chapterTitles"] = file_titles
    json.dump(m, open(mfp, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"{bid}: toc {len(old_toc)} → {len(new_toc)} (chapterCount={n})")
    ra.sync_three(bid)
    print(f"{bid}: 三端同步完成")
