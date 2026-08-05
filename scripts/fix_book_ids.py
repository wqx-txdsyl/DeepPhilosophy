"""修复 books.json ID，与 rebuild_spine 文件路径对齐。无重复保证。"""
import os, json, hashlib

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOOKS_FILE = os.path.join(BASE, 'app', 'public', 'books.json')
DETAIL_DIR = os.path.join(BASE, 'app', 'public', 'book_detail')
BOOKS_DIR = 'F:/philosophy'

with open(BOOKS_FILE, 'r', encoding='utf-8') as f:
    books = json.load(f)

# 第一遍：收集所有文件 → ID 映射
all_files = {}  # rel_path -> id
for root, dirs, files in os.walk(BOOKS_DIR):
    for f in files:
        fp = os.path.join(root, f)
        rel = os.path.relpath(fp, BOOKS_DIR).replace('\\', '/')
        bid = hashlib.md5(rel.encode()).hexdigest()[:12]
        all_files[rel] = bid

# 第二遍：为每本书匹配最合适的文件（每个文件只能用一次）
used_files = set()

def match_score(title, filename):
    """0-100 匹配度"""
    t = title.lower()
    f = filename.lower()
    # 精确匹配
    t_short = t.split('：')[0].split(':')[0].split('（')[0].split('(')[0].strip().rstrip('.')
    f_short = f.split('：')[0].split(':')[0].split('（')[0].split('(')[0].strip().rstrip('.')
    if t_short == f_short: return 100
    if t in f or f in t: return 85
    # 字符重叠率
    common = len(set(t) & set(f))
    total = len(set(t) | set(f))
    return int(common / max(total, 1) * 50)

fixed = 0
for b in books:
    region = b.get('region', '')
    author = b.get('author', '')
    title = b.get('title', '')
    ext = b.get('file_type', 'epub')
    old_id = b['id']

    # 在该作者目录下找候选文件
    candidates = []
    prefix = region + '/' + author + '/'
    for rel, bid in all_files.items():
        if rel.startswith(prefix) and rel.endswith('.' + ext) and rel not in used_files:
            fname = os.path.basename(rel)
            score = match_score(title, fname)
            if score > 0:
                candidates.append((score, rel, bid))

    candidates.sort(reverse=True)
    # 要求：有候选、最高分>=50、且最高分独享（不与他人共享同一个文件）
    if candidates and candidates[0][0] >= 50:
        best_score, best_rel, best_id = candidates[0]
        # 检查是否只有这本书能匹配到这个文件（独享）
        is_unique = len(candidates) == 1 or candidates[0][0] > candidates[1][0] + 20
        if is_unique:
            used_files.add(best_rel)
            if best_id != old_id:
                old_dp = os.path.join(DETAIL_DIR, old_id + '.json')
                new_dp = os.path.join(DETAIL_DIR, best_id + '.json')
                if os.path.exists(old_dp) and not os.path.exists(new_dp):
                    os.rename(old_dp, new_dp)
                b['id'] = best_id
                fixed += 1

# 验证
from collections import Counter
ids = [b['id'] for b in books]
dupes = [i for i, c in Counter(ids).items() if c > 1]
if dupes:
    print('ERROR: {} duplicates!'.format(len(dupes)))
    for i in dupes:
        titles = [b['title'][:30] for b in books if b['id'] == i]
        print('  {}: {}'.format(i, titles))
    exit(1)

with open(BOOKS_FILE, 'w', encoding='utf-8') as f:
    json.dump(books, f, ensure_ascii=False, indent=2)

CHAPTER_DIR = os.path.join(BASE, 'backend', 'data', 'book_chapters')
chapter_dirs = {d for d in os.listdir(CHAPTER_DIR) if os.path.isdir(os.path.join(CHAPTER_DIR, d))} if os.path.isdir(CHAPTER_DIR) else set()

# 第三遍：孤儿章节目录 → 反向匹配到书
orphan_fixed = 0
for ch_id in chapter_dirs:
    if ch_id in {b['id'] for b in books}:
        continue  # 已匹配
    meta_file = os.path.join(CHAPTER_DIR, ch_id, 'meta.json')
    if not os.path.exists(meta_file):
        continue
    with open(meta_file, 'r', encoding='utf-8') as f:
        meta = json.load(f)
    meta_title = meta.get('title', '')
    if not meta_title:
        continue

    # 找匹配的书
    for b in books:
        b_title = b['title']
        # 书名匹配（去括号、去冒号）
        b_short = b_title.split('：')[0].split(':')[0].split('（')[0].split('(')[0].strip()
        m_short = meta_title.split('：')[0].split(':')[0].split('（')[0].split('(')[0].strip()
        if b_short == m_short:
            old_id = b['id']
            if old_id != ch_id:
                old_dp = os.path.join(DETAIL_DIR, old_id + '.json')
                new_dp = os.path.join(DETAIL_DIR, ch_id + '.json')
                if os.path.exists(old_dp) and not os.path.exists(new_dp):
                    os.rename(old_dp, new_dp)
                b['id'] = ch_id
                orphan_fixed += 1
            break

fixed += orphan_fixed

# 重验证
ids = [b['id'] for b in books]
dupes = [i for i, c in Counter(ids).items() if c > 1]
if dupes:
    print('ERROR: {} duplicates!'.format(len(dupes)))
    for i in dupes:
        titles = [b['title'][:30] for b in books if b['id'] == i]
        print('  {}: {}'.format(i, titles))
    exit(1)

with open(BOOKS_FILE, 'w', encoding='utf-8') as f:
    json.dump(books, f, ensure_ascii=False, indent=2)

matched = sum(1 for b in books if b['id'] in chapter_dirs)

print('File-path fixed: {}'.format(fixed - orphan_fixed))
print('Orphan reverse-matched: {}'.format(orphan_fixed))
print('Books: {}'.format(len(books)))
print('Zero duplicates')
print('Chapter match: {}/{}'.format(matched, len(books)))
