# -*- coding: utf-8 -*-
"""PDF 书机械修复批次 2 (2026-08-08): A4 标题粘正文 + 章名 OCR 错字
1. 政治学 53b09f03e24e: 8 卷首段剥离 toc 章名('卷（A）'等), 保留'章一'
2. 恐惧与战栗 f1e06cece874: '绪'/'跋'章首段剥离标题
3. 政府论下篇 e3a52553c303: 章名 OCR 错字修正(谥/险/渝/睢/临/脸/谕/粽/治→论) + [7]手动剥离
"""
import sys, json, os, re, shutil
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"f:\program\Python\PhiAgent\backend\tools")
import rebuild_auto as ra

def dw(t):
    return re.sub(r"\s+", "", t)

def strip_toc_title(D, idx, title, extra_prefixes=()):
    """首段以 toc 章名(去空白)开头 → 剥离(标题已在 toc, 正文保留)"""
    fp = os.path.join(D, f"{idx}.json")
    j = json.load(open(fp, encoding="utf-8"))
    content = j["content"]
    ti = next((i for i, b in enumerate(content) if b.get("type") == "text"), None)
    if ti is None:
        return False
    t = content[ti]["value"]
    for pre in [title] + list(extra_prefixes):
        dp = dw(pre)
        if dp and dw(t).startswith(dp):
            # 定位去空白前缀在原文中的切割点
            cnt = 0
            cut = 0
            for k, ch in enumerate(t):
                if not ch.isspace():
                    if cnt == len(dp):
                        cut = k
                        break
                    cnt += 1
            content[ti]["value"] = t[cut:]
            json.dump(j, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            return True
    return False

def fix_titles(D, mapping):
    """章名错字修正: 替换 meta.toc/chapterTitles + 章文件 title"""
    m = json.load(open(os.path.join(D, "meta.json"), encoding="utf-8"))
    n = 0
    for t in m.get("toc") or []:
        if t.get("type") != "chapter":
            continue
        old = t["title"]
        new = old
        for k, v in mapping:
            new = re.sub(k, v, new)
        if new != old:
            t["title"] = new
            n += 1
            fp = os.path.join(D, f"{t['index']}.json")
            if os.path.exists(fp):
                j = json.load(open(fp, encoding="utf-8"))
                j["title"] = new
                json.dump(j, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    m["chapterTitles"] = [t["title"] for t in m["toc"] if t.get("type") == "chapter"]
    json.dump(m, open(os.path.join(D, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return n

# 1. 政治学: 剥离 8 卷章名
D1 = os.path.join(ra.CH, "53b09f03e24e")
m1 = json.load(open(os.path.join(D1, "meta.json"), encoding="utf-8"))
n1 = 0
for t in m1["toc"]:
    if t.get("type") == "chapter" and strip_toc_title(D1, t["index"], t["title"]):
        n1 += 1
print(f"政治学: 剥离 {n1} 章")
ra.sync_three("53b09f03e24e")

# 2. 恐惧与战栗: 绪/跋 剥离(章名'绪'/'跋')
D2 = os.path.join(ra.CH, "f1e06cece874")
for idx, pre in [(4, "绪"), (10, "跋")]:
    ok = strip_toc_title(D2, idx, pre)
    print(f"恐惧与战栗 [{idx}] 剥离 {pre!r}: {ok}")
ra.sync_three("f1e06cece874")

# 3. 政府论下篇: 章名错字 + [7] 剥离
D3 = os.path.join(ra.CH, "e3a52553c303")
ERR = [("^第(二|三|四|五|七|八|九|十|十一|十二|十三|十四|十五|十六|十七|十八|十九)章[谥险渝睢临脸谕粽治]*", "论")]
# 逐章映射(具体章名级, 防误伤正文): 用章名原文替换
m3 = json.load(open(os.path.join(D3, "meta.json"), encoding="utf-8"))
fixmap = [
    ("第二章 谥自然状态", "第二章 论自然状态"),
    ("第三章 险战争状态", "第三章 论战争状态"),
    ("第四章 渝奴役", "第四章 论奴役"),
    ("第五章 谥财产", "第五章 论财产"),
    ("第七章 睢政治的或公民的祖会", "第七章 论政治的或公民的社会"),
    ("第八章 临政治社会的起源", "第八章 论政治社会的起源"),
    ("第九章 谥政治社会和政府的目的", "第九章 论政治社会和政府的目的"),
    ("第十章 谥国家的形式", "第十章 论国家的形式"),
    ("第十一章 脸立法权的范圉", "第十一章 论立法权的范围"),
    ("第十二章 脸国家的立法权、执行权和对外权", "第十二章 论国家的立法权、执行权和对外权"),
    ("第十三章 脸国家权力的統屡", "第十三章 论国家权力的统属"),
    ("第十四章 谕特权", "第十四章 论特权"),
    ("第十五章 粽险父权政治权力和专制权力", "第十五章 论父权政治权力和专制权力"),
    ("第十八章 渝暴政", "第十八章 论暴政"),
    ("第十九章 治政府的解体", "第十九章 论政府的解体"),
]
for t in m3["toc"]:
    if t.get("type") != "chapter":
        continue
    old = t["title"]
    for k, v in fixmap:
        if old == k:
            t["title"] = v
            fp = os.path.join(D3, f"{t['index']}.json")
            j = json.load(open(fp, encoding="utf-8"))
            j["title"] = v
            json.dump(j, open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            break
m3["chapterTitles"] = [t["title"] for t in m3["toc"] if t.get("type") == "chapter"]
json.dump(m3, open(os.path.join(D3, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
# [7] 手动剥离(章名已是'论', 首段是'谥'变体)
j7 = json.load(open(os.path.join(D3, "7.json"), encoding="utf-8"))
t7 = j7["content"][0]["value"]
print("政府论 [7] 剥离前:", t7[:50].replace(chr(10), " "))
m = re.search(r"第九章谥政治社会和政府的目的", t7)
if m:
    cut = m.end()
    j7["content"][0]["value"] = t7[cut:]
    json.dump(j7, open(os.path.join(D3, "7.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("政府论 [7] 剥离后:", j7["content"][0]["value"][:50].replace(chr(10), " "))
ra.sync_three("e3a52553c303")
print("政府论: 章名修正完成")
