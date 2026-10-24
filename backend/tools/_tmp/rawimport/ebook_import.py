# -*- coding: utf-8 -*-
"""通用电子书文本导入器（汉译名著/译文丛类，一段一行或空行分段）
配置驱动：ch_rx 章标题；header_rx 页眉剔除；junk 杂质；mode line/merge。
"""
import re, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importer import read_text, full_sync, chunk_long_paras

H = "/Users/sen/Downloads/raw/incoming-codex/raw-text-handoff-20261023"


def pick(bid, cand=None):
    d = os.path.join(H, bid)
    if cand:
        return os.path.join(d, cand, "raw.txt")
    for cs in sorted(os.listdir(d)):
        p = os.path.join(d, cs, "raw.txt")
        if os.path.exists(p):
            return p
    raise FileNotFoundError(bid)


def find_headings(lines, ch_rx, min_gap=60, title_max=60, require_blank=True, toc_run=5):
    """找章标题行。前空行约束；同名近距剔除；目录簇剔除；标题行清理（剥首尾页码、制表符、竖线）。"""
    cands = []
    for i, l in enumerate(lines):
        s = l.strip()
        if not s or len(s) > title_max:
            continue
        if not re.match(ch_rx, s):
            continue
        if require_blank and i > 0 and lines[i - 1].strip():
            prev = lines[i - 1].strip()
            if len(prev) > 8 or not re.match(ch_rx, prev):
                continue
        s2 = re.sub(r"\d{1,4}\s*$", "", s)
        s2 = re.sub(r"^\d{1,4}[\s　]+", "", s2)
        s2 = re.sub(r"[\t|｜]+\s*$", "", s2)
        s2 = re.sub(r"\s+", " ", s2).strip()
        cands.append((i, s2))
    out = []
    k = 0
    while k < len(cands):
        j = k
        while j + 1 < len(cands) and cands[j + 1][0] - cands[j][0] < 3:
            j += 1
        if j - k + 1 >= toc_run:
            k = j + 1
            continue
        out.extend(cands[k:j + 1])
        k = j + 1
    final, last_key, last_i = [], None, -10**9
    for i, s2 in out:
        key = re.sub(r"[\s\u3000]+", "", s2)
        if key == last_key and i - last_i < min_gap:
            continue
        final.append((i, s2))
        last_key, last_i = key, i
    return final


def clean_chapter(lines, junk_res, mode="line"):
    paras, cur = [], []
    for ln in lines:
        s = ln.strip()
        if not s:
            if mode == "line":
                continue
            if cur:
                paras.append("".join(cur))
                cur = []
            continue
        if any(rx.search(s) for rx in junk_res):
            continue
        if mode == "line":
            if s[0] in "①②③④⑤⑥⑦⑧⑨⑩⑪⑫":
                if cur:
                    paras.append("".join(cur))
                    cur = []
                paras.append(s)
            else:
                cur.append(s)
                if len(s) > 30 and s[-1] in "。！？”…；：" or len(cur) >= 12:
                    paras.append("".join(cur))
                    cur = []
        else:
            cur.append(s)
    if cur:
        paras.append("".join(cur))
    return [chunk_long_paras([p])[0] if len(p) > 600 else p for p in paras if p.strip()]




def merge_tiny_dup_chapters(chs):
    """同名章（归一化后）合并到首现章；消除页眉重复产生的碎片章。"""
    def norm(t):
        return re.sub(r"[\s\u3000]+", "", t)
    seen = {}
    out = []
    for t, p2 in chs:
        k = norm(t)
        if k in seen:
            out[seen[k]] = (out[seen[k]][0], out[seen[k]][1] + p2)
            continue
        seen[k] = len(out)
        out.append((t, p2))
    return out

def import_ebook(bid, title, author, region, raw, ch_rx, edition, junk=None,
                 mode="line", part_rx=None, pre_slices=None, ranges=None, title_max=60,
                 known_issues=None, dedupe=True, min_gap=60, require_blank=True):
    """pre_slices: [(title, start, end)] 前置章；ranges: [(start,end)] 只取这些区间。"""
    lines = read_text(raw).split("\n")
    junk_res = [re.compile(j) for j in (junk or [])]
    chs = []
    if ranges:
        segs = ranges
    elif ch_rx is None:
        if pre_slices:
            segs = []
            for (t2, s2, e2) in pre_slices:
                segs.append((t2, s2, len(lines) if e2 is None else e2))
            if pre_slices[-1][2] is not None:
                segs.append(("全文", pre_slices[-1][2], len(lines)))
        else:
            segs = [("全文", 0, len(lines))]
    else:
        heads = find_headings(lines, ch_rx, title_max=title_max, min_gap=min_gap,
                              require_blank=require_blank)
        bounds = [h[0] for h in heads]
        segs = []
        for k, (i, t) in enumerate(heads):
            e = bounds[k + 1] if k + 1 < len(bounds) else len(lines)
            segs.append((t, i, e))
        if bounds:
            if pre_slices:
                for (t2, s2, e2) in pre_slices:
                    chs.append((t2, clean_chapter(lines[s2:e2], junk_res, mode)))
            else:
                front = clean_chapter(lines[0:bounds[0]], junk_res, mode)
                if len(front) >= 6:
                    chs.append(("卷首", front))
        else:
            segs = [("全文", 0, len(lines))]
    for seg in segs:
        if len(seg) == 3:
            t2, s2, e2 = seg
            if e2 is None:
                e2 = len(lines)
            chs.append((t2, clean_chapter(lines[s2:e2], junk_res, mode)))
        else:
            s2, e2 = seg
            chs.append(("全文", clean_chapter(lines[s2:e2], junk_res, mode)))
    if dedupe:
        chs = merge_tiny_dup_chapters(chs)
        chs = [(t2, p2) for t2, p2 in chs if p2]
    meta = {"bookId": bid, "title": title, "author": author, "region": region}
    m, ok, outp = full_sync(bid, meta, chs, edition)
    print(f"== {title} [{bid}] verify={ok} chapters={len(chs)} blocks={sum(len(p) for _, p in chs)}")
    if not ok:
        print(outp[-800:])
    for t2, p2 in chs[:6]:
        print(f"   {len(p2):4d}b {t2[:34]}")
    if known_issues:
        for ki in known_issues:
            print("   ⚠", ki)
    return ok, chs
