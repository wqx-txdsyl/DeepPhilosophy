# -*- coding: utf-8 -*-
"""哲学谈话录 全本重导 (2026-08-08) — 库章节连环错位修复
源: F:\philosophy\西方\爱比克泰德\哲学谈话录.pdf (342 页文本层)
结构: 中译者序 + 阿里安的开场白 + 4 卷 94 节 → 96 章, 卷=part(level0), 节=chapter(level1)
边界: 序号递增扫描 ^N. 标题行 (跳过目录页 p4-8); 开场白/中译者序硬编码
用法: python _rebuild_ephictetus.py [--write]
"""
import sys, os, re, json, shutil
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"f:\program\Python\PhiAgent\backend\tools")
import rebuild_auto as ra
import fitz

WRITE = "--write" in sys.argv
SRC = r"F:\philosophy\西方\爱比克泰德\哲学谈话录.pdf"
BOOKS = json.load(open(r"f:\program\Python\PhiAgent\app\public\books.json", encoding="utf-8"))
BID = next(b["id"] for b in BOOKS if b["title"] == "哲学谈话录")
CH = ra.CH
D = os.path.join(CH, BID)

d = fitz.open(SRC)
pages = []  # (page, lines)  行已 strip, 保留空行占位
for i in range(len(d)):
    lines = [ln.strip() for ln in d[i].get_text().split("\n")]
    pages.append((i, lines))
d.close()

VOL_RE = re.compile(r"^第[一二三四]卷$")
TITLE_RE = re.compile(r"^(\d{1,2})[\.、．]\s*(.+)$")
NOTE_NO_RE = re.compile(r"^[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]+$")

# ── 1. 章边界扫描 (p18 起; 序言 p9-17 归中译者序; 卷起始硬编码) ──
VOL_START = {97: 2, 183: 3, 270: 4}   # 第二/三/四卷起始页
bounds = {}   # (page, line_idx) -> (seq, title, vol)
expected = 1
vol = 1
for p, lines in pages:
    if p < 18 or p > 330:
        continue
    for li, ls in enumerate(lines):
        m = TITLE_RE.match(ls)
        if not m:
            continue
        seq, title = int(m.group(1)), m.group(2).strip()
        if len(title) < 3 or title.endswith("。"):
            continue
        if seq == expected:
            bounds[(p, li)] = (seq, title, vol)
            expected += 1
        elif seq == 1 and expected > 1:
            # 仅硬编码卷起始页接受新卷, 其余为页脚重复(忽略)
            if p in VOL_START:
                vol = VOL_START[p]
                bounds[(p, li)] = (1, title, vol)
                expected = 2
# 开场白 + 中译者序
for p, lines in pages:
    if p == 18:
        for li, ls in enumerate(lines):
            if "阿里安" in ls and "开场白" in ls:
                bounds[(18, li)] = (0, "阿里安（Arrian）的开场白", 1)
                break
# 中译者序起点 = p9 第一非空行; 终点 = p18 开场白前
pre_line = next(li for li, ls in enumerate(pages[9][1]) if ls)
bounds[(9, pre_line)] = (-1, "中译者序", 0)

# 已知章标题 norm 集(用于页脚章名过滤; 统一全半角标点)
def norm_key(s):
    s = s.replace("？", "?").replace("，", ",").replace("；", ";").replace("：", ":") \
         .replace("！", "!").replace("（", "(").replace("）", ")")
    return re.sub(r"[\s(《》「」\"'”’【】)\]·•　\-—①-⑳]+", "", s).lower()

known_norms = {}
for (p, li), (seq, title, v) in bounds.items():
    key = norm_key(title)
    known_norms.setdefault(key, []).append((p, li))

order = sorted(bounds.items(), key=lambda kv: (kv[0][0], kv[0][1]))
print(f"边界命中: {len(order)} 章")
for (p, li), (seq, title, v) in order:
    print(f"  p{p}:{li} [v{v} seq{seq}] {title[:36]}")

# ── 2. 逐章提取 ──
def is_junk(ls):
    """页眉/页脚/页码行"""
    if not ls:
        return False
    if VOL_RE.match(ls):
        return True
    if ls == "中译者序" or ls == "哲学谈话录":
        return True
    if re.match(r"^\d{1,4}$", ls):
        return True
    if re.match(r"^\d{1,4}哲学谈话录$", ls):
        return True
    if len(ls) < 18 and "哲学谈话录" in ls and not any(
            "一" <= c <= "鿿" and c not in "哲学谈话录" for c in ls):
        return True
    if re.fullmatch(r"[\sA-Za-z\-0-9.,:;'()]+", ls) and len(ls) > 15:
        return True  # 英文书系名页眉
    m = TITLE_RE.match(ls)
    if m:
        key = norm_key(m.group(2))
        hits = known_norms.get(key, [])
        if hits and all(h != (p_ctx[0], li_ctx[0]) for h in hits):
            return True  # 页脚章名(非边界页)
    return False

p_ctx, li_ctx = [0], [0]

def extract_ch(start, end):
    """start/end = (page, line_idx) 半开区间 → (paras, notes)"""
    paras, notes = [], []
    buf = ""
    for p in range(start[0], end[0] + 1):
        p_ctx[0] = p
        lines = pages[p][1]
        lo = start[1] if p == start[0] else 0
        hi = end[1] if p == end[0] else len(lines)
        # 分离页脚注释 (圈号编号行触发)
        body_lines, note_lines = [], []
        in_note = False
        for li, ls in enumerate(lines[lo:hi]):
            li_ctx[0] = li
            if NOTE_NO_RE.match(ls):
                in_note = True
                note_lines.append("")
                continue
            if in_note:
                note_lines[-1] = note_lines[-1] + ls
                continue
            body_lines.append(ls)
        note_lines = [n for n in note_lines if n]
        notes.extend(note_lines)
        # 正文段切分
        for li, ls in enumerate(body_lines):
            li_ctx[0] = li
            if not ls:
                if buf.strip():
                    paras.append(buf.strip())
                    buf = ""
                continue
            if is_junk(ls):
                continue
            buf += ls
    if buf.strip():
        paras.append(buf.strip())
    return paras, notes

# 提取全部章
chapters = []
for i, ((sp, sl), (seq, title, v)) in enumerate(order):
    ep, el = order[i + 1][0] if i + 1 < len(order) else (341, 999999)
    paras, notes = extract_ch((sp, sl + 1), (ep, el))
    chapters.append({"seq": seq, "title": title, "vol": v, "paras": paras,
                     "notes": notes, "page": sp})
    n = sum(len(x) for x in paras)
    flag = "!!" if n < 150 else ""
    print(f"  [{i:>2}] v{v} {title[:30]:<32} p{sp:<3} 段{len(paras):<3} 字{n:<6} {flag}")

# ── 3. 校验 ──
print("\n=== 校验 ===")
bad = [c for c in chapters if sum(len(x) for x in c["paras"]) < 150]
print(f"过短章: {len(bad)} 个 -> {[c['title'][:20] for c in bad]}")
# 首段残留标题 / 尾段截断
for c in chapters:
    if not c["paras"]:
        print(f"  空章: {c['title']}")
        continue
    first, last = c["paras"][0], c["paras"][-1]
    m = TITLE_RE.match(first)
    if m and len(first) < 60:
        print(f"  首段疑标题残留: [{c['title'][:20]}] {first[:50]}")
    if last and last[-1] not in "。！？；…\"”":
        print(f"  尾段无句末标点: [{c['title'][:20]}] …{last[-40:]}")

if WRITE:
    BAK = os.path.join(CH, "_rebuild_bak", f"{BID}_v1")
    os.makedirs(BAK, exist_ok=True)
    if not os.listdir(BAK):  # 仅首次备份, 防止覆盖已备份的原库
        for f in sorted(os.listdir(D)):
            shutil.copy2(os.path.join(D, f), os.path.join(BAK, f))
    # meta: part(卷) + chapter(节)
    meta = {"bookId": BID, "title": "哲学谈话录", "author": "爱比克泰德",
            "toc": [], "cover": None, "chapterCount": len(chapters), "chapterTitles": []}
    for i, c in enumerate(chapters):
        fp = os.path.join(D, f"{i}.json")
        content = [{"type": "text", "value": x} for x in c["paras"]] + \
                  [{"type": "text", "value": n} for n in c["notes"]]
        json.dump({"title": c["title"], "content": content, "index": i},
                  open(fp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        if c["seq"] == -1:
            meta["toc"].append({"type": "chapter", "title": "中译者序", "index": i, "level": 1})
            meta["chapterTitles"].append("中译者序")
            continue
        # 卷 part: 卷号变化时插入
        if c["vol"] != chapters[i - 1]["vol"] if i > 0 else False:
            meta["toc"].append({"type": "part", "title": f"第{'一二三四'[c['vol']-1]}卷",
                                "index": i, "level": 0})
        t = c["title"]
        if c["seq"] == 0:
            pass
        elif c["seq"] > 0:
            t = f"第{c['seq']}节 {t}"
        meta["toc"].append({"type": "chapter", "title": t, "index": i, "level": 1})
        meta["chapterTitles"].append(t)
    json.dump(meta, open(os.path.join(D, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n写入完成: {len(chapters)} 章")
    ra.sync_three(BID)
    print("sync_three 完成")
