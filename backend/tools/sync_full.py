# -*- coding: utf-8 -*-
"""
sync_full.py — 全库三端内容同步（2026-08-07 全库核查 C9/C10）
根因: fix_merge_empty / fix_toc_sync 只改了 PhiAgent 端 book_chapters/meta,
      DP 两端（public 挂载 + backend 主源）没同步 → 117 本 C9 DIFF
动作: PhiAgent（主源）→ DP public + DP backend
  1. book_chapters/<bid> 整体复制（rmtree + copytree）
  2. book_detail/<bid>.json 三端同步（PhiAgent 端为准）
  3. DP public/books.json chapterCount/title 更新（id 匹配）
用法: python sync_full.py [bid ...]（无参数 = 全部 DIFF 书; --all = 全部书）
"""
import sys, os, json, re, shutil, hashlib

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TOOLS = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.dirname(TOOLS)
PHI_CH = os.path.join(BASE, "data", "book_chapters")
PHI_DET = os.path.join(BASE, "data", "book_detail")
DP_BACKEND = os.path.join(BASE, "..", "..", "DeepPhilosophy", "DeepPhilosophy", "backend")
DP_PUBLIC = os.path.join(BASE, "..", "..", "DeepPhilosophy", "DeepPhilosophy", "app", "public")
DP_PUB_CH = os.path.join(DP_PUBLIC, "backend", "data", "book_chapters")
DP_PUB_DET = os.path.join(DP_PUBLIC, "book_detail")
BOOKS_JSON = os.path.join(DP_PUBLIC, "books.json")


def md5dir(d):
    h = hashlib.md5()
    for fn in sorted(os.listdir(d)):
        if fn.endswith(".json"):
            h.update(fn.encode())
            h.update(open(os.path.join(d, fn), "rb").read())
    return h.hexdigest()


def find_diff():
    bad = []
    for bid in sorted(os.listdir(PHI_CH)):
        bd = os.path.join(PHI_CH, bid)
        if not os.path.exists(os.path.join(bd, "meta.json")):
            continue
        s0 = md5dir(bd)
        for root in (DP_PUB_CH, os.path.join(DP_BACKEND, "data", "book_chapters")):
            d = os.path.join(root, bid)
            if not os.path.exists(os.path.join(d, "meta.json")):
                bad.append(bid)
                break
            elif md5dir(d) != s0:
                bad.append(bid)
                break
    return bad


def sync_one(bid):
    bd = os.path.join(PHI_CH, bid)
    meta = json.load(open(os.path.join(bd, "meta.json"), encoding="utf-8"))
    for dst in (os.path.join(DP_PUB_CH, bid),
                os.path.join(DP_BACKEND, "data", "book_chapters", bid)):
        if os.path.exists(dst):
            shutil.rmtree(dst)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copytree(bd, dst)
    # detail 三端
    for det_pa in (os.path.join(PHI_DET, f"{bid}.json"),
                   os.path.join(DP_BACKEND, "data", "book_detail", f"{bid}.json"),
                   os.path.join(DP_PUB_DET, f"{bid}.json")):
        if not os.path.exists(det_pa):
            continue
        det = json.load(open(det_pa, encoding="utf-8"))
        for k in ("toc", "chapterCount", "chapterTitles"):
            det[k] = meta[k]
        det["title"] = meta.get("title", det.get("title"))
        json.dump(det, open(det_pa, "w", encoding="utf-8"), ensure_ascii=False)
    # DP public books.json
    if os.path.exists(BOOKS_JSON):
        bl = json.load(open(BOOKS_JSON, encoding="utf-8"))
        ch = False
        for b in bl:
            if b.get("id") == bid:
                b["chapterCount"] = meta["chapterCount"]
                b["title"] = meta.get("title", b.get("title"))
                ch = True
                break
        if ch:
            json.dump(bl, open(BOOKS_JSON, "w", encoding="utf-8"), ensure_ascii=False)
    return meta.get("title", "")[:24]


def main():
    all_flag = "--all" in sys.argv
    bids = [b for b in sys.argv[1:] if not b.startswith("--")]
    if not bids:
        bids = sorted(os.listdir(PHI_CH)) if all_flag else find_diff()
    n = 0
    for bid in bids:
        bd = os.path.join(PHI_CH, bid)
        if not os.path.exists(os.path.join(bd, "meta.json")):
            print(f"✗ {bid}: 无 meta", flush=True)
            continue
        t = sync_one(bid)
        n += 1
        print(f"✓ {bid} {t!r} 已同步", flush=True)
    print(f"\n完成: 同步 {n} 本", flush=True)


if __name__ == "__main__":
    main()
