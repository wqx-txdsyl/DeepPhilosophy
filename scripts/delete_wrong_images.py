"""删除所有已确认错图：AI 49 个 + L1-L4 已修复的"""
import json, os, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(BASE, 'app', 'public', 'philosopher')
PHIL_FILE = os.path.join(BASE, 'app', 'public', 'philosophers.json')
PROGRESS_FILE = os.path.join(BASE, 'scripts', '_ai_batch_progress.json')

with open(PHIL_FILE, 'r', encoding='utf-8') as f:
    philosophers = json.load(f)

# 收集所有确认错图
to_delete = set()

# 1. AI 验证确认的 49 个
if os.path.exists(PROGRESS_FILE):
    with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
        prog = json.load(f)
    for m in prog.get('mismatches', []):
        to_delete.add(m['name'])

# 2. L1-L4 之前确认的（L2坏图 + L4 AI确认的5个——可能已有重叠）
l1l4_wrong = {
    '道元', '泰勒', '帕卡尔大帝', '阿马菲乌斯', '阿达帕',
    '霍尔姆斯·罗尔斯顿三世', '帕特里夏·丘奇兰德', 'Enrique Dussel',
    '摩西', '仁钦·乔玛', '卡蒂尼', '维雷杜·维雷杜', '瓦曼·波马·德·阿亚拉',
    # L3 duplicates (images shared with wrong person) — already deleted in earlier cleanup
}
to_delete.update(l1l4_wrong)

def safe_fn(name):
    return name.replace('/', '-').replace('\\', '-').replace(':', '-')

# 删除
deleted = 0
not_found = []
for name in sorted(to_delete):
    if name not in philosophers:
        continue
    fn = safe_fn(name)
    found = False
    for ext in ['.jpg', '.png', '.webp']:
        fp = os.path.join(IMG_DIR, fn + ext)
        if os.path.exists(fp):
            os.remove(fp)
            print(f'[DEL] {fn}{ext}')
            deleted += 1
            found = True
    if not found:
        not_found.append(name)

# 统计
missing = 0
for name in philosophers:
    fn = safe_fn(name)
    has = any(os.path.exists(os.path.join(IMG_DIR, fn + e)) for e in ['.jpg', '.png', '.webp'])
    if not has:
        missing += 1

remaining = len([f for f in os.listdir(IMG_DIR) if f.endswith(('.jpg', '.png', '.webp'))])

print(f'\n=== 清理结果 ===')
print(f'删除: {deleted}')
print(f'未找到(已删过): {len(not_found)}')
print(f'缺图: {missing}/{len(philosophers)}')
print(f'剩余图片: {remaining}')
