"""根据 books.json 反向匹配哲学家著作，补全 philosophers.json 和详情 JSON 的 books 字段"""
import json, os, sys, io, re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(__file__)
PHILO_PATH = os.path.join(BASE, "..", "app", "public", "philosophers.json")
BOOKS_PATH = os.path.join(BASE, "..", "app", "public", "books.json")
DETAIL_DIR = os.path.join(BASE, "..", "app", "public", "philosopher", "data")

philosophers = json.load(open(PHILO_PATH, "r", encoding="utf-8"))
books = json.load(open(BOOKS_PATH, "r", encoding="utf-8"))

# ─── 清理作者名用于匹配 ───
def clean_name(s):
    """去除括号、空格、英文名等"""
    s = s.strip()
    # 去掉英文名/罗马拼音 "(Plato)" 等
    s = re.sub(r'\s*[（(][^)）]*[)）]\s*', '', s)
    # 去掉 "/" 合著分隔（取第一个）
    if '/' in s:
        s = s.split('/')[0].strip()
    return s

# ─── 为每个哲学家匹配著作 ───
matched = 0
total_books_linked = 0

for philo_name, p in philosophers.items():
    philo_books = []
    clean_philo = clean_name(philo_name)

    for b in books:
        author_str = b.get('author', '')
        if not author_str or author_str == '合集&概述':
            continue

        # 检查作者字符串中是否包含哲学家名
        # 处理合著：author = "卡尔·马克思 / 弗里德里希·恩格斯"
        authors = [a.strip() for a in author_str.split('/')]
        for a in authors:
            clean_a = clean_name(a)
            # 精确匹配或包含匹配
            if clean_philo == clean_a or clean_philo in clean_a or clean_a in clean_philo:
                philo_books.append({
                    'title': b['title'],
                    'id': b['id'],
                    'file_type': b.get('file_type', 'epub'),
                })
                break

    if philo_books:
        p['books'] = philo_books
        p['book_count'] = len(philo_books)
        matched += 1
        total_books_linked += len(philo_books)
    else:
        p['books'] = []
        p['book_count'] = 0

# ─── 保存 philosophers.json ───
# 保持 rank 降序
items = sorted(philosophers.items(), key=lambda x: x[1].get('rank', 0), reverse=True)
philosophers = dict(items)
json.dump(philosophers, open(PHILO_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"philosophers.json: {matched}/{len(philosophers)} 位匹配到著作, 共 {total_books_linked} 本")

# ─── 更新详情 JSON ───
detail_updated = 0
for fname in os.listdir(DETAIL_DIR):
    if not fname.endswith('.json'):
        continue
    fpath = os.path.join(DETAIL_DIR, fname)
    try:
        detail = json.load(open(fpath, "r", encoding="utf-8"))
    except:
        continue

    name = detail.get('name', fname.replace('.json', ''))
    if name in philosophers:
        p = philosophers[name]
        detail['books'] = p.get('books', [])
        detail['book_count'] = p.get('book_count', 0)
        detail['region'] = p.get('region', detail.get('region', ''))
        detail['rank'] = p.get('rank', 0)
        json.dump(detail, open(fpath, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        detail_updated += 1

print(f"详情 JSON: {detail_updated} 个已更新")

# ─── 展示几个例子 ───
for name in ['柏拉图', '亚里士多德', '孔子', '老子', '康德']:
    p = philosophers.get(name, {})
    print(f"\n{name}: {p.get('book_count', 0)} 本")
    for b in (p.get('books') or [])[:3]:
        print(f"  - {b['title']} ({b['file_type']})")
