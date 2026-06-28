"""fix_stars.py v2 — 全量补全星丛哲学家 + 别名"""
import re, os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from philosophers_db import PHILOSOPHERS, NAME_ALIASES, get_philosopher_info

# === 1. Extract all thinker names ===
jsx_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        'app', 'src', 'pages', 'SchoolDetailPage.jsx')
with open(jsx_path, 'r', encoding='utf-8') as f:
    content = f.read()

all_names = set()
blocks = re.split(r'thinkers:\s*\[', content)
for block in blocks[1:]:
    depth, end = 0, 0
    for i, ch in enumerate(block):
        if ch == '[': depth += 1
        elif ch == ']':
            depth -= 1
            if depth < 0: end = i; break
    thinker_block = block[:end]
    for m in re.finditer(r'''name:\s*['"]([^'"]+)['"]''', thinker_block):
        all_names.add(m.group(1))

for m in re.finditer(r'''(?:from|to):\s*['"]([^'"]+)['"]''', content):
    all_names.add(m.group(1))

# Clean names
cleaned = set()
for name in all_names:
    name = name.strip()
    if not name or len(name) < 2: continue
    if '与' in name and 6 < len(name) < 20:
        for part in name.replace(' 与 ', '与').split('与'):
            part = part.strip()
            if len(part) >= 2: cleaned.add(part)
    else:
        name = re.sub(r'[（(].*?[）)]', '', name)
        for prefix in ['早期','后期','晚期']:
            if name.startswith(prefix): name = name[len(prefix):]
        if len(name) >= 2: cleaned.add(name)

cleaned = sorted(cleaned)
print(f'星丛思考者: {len(cleaned)}')

# === 2. Load book authors (for school/country hints) ===
summaries_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'book_summaries.json')
book_authors = {}
with open(summaries_path, 'r', encoding='utf-8') as f:
    summaries = json.load(f)
for key in summaries:
    if '||' in key:
        title, author = key.split('||', 1)
        if author and author not in ('合集&概述','合集','概述','其他'):
            region = '西方'  # default
            # Guess region from path
            book_tags = summaries[key].get('tags', []) if isinstance(summaries[key], dict) else []
            book_authors[author] = {'title': title, 'tags': book_tags}

print(f'书籍作者: {len(book_authors)}')

# === 3. Build match table ===
existing = dict(PHILOSOPHERS)
aliases = dict(NAME_ALIASES)

# Which thinkers are already covered?
matched = set()
for thinker in cleaned:
    if thinker in existing:
        matched.add(thinker)
    elif thinker in aliases:
        matched.add(thinker)
    elif get_philosopher_info(thinker):
        matched.add(thinker)

unmatched = [t for t in cleaned if t not in matched]
print(f'已覆盖: {len(matched)}, 需新增: {len(unmatched)}')

# === 4. For unmatched, try to find book author info ===
def fuzzy_find_book_author(thinker, book_authors):
    """Find the closest book author for a thinker name"""
    if thinker in book_authors:
        return thinker, book_authors[thinker]
    # Try removing prefixes/suffixes
    for prefix in ['卡尔·','伯特兰·','索伦·','西蒙娜·德·','弗里德里希·','托马斯·','约翰·',
                   '威廉·','大卫·','亨利·','保罗·','罗兰·','彼得·','罗伯特·','查尔斯·',
                   '乔治·','阿尔弗雷德·']:
        if thinker.startswith(prefix):
            short = thinker[len(prefix):]
            if short in book_authors:
                return short, book_authors[short]
    # Check if thinker is a substring of any book author or vice versa
    for author, info in book_authors.items():
        if len(thinker) >= 3 and len(author) >= 3:
            if thinker in author or author in thinker:
                return author, info
            # Character overlap
            t_set = set(thinker)
            a_set = set(author)
            if len(t_set & a_set) >= min(len(t_set), len(a_set)) * 0.6:
                return author, info
    return None, None

# Also extract school info from the JSX (which school each thinker belongs to)
# Parse school context around each thinkers block
school_contexts = {}
school_pattern = re.finditer(
    r"(\w+_DATA|CONSTELLATION_DATA.*?)\s*=\s*\{[^}]*?name:\s*'([^']+)'[^}]*?\}",
    content, re.DOTALL
)

# === 5. Generate new philosophers ===
new_entries = {}
new_aliases = {}

for thinker in unmatched:
    # Try fuzzy match to book author
    book_author, book_info = fuzzy_find_book_author(thinker, book_authors)

    if book_author and book_author != thinker:
        # This thinker is a variant of an existing book author
        # Add alias to the book author
        if book_author in existing or book_author in new_entries:
            new_aliases[thinker] = book_author
            continue
        # Otherwise create entry using the canonical book author name
        thinker_to_add = book_author
        tags = book_info['tags'] if book_info else []
    else:
        thinker_to_add = thinker
        tags = book_info['tags'] if book_info else []

    if thinker_to_add in existing or thinker_to_add in new_entries:
        if thinker != thinker_to_add:
            new_aliases[thinker] = thinker_to_add
        continue

    # Build entry
    school_tags = [t for t in tags if t not in ('待收录','全集/选集','专著','对话/语录','pdf','epub')][:2]
    school_str = ' / '.join(school_tags) if school_tags else ''

    new_entries[thinker_to_add] = {
        "era": "",
        "country": "",
        "school": school_str,
        "bio": f"{thinker_to_add}，其哲学著作与思想收录于本馆。",
        "wiki_url": f"https://en.wikipedia.org/wiki/{thinker_to_add}",
    }

# Recheck: any unmatched still without entry?
for thinker in unmatched:
    if thinker not in existing and thinker not in new_entries and thinker not in new_aliases:
        # Check if fuzzy book author match now has an entry
        book_author, _ = fuzzy_find_book_author(thinker, book_authors)
        if book_author and (book_author in existing or book_author in new_entries):
            if thinker != book_author:
                new_aliases[thinker] = book_author
        else:
            # Add as bare-minimum entry
            new_entries[thinker] = {
                "era": "",
                "country": "",
                "school": "",
                "bio": f"{thinker}，哲学思想史上的人物。",
                "wiki_url": f"https://en.wikipedia.org/wiki/{thinker}",
            }

print(f'新增哲学家条目: {len(new_entries)}')
print(f'新增别名: {len(new_aliases)}')

# === 6. Update philosophers_db.py ===
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'philosophers_db.py')
bak_path = db_path + '.bak2'
if not os.path.exists(bak_path):
    import shutil
    shutil.copy2(db_path, bak_path)
    print(f'备份: {bak_path}')

with open(db_path, 'r', encoding='utf-8') as f:
    db_lines = f.readlines()

# Find insertion points
ph_end = None
alias_start = None
alias_end = None

for i, line in enumerate(db_lines):
    if 'PHILOSOPHERS = {' in line: pass
    if 'NAME_ALIASES = {' in line:
        alias_start = i
        # ph_end is 2 lines before alias (blank + comment)
        for j in range(i-1, max(i-20, 0), -1):
            if db_lines[j].strip() == '}':
                ph_end = j
                break
    if alias_start and i > alias_start and line.strip() == '}' and not alias_end:
        alias_end = i

# Insert new philosophers
new_ph_lines = ['\n    # ====== 星丛补全 ({n}) ======\n'.format(n=len(new_entries))]
for name in sorted(new_entries):
    info = new_entries[name]
    new_ph_lines.append(f'    "{name}": {{\n')
    new_ph_lines.append(f'        "era": "{info["era"]}",\n')
    new_ph_lines.append(f'        "country": "{info["country"]}",\n')
    new_ph_lines.append(f'        "school": "{info["school"]}",\n')
    bio = info['bio'].replace('\\', '\\\\').replace('"', '\\"')
    new_ph_lines.append(f'        "bio": "{bio}",\n')
    new_ph_lines.append(f'        "wiki_url": "{info["wiki_url"]}",\n')
    new_ph_lines.append(f'    }},\n')

# Insert new aliases
new_al_lines = ['    # ====== 星丛别名 ({n}) ======\n'.format(n=len(new_aliases))]
for alias in sorted(new_aliases):
    target = new_aliases[alias]
    new_al_lines.append(f'    "{alias}": "{target}",\n')

# Insert aliases INSIDE the NAME_ALIASES dict (before closing })
new_lines = (db_lines[:ph_end] + new_ph_lines + db_lines[ph_end:alias_end] +
             new_al_lines + ['}\n'] + db_lines[alias_end+1:])

with open(db_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

# Verify
import importlib, philosophers_db
importlib.reload(philosophers_db)
final_count = len(philosophers_db.PHILOSOPHERS)
final_aliases = len(philosophers_db.NAME_ALIASES)

print(f'\n=== COMPLETE ===')
print(f'原: 148 哲学家, 4 别名')
print(f'现: {final_count} 哲学家, {final_aliases} 别名')
print(f'新增: {len(new_entries)} 哲学家, {len(new_aliases)} 别名')
