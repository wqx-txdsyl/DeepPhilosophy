# -*- coding: utf-8 -*-
"""
dp_sync_all.py — 双端全量同步（2026-08-07, 最高规则落地）
① book_chapters: PhiAgent data → DP public(5173) + DP backend(git/CDN 源)
② book_detail:   PhiAgent data → DP public
③ books.json:    DP public 全量刷新 chapterCount/title（以 meta 为准）

⚠️ 2026-08-12 教训: PHA 侧不是所有书的权威——道德经 PHA 曾留旧 85 章脏版、
   费希特 PHA 曾留文本粘连损坏版, 全量覆盖会把 DP git 的清洗/完整版覆盖坏。
   跑本脚本前必须先做 PHA vs DP 全库一致性核对（md5dir 对比, 见 dp_sync_books 说明),
   不一致时以 DP git 版本为准恢复 PHA, 再同步。
"""
import sys, io, os, json, shutil

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CH = os.path.join(BASE_DIR, "data", "book_chapters")
DETAIL = os.path.join(BASE_DIR, "data", "book_detail")
DP_PUBLIC = os.path.join(BASE_DIR, "..", "..", "DeepPhilosophy", "app", "public")
DP_BACKEND = os.path.join(BASE_DIR, "..", "..", "DeepPhilosophy", "backend")


def sync_chapters():
    n = 0
    for bid in sorted(os.listdir(CH)):
        src = os.path.join(CH, bid)
        if not os.path.exists(os.path.join(src, "meta.json")):
            continue
        for dst in (os.path.join(DP_PUBLIC, "backend", "data", "book_chapters", bid),
                    os.path.join(DP_BACKEND, "data", "book_chapters", bid)):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copytree(src, dst)
        n += 1
    print(f"① book_chapters 同步 {n} 本 → DP public + DP backend", flush=True)


def sync_details():
    n = 0
    dst_dir = os.path.join(DP_PUBLIC, "book_detail")
    os.makedirs(dst_dir, exist_ok=True)
    for fn in os.listdir(DETAIL):
        if not fn.endswith(".json"):
            continue
        shutil.copy2(os.path.join(DETAIL, fn), os.path.join(dst_dir, fn))
        n += 1
    print(f"② book_detail 同步 {n} 份 → DP public", flush=True)


def sync_books_json():
    bf = os.path.join(DP_PUBLIC, "books.json")
    books = json.load(open(bf, encoding="utf-8"))
    fixed = 0
    for b in books:
        bid = b.get("id")
        mp = os.path.join(CH, bid, "meta.json")
        if not os.path.exists(mp):
            continue
        meta = json.load(open(mp, encoding="utf-8"))
        if b.get("chapterCount") != meta.get("chapterCount"):
            b["chapterCount"] = meta.get("chapterCount")
            fixed += 1
        if b.get("title") != meta.get("title"):
            b["title"] = meta.get("title")
            fixed += 1
    json.dump(books, open(bf, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"③ books.json 刷新 {fixed} 处 chapterCount/title", flush=True)


def main():
    sync_chapters()
    sync_details()
    sync_books_json()
    print("同步完成", flush=True)


if __name__ == "__main__":
    main()
