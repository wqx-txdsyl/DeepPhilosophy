# -*- coding: utf-8 -*-
"""
dp_fix_authors.py — 作者字段修复（2026-08-07, 用户要求）
1. 马恩合著补全: 共产党宣言/德意志意识形态/文集/MEGA/神圣家族 → 卡尔·马克思/弗里德里希·恩格斯
2. 多作者分隔符统一 /（扬布里柯/波爱修斯）
同步: books.json(PhiAgent+DP) / meta.json(PhiAgent+DP双端) / book_detail(PhiAgent+DP)
"""
import sys, io, os, json

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CH = os.path.join(BASE, "data", "book_chapters")
DETAIL = os.path.join(BASE, "data", "book_detail")
PA_BOOKS = os.path.join(BASE, "..", "app", "public", "books.json")
DP_PUBLIC = os.path.join(BASE, "..", "..", "DeepPhilosophy", "DeepPhilosophy", "app", "public")
DP_BACKEND = os.path.join(BASE, "..", "..", "DeepPhilosophy", "DeepPhilosophy", "backend")

# bid → 新 author
AUTHORS = {
    "420f076ba733": "卡尔·马克思/弗里德里希·恩格斯",   # 共产党宣言
    "7729ccdecb0f": "卡尔·马克思/弗里德里希·恩格斯",   # 马克思恩格斯文集
    "ae97dec227b6": "卡尔·马克思/弗里德里希·恩格斯",   # 德意志意识形态
    "1085686cbd33": "卡尔·马克思/弗里德里希·恩格斯",   # MEGA（原 、）
    "c309f9dd4214": "卡尔·马克思/弗里德里希·恩格斯",   # 神圣家族（原 、）
    "26f5e0df6d76": "扬布里柯/波爱修斯",               # 哲学规劝录 哲学的慰藉
}

def main():
    books_pa = json.load(open(PA_BOOKS, encoding="utf-8"))
    books_dp = json.load(open(os.path.join(DP_PUBLIC, "books.json"), encoding="utf-8"))

    for bid, new_author in AUTHORS.items():
        n = 0
        for mp in (os.path.join(CH, bid, "meta.json"),
                   os.path.join(DP_PUBLIC, "backend", "data", "book_chapters", bid, "meta.json"),
                   os.path.join(DP_BACKEND, "data", "book_chapters", bid, "meta.json"),
                   os.path.join(DETAIL, f"{bid}.json"),
                   os.path.join(DP_PUBLIC, "book_detail", f"{bid}.json")):
            if not os.path.exists(mp):
                continue
            data = json.load(open(mp, encoding="utf-8"))
            if isinstance(data, dict) and data.get("author") and data["author"] != new_author:
                data["author"] = new_author
                json.dump(data, open(mp, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
                n += 1
        nb = 0
        for books in (books_pa, books_dp):
            for b in books:
                if b.get("id") == bid and b.get("author") != new_author:
                    b["author"] = new_author
                    nb += 1
        title = "?"
        for b in books_pa:
            if b.get("id") == bid:
                title = b.get("title", "?")
        print(f"✓ {bid} {title[:20]}: author → {new_author} (meta/detail {n}, books {nb})")

    json.dump(books_pa, open(PA_BOOKS, "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(books_dp, open(os.path.join(DP_PUBLIC, "books.json"), "w", encoding="utf-8"), ensure_ascii=False)
    print("\n完成")


if __name__ == "__main__":
    main()
