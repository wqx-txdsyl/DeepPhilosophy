# -*- coding: utf-8 -*-
"""
dp_sync_fixed.py — 已修复书的双端同步补漏（2026-08-07）
修复 dp_verify_dual 报的 29 个问题:
  1. 6 本 epub 重导（5 本 + 存在与时间）: chapters → DP 双端, detail → DP public, books.json chapterCount
  2. 与神对话: books.json chapterCount 53→146
  3. 5 本 OCR 修复书: PhiAgent data/book_detail 从 meta 重建（与 DP public 对齐）
"""
import sys, io, os, json, shutil

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CH = os.path.join(BASE, "data", "book_chapters")
DETAIL = os.path.join(BASE, "data", "book_detail")
DP_PUBLIC = os.path.join(BASE, "..", "..", "DeepPhilosophy", "DeepPhilosophy", "app", "public")
DP_BACKEND = os.path.join(BASE, "..", "..", "DeepPhilosophy", "DeepPhilosophy", "backend")
PA_BOOKS = os.path.join(BASE, "..", "app", "public", "books.json")   # PhiAgent 前端
DP_BOOKS = os.path.join(DP_PUBLIC, "books.json")                     # DP 前端

# ① 6 本 epub 重导（章节/块全变）
EPUB_BIDS = ["30cc02edc262", "32bcb0d7a466", "46736478a11d", "be928be3b1c9",
             "f6af30aab723", "e5d3c15b8a24"]  # 存在与时间 bid 占位, 下方按 meta 匹配
# ② 与神对话: 只更新 books.json chapterCount
YSDH_BID = "7657ef4a2cd3"
# ③ 5 本 OCR 修复书: detail 重建
OCR_BIDS = None  # 自动: detail 不一致的书


def find_bid(title_key, exact=False):
    for bid in sorted(os.listdir(CH)):
        mp = os.path.join(CH, bid, "meta.json")
        if not os.path.exists(mp):
            continue
        meta = json.load(open(mp, encoding="utf-8"))
        t = (meta.get("title") or "")
        if (t == title_key) if exact else (title_key in t and "释义" not in t):
            return bid
    return None


def sync_chapters(bid):
    src = os.path.join(CH, bid)
    for dst in (os.path.join(DP_PUBLIC, "backend", "data", "book_chapters", bid),
                os.path.join(DP_BACKEND, "data", "book_chapters", bid)):
        if os.path.exists(dst):
            shutil.rmtree(dst)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copytree(src, dst)


def sync_detail_public(bid):
    det_fp = os.path.join(DETAIL, f"{bid}.json")
    if os.path.exists(det_fp):
        shutil.copy2(det_fp, os.path.join(DP_PUBLIC, "book_detail", f"{bid}.json"))


def rebuild_detail_from_meta(bid):
    """从 meta 重建 detail（toc/chapterCount/chapterTitles）, 保留既有 summary/tags/cover"""
    meta = json.load(open(os.path.join(CH, bid, "meta.json"), encoding="utf-8"))
    det_fp = os.path.join(DETAIL, f"{bid}.json")
    det = json.load(open(det_fp, encoding="utf-8")) if os.path.exists(det_fp) else {}
    n = meta.get("chapterCount", 0)
    det.update({"bookId": bid, "title": meta.get("title"), "author": meta.get("author"),
                "toc": meta.get("toc") or [], "chapterCount": n,
                "chapterTitles": [json.load(open(os.path.join(CH, bid, f"{i}.json"), encoding="utf-8")).get("title", "")
                                  for i in range(n)],
                "region": meta.get("region"), "file_type": meta.get("file_type")})
    json.dump(det, open(det_fp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return det


def update_books_count(bid, count, name):
    for bf in (DP_BOOKS, PA_BOOKS):
        if not os.path.exists(bf):
            continue
        books = json.load(open(bf, encoding="utf-8"))
        changed = False
        for b in books:
            if b.get("id") == bid and b.get("chapterCount") != count:
                b["chapterCount"] = count
                changed = True
        if changed:
            json.dump(books, open(bf, "w", encoding="utf-8"), ensure_ascii=False)
            print(f"  ✓ {name}: books.json chapterCount → {count}")


def main():
    # ① epub 重导同步
    ex = find_bid("存在与时间")
    if ex is None:
        print("!! 找不到 存在与时间 bid, 跳过")
    for bid in [b for b in EPUB_BIDS if b != "e5d3c15b8a24"] + ([ex] if ex else []):
        meta = json.load(open(os.path.join(CH, bid, "meta.json"), encoding="utf-8"))
        name = meta.get("title", bid)
        print(f"① {name} ({bid}):", flush=True)
        sync_chapters(bid)
        sync_detail_public(bid)
        update_books_count(bid, meta["chapterCount"], name)
        print("   ✓ chapters/detail/books.json 已同步", flush=True)

    # ② 与神对话 books.json
    meta = json.load(open(os.path.join(CH, YSDH_BID, "meta.json"), encoding="utf-8"))
    update_books_count(YSDH_BID, meta["chapterCount"], "与神对话")

    # ③ OCR 修复书 detail 重建（PhiAgent detail ≠ DP public 的）
    for bid in sorted(os.listdir(CH)):
        mp = os.path.join(CH, bid, "meta.json")
        if not os.path.exists(mp):
            continue
        det_fp = os.path.join(DETAIL, f"{bid}.json")
        dp_fp = os.path.join(DP_PUBLIC, "book_detail", f"{bid}.json")
        if not (os.path.exists(det_fp) and os.path.exists(dp_fp)):
            continue
        if open(det_fp, "rb").read() == open(dp_fp, "rb").read():
            continue
        meta = json.load(open(mp, encoding="utf-8"))
        rebuild_detail_from_meta(bid)
        shutil.copy2(det_fp, dp_fp)
        print(f"③ {meta.get('title','')[:24]} ({bid}): detail 已重建并同步 DP public", flush=True)

    print("\n完成")


if __name__ == "__main__":
    main()
