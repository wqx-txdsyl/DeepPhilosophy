"""清理哲学家数据库：去重 + 去除非人格条目"""
import json, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE = os.path.dirname(__file__)
PHILO_PATH = os.path.join(BASE, "..", "app", "public", "philosophers.json")
NETWORK_PATH = os.path.join(BASE, "..", "app", "public", "philosopher_network.json")
DETAIL_DIR = os.path.join(BASE, "..", "app", "public", "philosopher", "data")

REMOVE = [
    # 思想阶段分身 → 保留主条目
    '早期维特根斯坦', '后期维特根斯坦',   # → 路德维希·维特根斯坦
    '福柯（后期）',                       # → 米歇尔·福柯
    '巴特(后期)', '巴特',                 # → 罗兰·巴特
    '梅洛-庞蒂（东欧影响）',               # → 莫里斯·梅洛-庞蒂
    # 同名异译重复
    '伊本·西那（Avicenna）', '伊本·西那（阿维森纳）',  # → 伊本·西那
    '法拉比（Al-Farabi）',                # → 法拉比
    '传道者（柯希勒特）',                  # → 传道者
    '伪狄奥尼修斯（托名）',                # → 伪狄奥尼修斯
    # 非人格条目
    '后期墨家',                           # 学派，非个人
    '双胞胎英雄（胡纳赫普与斯巴兰克）',     # 神话双人组
    '奥梅特奥特尔（神格化概念）',           # 神格概念
    '奇兰·巴兰（复数先知）',               # 复数先知
    '占星家与祭司群体',                    # 群体
]

# 1. philosophers.json
d = json.load(open(PHILO_PATH, 'r', encoding='utf-8'))
removed = [n for n in REMOVE if n in d]
for n in removed:
    del d[n]
items = sorted(d.items(), key=lambda x: x[1].get('rank', 0), reverse=True)
json.dump(dict(items), open(PHILO_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(f'philosophers.json: {len(d)} remaining (removed {len(removed)})')

# 2. philosopher_network.json
net = json.load(open(NETWORK_PATH, 'r', encoding='utf-8'))
for n in REMOVE:
    if n in net:
        del net[n]
for n in net:
    net[n]['connections'] = [c for c in net[n]['connections'] if c['name'] not in REMOVE]
json.dump(net, open(NETWORK_PATH, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(f'philosopher_network.json: {len(net)} nodes')

# 3. Detail JSONs
cnt = 0
for f in os.listdir(DETAIL_DIR):
    if f.endswith('.json') and f.replace('.json', '') in REMOVE:
        os.remove(os.path.join(DETAIL_DIR, f))
        cnt += 1
print(f'Detail JSONs deleted: {cnt}')

print('\nRemoved entries:')
for n in removed:
    print(f'  ✕ {n}')
