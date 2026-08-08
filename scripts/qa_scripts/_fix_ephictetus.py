# -*- coding: utf-8 -*-
"""哲学谈话录 第4节/第5节 从源PDF文本层重建 (2026-08-08)
边界: 第4节 = p27~p30 正文 + p31 首段('这样一种果实…感谢吗?') ; 第5节 = p31 '爱比克泰德说' ~ p33
页眉过滤: '第一卷'/'哲学谈话录'/纯页码/章标题行; 注释块: 纯编号行后内容 → 章尾注释段
用法: python _fix_ephictetus.py [--write]
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

HEADER_RE = re.compile(
    r"^(第?[一二三四五六七八九十百]+卷|哲学谈话录|[0-9０-９]{1,4}|"
    r"4\.\s*关于进步|5\.\s*反学园派[①]*|6\.\s*论天意)$"
)
NOTE_NO_RE = re.compile(r"^[①②③④⑤⑥⑦⑧⑨⑩]+$")

d = fitz.open(SRC)
pages = []   # (page_idx, paras_list, notes_list)
for i in range(27, 34):
    lines = []
    for ln in d[i].get_text().split("\n"):
        ls = ln.strip()
        if not ls:
            continue
        if HEADER_RE.match(ls):
            continue
        lines.append(ls)
    # 切注释块: 纯编号行启动, 后续行并入注释段(同页内)
    paras, notes, cur_note = [], [], None
    for ls in lines:
        if NOTE_NO_RE.match(ls):
            cur_note = ""
            continue
        if cur_note is not None:
            if ls and (cur_note or not ls.startswith("参看")):
                cur_note += ls
            continue
        paras.append(ls)
    # 注释拼接: 同一编号行后的多行合并（编号行间断时一段注释结束）
    notes_final = []
    for ls in lines:
        if NOTE_NO_RE.match(ls):
            notes_final.append("")
        elif notes_final:
            if ls:
                notes_final[-1] = notes_final[-1] + ls
    notes_final = [n for n in notes_final if n]
    pages.append((i, paras, notes_final))
d.close()

# ── 正文段拼接: 页间续行(页末行尾无标点 → 接下一页首行) + 空行切段 ──
def join_pages(plist):
    """plist: [(page_idx, paras)] → 段落流: 每页 paras 按空行切段, 页间续行"""
    flow = []
    for i, paras in plist:
        flow.extend(paras)
        flow.append("<<PAGE_BREAK>>")
    # 切段: 空行是段界; 页断处若前段尾无句末标点 → 直接拼接
    paras = []
    buf = ""
    for item in flow:
        if item == "<<PAGE_BREAK>>":
            if buf and buf[-1] not in "。！？；:”：』」）】…—\"":
                pass  # 续行, 不切段
            continue
        if not item.strip():
            if buf.strip():
                paras.append(buf.strip())
                buf = ""
            continue
        if buf and buf[-1] not in "。！？；:”：』」）】…—\"":
            buf += item
        else:
            if buf.strip():
                paras.append(buf.strip())
            buf = item
    if buf.strip():
        paras.append(buf.strip())
    return paras

# p27~p30 + p31首段 = 第4节正文; p31(爱比克泰德说起)~p33 = 第5节正文
p27_30 = join_pages([(i, ps) for i, ps, _ in pages[:4]])
p31_head = pages[4][1][0]     # p31 首段 = '这样一种果实…感谢吗?'
p31_rest = pages[4][1][1:]    # p31 其余 = 第5节正文起
p32_33 = join_pages([(i, ps) for i, ps, _ in pages[5:7]])
ch4_paras = p27_30 + [p31_head]
ch5_paras = p31_rest + p32_33
ch4_notes = [n for _, _, ns in pages[:4] for n in ns]
ch5_notes = [n for _, _, ns in pages[4:] for n in ns]

print(f"== 第4节: 正文{len(ch4_paras)}段 + 注释{len(ch4_notes)}段 ==")
for k, p in enumerate(ch4_paras):
    print(f"  [{k}] {p[:60]}")
print(f"  注释: {[n[:30] for n in ch4_notes]}")
print(f"\n== 第5节: 正文{len(ch5_paras)}段 + 注释{len(ch5_notes)}段 ==")
for k, p in enumerate(ch5_paras):
    print(f"  [{k}] {p[:60]}")
print(f"  注释: {[n[:30] for n in ch5_notes]}")

if WRITE:
    BAK = os.path.join(CH, "_rebuild_bak", f"{BID}_v1")
    os.makedirs(BAK, exist_ok=True)
    for idx in (4, 5):
        fp = os.path.join(CH, BID, f"{idx}.json")
        shutil.copy2(fp, os.path.join(BAK, f"{idx}.json"))
    def write_ch(idx, title, paras, notes):
        content = [{"type": "text", "value": p} for p in paras] + [{"type": "text", "value": n} for n in notes]
        json.dump({"title": title, "content": content, "index": idx},
                  open(os.path.join(CH, BID, f"{idx}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    write_ch(4, "第4节 关于进步", ch4_paras, ch4_notes)
    write_ch(5, "第5节 反学园派①", ch5_paras, ch5_notes)
    print("\n写入完成, sync_three...")
    ra.sync_three(BID)
    print("sync_three 完成")
