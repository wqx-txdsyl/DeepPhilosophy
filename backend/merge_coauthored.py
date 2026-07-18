"""合并多人合著的重复书籍条目（马恩合著被重复录入）"""
import json, os, shutil

BASE = os.path.dirname(__file__)
BOOKS_PATH = os.path.join(BASE, "..", "app", "public", "books.json")
DETAIL_DIR = os.path.join(BASE, "..", "app", "public", "book_detail")
CHAPTERS_DIR = os.path.join(BASE, "..", "app", "public", "book_chapters")
CHAPTERS_BACKEND = os.path.join(BASE, "data", "book_chapters")

# 合著映射：{ 主标题: (保留id, 移除id, 合并后作者) }
MERGES = {
    "共产党宣言": ("420f076ba733", "77f5d11ce69f", "卡尔·马克思 / 弗里德里希·恩格斯"),
    "马克思恩格斯文集": ("7729ccdecb0f", "9f2c734a9c8f", "卡尔·马克思 / 弗里德里希·恩格斯"),
    "德意志意识形态（节选本）": ("ae97dec227b6", "3aa06a397eb5", "卡尔·马克思 / 弗里德里希·恩格斯"),
    "MEGA：陶伯特版《德意志意识形态·费尔巴哈》": ("1085686cbd33", "a87ccfd55328", "卡尔·马克思 / 弗里德里希·恩格斯"),
    "神圣家族": ("21113ab6076e", "90f905a248c6", "卡尔·马克思 / 弗里德里希·恩格斯"),
}

# ─── 1. 更新 books.json ───
books = json.load(open(BOOKS_PATH, "r", encoding="utf-8"))
removed_ids = set(v[1] for v in MERGES.values())
new_books = []
for b in books:
    if b["id"] in removed_ids:
        continue
    for title, (keep_id, remove_id, author) in MERGES.items():
        if b["id"] == keep_id:
            b["author"] = author
            break
    new_books.append(b)
removed_count = len(books) - len(new_books)
json.dump(new_books, open(BOOKS_PATH, "w", encoding="utf-8"), ensure_ascii=False)
print(f"books.json: {len(books)} → {len(new_books)} (removed {removed_count})")

# ─── 2. 更新 book_detail JSONs ───
for title, (keep_id, remove_id, author) in MERGES.items():
    # 更新保留的 detail
    keep_path = os.path.join(DETAIL_DIR, f"{keep_id}.json")
    if os.path.exists(keep_path):
        d = json.load(open(keep_path, "r", encoding="utf-8"))
        d["author"] = author
        json.dump(d, open(keep_path, "w", encoding="utf-8"), ensure_ascii=False)
        print(f"detail updated: {keep_id} author → {author}")

    # 删除重复的 detail
    for dir_path in [DETAIL_DIR]:
        rm = os.path.join(dir_path, f"{remove_id}.json")
        if os.path.exists(rm):
            os.remove(rm)
            print(f"detail removed: {remove_id}")

# ─── 3. 更新章节 meta.json 中的 author ───
for title, (keep_id, remove_id, author) in MERGES.items():
    # 更新保留的 meta
    for chapters_root in [CHAPTERS_DIR, CHAPTERS_BACKEND]:
        meta_path = os.path.join(chapters_root, keep_id, "meta.json")
        if os.path.exists(meta_path):
            m = json.load(open(meta_path, "r", encoding="utf-8"))
            if m.get("author") != author:
                m["author"] = author
                json.dump(m, open(meta_path, "w", encoding="utf-8"), ensure_ascii=False)
                print(f"meta updated: {keep_id} author → {author}")

    # 删除重复的章节数据
    for chapters_root in [CHAPTERS_DIR, CHAPTERS_BACKEND]:
        rm_dir = os.path.join(chapters_root, remove_id)
        if os.path.exists(rm_dir):
            shutil.rmtree(rm_dir)
            print(f"chapters removed: {remove_id} ({chapters_root})")

print("\nDone.")
