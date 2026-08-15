"""综合去重：1.括号别名 2.姓氏vs全名"""
import os, sys, json, re, io
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHIL_FILE = os.path.join(BASE, 'app', 'public', 'philosophers.json')

with open(PHIL_FILE, 'r', encoding='utf-8') as f:
    philosophers = json.load(f)

# 备份
BAK_FILE = os.path.join(BASE, 'app', 'public', 'philosophers_pre_dedup.json')
with open(BAK_FILE, 'w', encoding='utf-8') as f:
    json.dump(philosophers, f, ensure_ascii=False, indent=2)
print(f'备份: philosophers_pre_dedup.json ({len(philosophers)} 人)')

def simplify(name):
    return re.sub(r'[（(][^)）]*[)）]', '', name).replace('·', '').replace(' ', '').strip()

def split_parts(name):
    base = re.sub(r'[（(][^)）]*[)）]', '', name).strip()
    return [p.strip() for p in re.split(r'[·•\- ]', base) if p.strip() and len(p.strip()) >= 2]

total_deleted = 0

# ===== 第一轮：括号别名去重 =====
print('\n--- 第一轮：括号别名 ---')
simple_map = defaultdict(list)
for name in philosophers:
    simple_map[simplify(name)].append(name)

for simp, names in simple_map.items():
    if len(names) <= 1:
        continue

    # 保留 bio 最长的
    def bio_len(n):
        d = philosophers.get(n, {})
        return len(d.get('bio', '')) if isinstance(d, dict) else 0

    best = max(names, key=bio_len)
    others = [n for n in names if n != best]

    for old_name in others:
        old_data = philosophers.get(old_name, {})
        best_data = philosophers.get(best, {})
        if not isinstance(old_data, dict) or not isinstance(best_data, dict):
            continue

        # 合并数据
        if old_data.get('book_count', 0) > best_data.get('book_count', 0):
            best_data['book_count'] = old_data['book_count']
        if old_data.get('rank', 0) > best_data.get('rank', 0):
            best_data['rank'] = old_data['rank']
        if old_data.get('books') and not best_data.get('books'):
            best_data['books'] = old_data['books']

        del philosophers[old_name]
        total_deleted += 1
        print(f'  [{total_deleted}] 合并: {old_name} -> {best}')

# ===== 第二轮：姓氏vs全名去重 =====
print('\n--- 第二轮：短名vs全名 ---')

# 这些是人工确认的确定重复对 (short_name, full_name)
confirmed_dupes = [
    # HIGH confidence from earlier analysis
    ('列维纳斯', '伊曼纽尔·列维纳斯'),
    ('卢卡奇', '格奥尔格·卢卡奇'),
    ('恩格斯', '弗里德里希·恩格斯'),
    ('葛兰西', '安东尼奥·葛兰西'),
    ('雅斯贝尔斯', '卡尔·雅斯贝尔斯'),
    ('卡尔纳普', '鲁道夫·卡尔纳普'),
    ('斯宾塞', '赫伯特·斯宾塞'),
    ('施莱尔马赫', '弗里德里希·施莱尔马赫'),
    ('桑德尔', '迈克尔·桑德尔'),
    ('狄尔泰', '威廉·狄尔泰'),
    ('詹姆斯', '威廉·詹姆斯'),
    ('费尔巴哈', '路德维希·费尔巴哈'),
    ('费耶阿本德', '保罗·费耶阿本德'),
    ('马尔库塞', '赫伯特·马尔库塞'),
    ('布伯', '马丁·布伯'),
    ('门德尔松', '摩西·门德尔松'),
    ('迈蒙尼德', '摩西·迈蒙尼德'),
]

for short, full in confirmed_dupes:
    if short not in philosophers or full not in philosophers:
        continue

    sd = philosophers[short]
    fd = philosophers[full]
    if not isinstance(sd, dict) or not isinstance(fd, dict):
        continue

    # 保留 bio 更长的
    if len(fd.get('bio', '')) >= len(sd.get('bio', '')):
        keeper, dropper = full, short
    else:
        keeper, dropper = short, full

    if dropper not in philosophers:
        continue

    # 合并
    keeper_data = philosophers[keeper]
    dropper_data = philosophers[dropper]

    if dropper_data.get('book_count', 0) > keeper_data.get('book_count', 0):
        keeper_data['book_count'] = dropper_data['book_count']
    if dropper_data.get('rank', 0) > keeper_data.get('rank', 0):
        keeper_data['rank'] = dropper_data['rank']
    if dropper_data.get('books') and not keeper_data.get('books'):
        keeper_data['books'] = dropper_data['books']

    del philosophers[dropper]
    total_deleted += 1
    print(f'  [{total_deleted}] 合并: {dropper} -> {keeper}')

# 保存
with open(PHIL_FILE, 'w', encoding='utf-8') as f:
    json.dump(philosophers, f, ensure_ascii=False, indent=2)

print(f'\n=== 去重完成 ===')
print(f'删除: {total_deleted} 条')
print(f'剩余: {len(philosophers)} 位哲学家')
print(f'备份: philosophers_pre_dedup.json')
