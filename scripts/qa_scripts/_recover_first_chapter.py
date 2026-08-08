# -*- coding: utf-8 -*-
"""恢复被误删的第 0 章（_del_first_chapter 的 os.remove bug 删了真第一章）:
  拟仿物    0.json = OCR p4~p14 (關於布希亞的它方與它者, 繁体)  + 删残留 20.json
  自然与快乐 0.json = OCR p18~p19首段 (第1节 导论①)             + 删残留 81.json
段落逻辑与 dp_pdf_import 一致: merge_lines(行尾中文+行首中文拼接) + 空行切段
用法: python _recover_first_chapter.py
"""
import sys, os, re, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, r"f:\program\Python\PhiAgent\backend\tools")
import rebuild_auto as ra

CKPT = r"f:\program\Python\PhiAgent\backend\data\dp_pdf_import_ckpt.json"
ckpt = json.load(open(CKPT, encoding="utf-8"))

def _is_cjk(c):
    return 0x4E00 <= ord(c) <= 0x9FFF or 0x3400 <= ord(c) <= 0x4DBF

def merge_lines(text):
    lines = text.split("\n")
    merged = []
    for line in lines:
        s = line.strip()
        if not s:
            merged.append("")
            continue
        if merged and merged[-1] and _is_cjk(merged[-1][-1]) and _is_cjk(s[0]):
            merged[-1] += s
        else:
            merged.append(s)
    return "\n".join(merged)

def to_paras(ch_text):
    return [p.strip() for p in re.split(r"\n\s*\n", ch_text) if p.strip()]

PAGE_RE = re.compile(r"^\d{1,6}$")

def pages_text(ck, key, lo, hi):
    """lo..hi 页 OCR 文本拼接, 过滤纯页码行"""
    pages = ck["ocr"][key]
    parts = []
    for i in range(lo, hi + 1):
        t = pages.get(str(i), "")
        if not t or t == "__FAILED__":
            continue
        lines = [l for l in t.split("\n") if not PAGE_RE.match(l.strip())]
        parts.append("\n".join(lines))
    return "\n\n".join(parts)

def write_ch(bid, title, paras):
    d = os.path.join(ra.CH, bid)
    content = [{"type": "text", "value": p} for p in paras]
    json.dump({"title": title, "content": content, "index": 0},
              open(os.path.join(d, "0.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"  写 0.json: {title} 段{len(paras)} 字{sum(len(p) for p in paras)}")

def del_residual(bid, n):
    """删除残留的 n.json（前移后尾部重复文件）"""
    fp = os.path.join(ra.CH, bid, f"{n}.json")
    if os.path.exists(fp):
        os.remove(fp)
        print(f"  删残留 {n}.json")

# ── 拟仿物: 第一章 = p4~p14 (p15 空白, p16 第二章) ──
KEY1 = "西方_让_鲍德里亚_擬仿物與擬像.pdf"
raw1 = pages_text(ckpt, KEY1, 4, 14)
paras1 = to_paras(merge_lines(raw1))
# 去掉页眉/小标题行干扰: 首段若以"關於布希亞的它方"开头则保留为正文标题?
write_ch("cc9d0d9358a7", "關於布希亞的它方與它者", paras1)
del_residual("cc9d0d9358a7", 20)

# ── 自然与快乐: 第一章 = p18 全页 + p19 "2.标准"标题之前 ──
KEY2 = "西方_伊壁鸠鲁_自然与快乐.pdf"
pages = ckpt["ocr"][KEY2]
t18 = pages.get("18", "")
t19 = pages.get("19", "")
lines19 = t19.split("\n")
cut = next((i for i, l in enumerate(lines19) if l.strip().startswith("2.标准")), len(lines19))
raw2 = t18 + "\n\n" + "\n".join(lines19[:cut])
paras2 = to_paras(merge_lines(raw2))
write_ch("221f09d04944", "第1节 导论①", paras2)
del_residual("221f09d04944", 81)

for bid in ("cc9d0d9358a7", "221f09d04944"):
    ra.sync_three(bid)
print("sync_three 完成")
