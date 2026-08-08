# -*- coding: utf-8 -*-
"""尼采与哲学: 75 节 → 5 章（第X章卷级）合并重建
- 卷首节正文剥卷标题残留（重建 bug: "一、悲剧一、悲剧1. 系谱学概念…"）
- 节标题行写回正文（重建时被剥成章 title 的节, 内容里没有标题行 → 恢复原文）
- meta toc/chapterCount/chapterTitles 重写 + 三端同步
"""
import sys, os, json, re, shutil
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"f:/program/Python/PhiAgent/backend/tools")
import rebuild_auto as ra

bid = "e7c27b39a87c"
bd = os.path.join(ra.CH, bid)
VOLS = [
    ("第一章 悲剧", 0, 16),
    ("第二章 能动与反动", 16, 31),
    ("第三章 批判", 31, 46),
    ("第四章 从怨恨到内疚", 46, 62),
    ("第五章 超人：反辩证法", 62, 75),
]
STRIP = ["一、悲剧一、悲剧", "二、能动与反动", "三、批判三、批判", "四、从怨恨到内疚", "五、超人：反辩证法"]

# 1. 备份
bak = os.path.join(ra.BAK, f"{bid}_old75ch")
if os.path.exists(bak):
    shutil.rmtree(bak)
shutil.copytree(bd, bak)
print(f"备份 → {bak}")

# 2. 读 75 章
chs = []
for i in range(75):
    c = json.load(open(os.path.join(bd, f"{i}.json"), encoding="utf-8"))
    chs.append(c)
old_words = sum(len(x.get("value", "")) for c in chs for x in c["content"] if x.get("type") == "text")

# 3. 合并
new_chs = []
for vi, (vtitle, s, e) in enumerate(VOLS):
    content = []
    for i in range(s, e):
        c = chs[i]
        m = re.match(r"^第(\d+)节\s*(.*)$", c["title"])
        sec_no, sec_title = (int(m.group(1)), m.group(2)) if m else (None, c["title"])
        texts = [x["value"] for x in c["content"] if x.get("type") == "text"]
        if not texts:
            continue
        # 卷首节: 剥卷标题残留
        if vi < len(STRIP):
            texts[0] = texts[0][len(STRIP[vi]):] if texts[0].startswith(STRIP[vi]) else texts[0]
        # 节标题写回（首段未以"数字."开头时插独立段, 恢复原文节标题行）
        if sec_no is not None and not re.match(r"^\d{1,2}\.", texts[0]):
            content.append({"type": "text", "value": f"{sec_no}. {sec_title}"})
        for t in texts:
            content.append({"type": "text", "value": t})
    new_chs.append({"index": vi, "title": vtitle, "content": content})
    w = sum(len(x["value"]) for x in content)
    print(f"  {vtitle}: 节{s}-{e-1} → {len(content)} 段 {w} 字")

new_words = sum(len(x["value"]) for c in new_chs for x in c["content"])
print(f"字数: {old_words} → {new_words} (差 {new_words - old_words})")

# 4. 写文件
for c in new_chs:
    json.dump(c, open(os.path.join(bd, f"{c['index']}.json"), "w", encoding="utf-8"), ensure_ascii=False)
for i in range(5, 75):
    p = os.path.join(bd, f"{i}.json")
    if os.path.exists(p):
        os.remove(p)

# 5. meta 重写
meta = json.load(open(os.path.join(bd, "meta.json"), encoding="utf-8"))
meta["toc"] = [{"type": "chapter", "title": c["title"], "index": c["index"]} for c in new_chs]
meta["chapterCount"] = 5
meta["chapterTitles"] = [c["title"] for c in new_chs]
json.dump(meta, open(os.path.join(bd, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False)
print("meta 重写:", meta["chapterTitles"])

# 6. 三端同步
ra.sync_three(bid)
print("三端同步完成")
