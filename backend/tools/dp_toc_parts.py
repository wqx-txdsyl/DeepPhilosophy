# -*- coding: utf-8 -*-
"""
dp_toc_parts.py — 扁平 toc → 层级 toc（part 分组）全库转换（2026-08-07）
规则: 标题以"第X部/编/集/卷/篇"或"与神对话N"开头 → type=part（分组标题, 不可点击）;
      其余条目 → type=chapter（可点击, index = 原扁平序号 = 块文件序号）
安全: 仅当 len(toc) == chapterCount 时转换（toc 可能含无对应文件的条目, 会错位则跳过）
同步: PhiAgent data + DP public/backend（5173 数据源 + git 追踪源）+ DP book_detail
"""
import sys, io, os, json, re, shutil

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CH = os.path.join(BASE_DIR, "data", "book_chapters")
DP_PUBLIC = os.path.join(BASE_DIR, "..", "..", "DeepPhilosophy", "DeepPhilosophy", "app", "public")
DP_BACKEND = os.path.join(BASE_DIR, "..", "..", "DeepPhilosophy", "DeepPhilosophy", "backend")

RE_PART_TITLE = re.compile(r"^(第[一二三四五六七八九十百\d]+[部编集卷篇]|与神对话\d)")


def to_hierarchical(toc, count):
    """扁平 toc → 层级; 返回 None 表示不转换（长度不符/已是层级）"""
    if not toc or isinstance(toc[0], dict):
        return None
    if len(toc) != count:
        return None
    out = []
    for i, t in enumerate(toc):
        s = (t or "").strip()
        if not s:
            continue
        if RE_PART_TITLE.match(s):
            out.append({"type": "part", "title": s})
        else:
            out.append({"type": "chapter", "title": s, "index": i})
    return out


def sync_dp(bid, meta):
    src = os.path.join(CH, bid)
    for dst in (os.path.join(DP_PUBLIC, "backend", "data", "book_chapters", bid),
                os.path.join(DP_BACKEND, "data", "book_chapters", bid)):
        if os.path.exists(dst):
            shutil.rmtree(dst)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copytree(src, dst)
    det_fp = os.path.join(DP_PUBLIC, "book_detail", f"{bid}.json")
    if os.path.exists(det_fp):
        det = json.load(open(det_fp, encoding="utf-8"))
        det["toc"] = meta["toc"]
        det["chapterCount"] = meta["chapterCount"]
        det["chapterTitles"] = meta["chapterTitles"]
        json.dump(det, open(det_fp, "w", encoding="utf-8"), ensure_ascii=False)


def main():
    changed = 0
    scanned = 0
    for bid in sorted(os.listdir(CH)):
        mp = os.path.join(CH, bid, "meta.json")
        if not os.path.exists(mp):
            continue
        meta = json.load(open(mp, encoding="utf-8"))
        toc = meta.get("toc") or []
        if toc and isinstance(toc[0], dict):
            continue  # 已是层级
        scanned += 1
        new_toc = to_hierarchical(toc, meta.get("chapterCount", 0))
        if new_toc is None:
            continue
        meta["toc"] = new_toc
        json.dump(meta, open(mp, "w", encoding="utf-8"), ensure_ascii=False)
        sync_dp(bid, meta)
        changed += 1
        npart = sum(1 for t in new_toc if t["type"] == "part")
        print(f"✓ {bid} {meta.get('title', '')[:20]}: {len(new_toc)} 条 → {npart} 个分组", flush=True)
    print(f"\n完成: 扫描 {scanned} 本扁平 toc, 转换 {changed} 本", flush=True)


if __name__ == "__main__":
    main()
