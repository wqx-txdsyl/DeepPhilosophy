"""
一次性修复 book_summaries.json 的 key 格式
从 {title} 改为 {title}||{author} — 解决同名不同作者的书籍相互覆盖问题
"""
import json, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SUMMARIES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "book_summaries.json")

# Load backend to scan books
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import main as backend_main
from config import KNOWLEDGE_DIR

print(f"Knowledge dir: {KNOWLEDGE_DIR}")

# Scan all books
books = backend_main.scan_books()
print(f"Books scanned: {len(books)}")

# Load current summaries (title-keyed)
with open(SUMMARIES_PATH, 'r', encoding='utf-8') as f:
    old_summaries = json.load(f)
print(f"Old entries: {len(old_summaries)}")

# Build new summaries with title||author keys
new_summaries = {}
for b in books:
    title = b["title"]
    author = b["author"]
    key = f"{title}||{author}"

    if title in old_summaries:
        new_summaries[key] = old_summaries[title]
    elif key in old_summaries:
        new_summaries[key] = old_summaries[key]
    else:
        # Create empty entry
        new_summaries[key] = {"summary": "", "tags": []}

print(f"New entries: {len(new_summaries)}")

# Verify no duplicates lost
old_titles = set(old_summaries.keys())
new_keys = set(new_summaries.keys())
covered = sum(1 for t in old_titles for k in new_keys if k.startswith(t + "||"))
print(f"Old titles covered in new keys: {covered}/{len(old_titles)}")

# Save
with open(SUMMARIES_PATH, 'w', encoding='utf-8') as f:
    json.dump(new_summaries, f, ensure_ascii=False, indent=2)
print(f"Saved {len(new_summaries)} entries to {SUMMARIES_PATH}")
print("Done!")
