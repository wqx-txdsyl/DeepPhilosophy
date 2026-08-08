# -*- coding: utf-8 -*-
"""《论人类不平等的起源和基础》epub 完全重建
旧库 11 章严重错位+内容丢失（致辞/第一部分/第二部分主体缺失，注释混入各章）。
方案：按 epub 文件+h1 边界重建 12 章（00005-00015），00004 保留(含图)但验证。
"""
import sys, re, json, zipfile, os, shutil
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, r"f:\program\Python\PhiAgent\backend\tools")
import rebuild_auto as ra

BID = "9e4f98733f0b"
EP = r"F:/philosophy/西方/让-雅克·卢梭/论人类不平等的起源和基础.epub"
BASE = ra.CH  # PhiAgent data/book_chapters 根
D = os.path.join(BASE, BID)

# ---------- 1. 备份 ----------
bak = os.path.join(ra.BAK, f"{BID}_old11ch")
os.makedirs(bak, exist_ok=True)
for f in os.listdir(D):
    shutil.copy2(os.path.join(D, f), os.path.join(bak, f))
print(f"备份 -> {bak}")

# ---------- 2. 提取 epub 段落 ----------
z = zipfile.ZipFile(EP)
def extract(fn):
    c = z.read(f"OEBPS/{fn}.html").decode("utf-8", errors="replace")
    paras = []
    for m in re.finditer(r"<(p|h[1-6])[^>]*>(.*?)</\1>", c, re.S):
        tag, body = m.group(1), m.group(2)
        t = re.sub(r"<[^>]+>", "", body)
        t = t.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        t = re.sub(r"[ \t\u3000]+", " ", t)
        t = re.sub(r"\s+", "", t)  # h1 内换行压缩; 段落内换行也压缩
        if t:
            paras.append((tag, t))
    return paras

# h1 里的 \r\n 处理: 提取时按段落内换行压缩, "本论\r\n[1]" -> "本论[1]"
def clean_title(t):
    t = re.sub(r"\s+", "", t)
    t = re.sub(r"\[1\]$", "", t).strip()
    return t

CHS = [  # (epub文件, 章标题)
    ("text00005", "导读"),
    ("text00006", "关于附注的说明"),
    ("text00007", "致辞：献给日内瓦共和国"),
    ("text00008", "序"),
    ("text00009", "本论"),
    ("text00010", "第一部分"),
    ("text00011", "第二部分"),
    ("text00012", "注释 卢梭注于讲稿完成后"),
    ("text00013", "卢梭致菲洛普利的信"),
    ("text00014", "卢梭生平大事年表"),
    ("text00015", "注释"),
]

new_files = {}   # idx -> content list
for fn, title in CHS:
    paras = extract(fn)
    hs = [p for tag, p in paras if tag != "p"]
    ps = [p for tag, p in paras if tag == "p"]
    if hs:
        # h1 应只有一个且与预期标题匹配(容差: 去空白后包含)
        h1 = clean_title(hs[0]) if hs[0] else ""
        print(f"== {fn} h1={h1!r} 期望={title!r} 段数={len(ps)}")
        if h1 and h1 != title:
            print(f"   !! h1 与标题不一致: {h1} vs {title}")
    else:
        print(f"== {fn} 无 h1 期望={title!r} 段数={len(ps)}")
    content = [{"type": "text", "value": title}] + [{"type": "text", "value": p} for p in ps]
    new_files[fn] = content

# ---------- 3. 验证 00004 (保留现有) ----------
old0 = json.load(open(os.path.join(D, "0.json"), encoding="utf-8"))
old0texts = [b["value"] for b in old0["content"] if b.get("type") == "text"]
ep4 = [p for tag, p in extract("text00004")]
print("\n== 00004 验证 ==")
print("epub 00004 段落:", [t[:20] for t in ep4])
missing = [t for t in ep4 if t not in old0texts]
if missing:
    print(f"!! 库 0 缺 {len(missing)} 段:")
    for t in missing:
        print("   ", t[:60])
else:
    print("库 0 已包含 epub 00004 全部段落 ✓")

# ---------- 4. 写入 1-11 ----------
for i, (fn, _) in enumerate(CHS, start=1):
    j = {"title": CHS[i-1][1], "content": new_files[fn], "index": i}
    json.dump(j, open(os.path.join(D, f"{i}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"写入 {i}.json ({fn}) 段数={len(j['content'])}")

# ---------- 5. 重写 meta toc ----------
toc = [{"type": "chapter", "title": "如何阅读本书", "index": 0}]
toc += [{"type": "chapter", "title": t, "index": i} for i, (_, t) in enumerate(CHS, start=1)]
chapterTitles = [t for _, t in CHS]
chapterTitles.insert(0, "如何阅读本书")
m = json.load(open(os.path.join(D, "meta.json"), encoding="utf-8"))
m["toc"] = toc
m["chapterCount"] = len(toc)
m["chapterTitles"] = chapterTitles
json.dump(m, open(os.path.join(D, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"\nmeta: chapterCount={len(toc)}")

# ---------- 6. 三端同步 ----------
ra.sync_three(BID)
print("sync_three 完成")
