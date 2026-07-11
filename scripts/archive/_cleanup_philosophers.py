"""清理哲人列表：去重、拆分、移除非人物条目"""
import os, sys

LIST_FILE = os.path.join(os.path.dirname(__file__), "_batch_philosophers_full.txt")
IMG_DIR = os.path.join(os.path.dirname(__file__), "..", "app", "public", "philosopher")

def safe_name(name):
    return name.replace("/", "-").replace("\\", "-").replace(":", "：")

def delete_images(names):
    for name in names:
        s = safe_name(name)
        for sub in ["", "thumb/"]:
            path = os.path.join(IMG_DIR, sub, s + ".jpg")
            if os.path.exists(path):
                os.remove(path)
                print("  Deleted image: " + path)

with open(LIST_FILE, "r", encoding="utf-8") as f:
    names = [l.strip() for l in f if l.strip()]

before = len(names)

# ── 删除 ──
remove = ["净土宗", "古文经学", "罗森堡", "二程"]
names = [n for n in names if n not in remove]
print("Removed: " + str(remove))
delete_images(remove)

# ── 拆分 二程 → 程颢, 程颐 ──
names.append("程颢")
names.append("程颐")
print("Added: 程颢, 程颐 (split from 二程)")

# ── 排序写回 ──
names = sorted(set(names))
after = len(names)
print("Before: " + str(before) + " → After: " + str(after))

with open(LIST_FILE, "w", encoding="utf-8") as f:
    for n in names:
        f.write(n + "\n")

print("Done. List saved to " + LIST_FILE)
