"""
哲人列表彻查：
1. 流派名 → 剔除
2. 同一人不同名 → 去重（优先级：有书 > 名更全 > 名更大 > 普通）
3. 一个条目代表两人 → 拆分
"""
import os, sys, json, re

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LIST_FILE = os.path.join(SCRIPT_DIR, "_batch_philosophers_full.txt")
PHILO_JSON = os.path.join(SCRIPT_DIR, "..", "backend", "data", "philosophers.json")
PHILO_DIR = os.path.join(SCRIPT_DIR, "..", "app", "public", "philosopher")

# ── 加载数据 ──
with open(LIST_FILE, "r", encoding="utf-8") as f:
    names = sorted(set(l.strip() for l in f if l.strip()))

with open(PHILO_JSON, "r", encoding="utf-8") as f:
    philo_db = json.load(f)

# 扫描书籍目录获取有书的作者
KNOWLEDGE_DIR = os.path.join(SCRIPT_DIR, "..", "backend", "modules", "..", "config.py")
sys.path.insert(0, os.path.join(SCRIPT_DIR, "..", "backend"))
from config import KNOWLEDGE_DIR as KD

book_authors = set()
for region in ["东方", "西方"]:
    rp = os.path.join(KD, region)
    if os.path.isdir(rp):
        for author_dir in os.listdir(rp):
            dp = os.path.join(rp, author_dir)
            if os.path.isdir(dp):
                has_books = any(
                    f.endswith(('.pdf', '.epub', '.txt', '.md')) and not f.startswith('.')
                    for f in os.listdir(dp) if os.path.isfile(os.path.join(dp, f))
                )
                if has_books:
                    book_authors.add(author_dir)

print("=" * 60)
print("PHILOSOPHER LIST AUDIT")
print("=" * 60)
print("Total entries: " + str(len(names)))
print("Has books: " + str(len(book_authors)))
print("In philosophers.json: " + str(len(philo_db)))

# ═══════════════════════════════
# CATEGORY 1: 流派名 / 非人物
# ═══════════════════════════════
print("\n" + "=" * 60)
print("CATEGORY 1: SCHOOL/RELIGION NAMES (should be removed)")
print("=" * 60)

school_patterns = [
    # Exact matches for known schools/religions
    "净土宗", "禅宗", "天台宗", "华严宗", "唯识宗", "密宗", "律宗", "三论宗",
    "耆那教", "琐罗亚斯德教", "摩尼教", "景教", "祆教",
    "米利都学派", "埃利亚学派", "智者学派", "毕达哥拉斯学派",
    "犬儒学派", "斯多葛学派", "伊壁鸠鲁学派", "怀疑论", "新柏拉图主义",
    "吠檀多派", "数论派", "胜论派", "正理派", "弥曼差派", "瑜伽派",
    "顺世论", "古文经学", "今文经学",
    # Patterns
]

remove_schools = []
for n in names:
    if n in school_patterns:
        remove_schools.append(n)
    elif n.endswith("宗") and len(n) <= 4 and n not in [""]:
        remove_schools.append(n)
    elif n.endswith("教") and len(n) <= 4 and n not in ["伊斯兰教"]:
        remove_schools.append(n)
    elif n.endswith("派") and len(n) <= 5:
        remove_schools.append(n)
    elif n.endswith("主义") and len(n) <= 5:
        remove_schools.append(n)
    elif "学派" in n and len(n) <= 6:
        remove_schools.append(n)

if remove_schools:
    print("\nTO REMOVE (schools/religions):")
    for n in remove_schools:
        has_book = " [HAS BOOKS!]" if n in book_authors else ""
        in_db = " [in DB]" if n in philo_db else ""
        print("  - " + n + has_book + in_db)
else:
    print("\nNone found!")

# ═══════════════════════════════
# CATEGORY 2: 同一人不同名 (去重)
# ═══════════════════════════════
print("\n" + "=" * 60)
print("CATEGORY 2: POTENTIAL DUPLICATES (same person, different name)")
print("=" * 60)

# Known duplicates mapping
known_dupes = [
    # (shorter/less_preferred, fuller/preferred)
    ("柏拉图", None),  # Not a dupe, just checking
]

# Heuristic: check if one name is a substring of another
dupes_found = []
sorted_names = sorted(names, key=len)
for i, short in enumerate(sorted_names):
    for long in sorted_names[i+1:]:
        if short != long and len(short) >= 2:
            # Short is fully contained in long
            if short in long:
                # Avoid false positives like "孔子" in "孔子弟子"
                if len(short) >= 3 or short in ["程颢", "程颐"]:
                    short_has_book = short in book_authors
                    long_has_book = long in book_authors
                    short_in_db = short in philo_db
                    long_in_db = long in philo_db

                    # Priority: has books > longer name > has DB entry
                    keep = long
                    remove_dup = short
                    reason = "longer name"

                    if short_has_book and not long_has_book:
                        keep = short
                        remove_dup = long
                        reason = "short has books, long doesn't"
                    elif long_has_book and not short_has_book:
                        keep = long
                        remove_dup = short
                        reason = "long has books, short doesn't"

                    dupes_found.append((remove_dup, keep, reason))

# Also check known aliases from name_aliases.json
alias_file = os.path.join(SCRIPT_DIR, "..", "backend", "data", "name_aliases.json")
if os.path.exists(alias_file):
    with open(alias_file, "r", encoding="utf-8") as f:
        aliases = json.load(f)
    # Check for names that are aliases of other names in our list
    for alias, canonical in aliases.items():
        if alias in names and canonical in names:
            dupes_found.append((alias, canonical, "alias→canonical in name_aliases.json"))

if dupes_found:
    print("\nPOTENTIAL DUPLICATES:")
    for remove_dup, keep, reason in dupes_found:
        print("  - REMOVE: " + remove_dup)
        print("    KEEP:   " + keep)
        print("    WHY:    " + reason)
        print()
else:
    print("\nNo obvious substring duplicates found.")

# ═══════════════════════════════
# CATEGORY 3: 一个条目代表两人
# ═══════════════════════════════
print("=" * 60)
print("CATEGORY 3: ONE ENTRY = TWO PEOPLE (should split)")
print("=" * 60)

# Known pairs
known_pairs = {
    "二程": ["程颢", "程颐"],
    "苏格拉底": None,  # single person
}

pairs_found = {}
for n in names:
    if n in known_pairs:
        if known_pairs[n]:
            pairs_found[n] = known_pairs[n]

if pairs_found:
    print("\nTO SPLIT:")
    for orig, parts in pairs_found.items():
        print("  - " + orig + " -> " + ", ".join(parts))
else:
    print("\nNo known pairs to split (二程 already split).")

# ═══════════════════════════════
# EXTRA: Check for suspicious names
# ═══════════════════════════════
print("\n" + "=" * 60)
print("EXTRA: SUSPICIOUS SHORT/LONG NAMES")
print("=" * 60)

for n in sorted(names):
    flags = []
    if len(n) <= 1:
        flags.append("1-CHAR")
    if len(n) >= 20:
        flags.append("VERY_LONG")
    if re.search(r'[0-9]', n):
        flags.append("HAS_DIGITS")
    if flags:
        print("  " + n + "  [" + ", ".join(flags) + "]")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print("Schools to remove: " + str(len(remove_schools)))
print("Duplicates to merge: " + str(len(dupes_found)))
print("Pairs to split: " + str(len(pairs_found)))
print("Current count: " + str(len(names)))
new_count = len(names) - len(remove_schools) - len(dupes_found)
for orig, parts in pairs_found.items():
    new_count = new_count - 1 + len(parts)
print("Projected after cleanup: " + str(new_count))
