"""构建哲学家星丛网络 — AI 识别真实思想关系（师承/论敌/影响/友谊）"""
import json, os, sys, io, time, urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHILO_PATH = os.path.join(BASE, "..", "app", "public", "philosophers.json")
OUT_PATH = os.path.join(BASE, "..", "app", "public", "philosopher_network.json")

# ─── API 配置 ───
def _load_env():
    env_path = os.path.join(os.path.dirname(BASE), ".env")
    if os.path.exists(env_path):
        for line in open(env_path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

_load_env()
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
API_URL = os.environ.get("DP_API_URL", "https://api.deepseek.com").rstrip("/")
if not API_KEY:
    print("未找到 DEEPSEEK_API_KEY")
    sys.exit(1)

philosophers_dict = json.load(open(PHILO_PATH, "r", encoding="utf-8"))

# 提取哲学家列表，按 rank 排序
all_philosophers = []
for name, p in philosophers_dict.items():
    all_philosophers.append({
        'name': name,
        'region': p.get('region', ''),
        'era': p.get('era', ''),
        'country': p.get('country', ''),
        'school': p.get('school', ''),
        'rank': p.get('rank', 0),
    })

all_philosophers.sort(key=lambda x: x['rank'], reverse=True)

# 只对 top 哲学家做 AI 查询（rank 前 120 + 每个领域前 40）
top_global = [p for p in all_philosophers if p['rank'] > 0][:120]
# 补充：每个区域的前 40
for region in ['东方', '西方', '世界']:
    region_top = [p for p in all_philosophers if p['region'] == region and p['rank'] > 0][:40]
    for p in region_top:
        if p not in top_global:
            top_global.append(p)

# 去重
seen = set()
query_list = []
for p in top_global:
    if p['name'] not in seen:
        seen.add(p['name'])
        query_list.append(p)

print(f"待查询哲学家: {len(query_list)} 位")

# 已知哲学家名单（供 AI 引用）
ALL_NAMES = [p['name'] for p in all_philosophers if p['rank'] > 0]
NAME_LIST_STR = "\n".join(f"- {n}" for n in sorted(ALL_NAMES))

RELATION_PROMPT = """你是一位哲学史教授。下面是一份哲学家名单。请为指定的哲学家找出他们真实的思想关系。

关系类型：
- 师承：老师→学生（单向）
- 影响：A影响了B的思想（单向）
- 论敌：两人有直接的思想争论或对立（双向）
- 友/合作：两人有友谊或思想合作（双向）

请只返回 JSON 对象。格式：
{"哲学家A": [{"name":"哲学家B","rel":"师承","role":"学生","note":"简述"}, ...], "哲学家B": [...], ...}

规则：
1. 只使用名单中的哲学家姓名（精确匹配）
2. 每人列出 3-8 个最重要的关系
3. 优先著名的、有明确历史记载的关系
4. 不要编造关系，不确定的不要写
5. 只返回 JSON，不要 markdown，不要解释"""

BATCH_SIZE = 8  # 每次查询 8 位哲学家的关系

def query_relations(batch, batch_num):
    """查询一批哲学家的关系"""
    target_names = [p['name'] for p in batch]
    targets_str = "\n".join(
        f"- {p['name']}（{p.get('era','')} · {p.get('country','')} · {p.get('school','')}）"
        for p in batch
    )

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": RELATION_PROMPT},
            {"role": "user", "content": f"哲学家名单：\n{NAME_LIST_STR}\n\n请为以下哲学家找出思想关系：\n{targets_str}"},
        ],
        "temperature": 0.3,
        "max_tokens": 4096,
        "response_format": {"type": "json_object"},
    }

    req = urllib.request.Request(
        f"{API_URL}/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
        },
    )

    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                content = result["choices"][0]["message"]["content"]
                content = content.strip()
                if content.startswith("```"):
                    content = content.split("\n", 1)[1].rsplit("```", 1)[0]
                relations = json.loads(content)
                total = sum(len(v) for v in relations.values())
                print(f"  batch {batch_num}: {len(relations)} philosophers, {total} relations")
                return relations
        except Exception as e:
            print(f"  batch {batch_num} attempt {attempt+1} failed: {e}")
            time.sleep(5)
    return {}

# ─── 逐批查询 ───
all_relations = {}
batches = [query_list[i:i+BATCH_SIZE] for i in range(0, len(query_list), BATCH_SIZE)]

for bi, batch in enumerate(batches):
    print(f"\nBatch {bi+1}/{len(batches)} ({len(batch)} philosophers)...")
    relations = query_relations(batch, bi+1)
    # 合并结果
    for name, rels in relations.items():
        if name not in all_relations:
            all_relations[name] = []
        for r in rels:
            if r not in all_relations[name]:
                all_relations[name].append(r)
    if bi < len(batches) - 1:
        time.sleep(1.5)

print(f"\n共获得 {len(all_relations)} 位哲学家的关系数据")

# ─── 构建网络 ───
# 关系权重映射
REL_WEIGHTS = {
    '师承': 5,
    '影响': 4,
    '论敌': 3,
    '友/合作': 3,
    '友': 3,
    '合作': 3,
}

network = {}
# 初始化所有哲学家
for p in all_philosophers:
    network[p['name']] = {
        'rank': p['rank'],
        'region': p['region'],
        'is_hot': p['rank'] >= 32.9,
        'connections': [],
    }

# 填充 AI 关系
direct_count = 0
inferred = {}  # 反向推断的关系

for name, rels in all_relations.items():
    if name not in network:
        continue

    for r in rels:
        target = r.get('name', '')
        rel_type = r.get('rel', '')
        role = r.get('role', '')
        note = r.get('note', '')

        if target not in network:
            continue

        weight = REL_WEIGHTS.get(rel_type, 2)

        # 正向关系
        network[name]['connections'].append({
            'name': target,
            'score': weight,
            'type': rel_type,
            'role': role,
            'note': note,
            'region': network[target]['region'],
            'rank': network[target]['rank'],
        })
        direct_count += 1

        # 推断反向关系
        reverse_type = {
            '师承': '影响' if role == '老师' else '师承',
            '影响': '影响',
            '论敌': '论敌',
            '友/合作': '友/合作',
        }.get(rel_type, rel_type)

        if target not in inferred:
            inferred[target] = []
        inferred[target].append({
            'name': name,
            'score': weight,
            'type': reverse_type,
            'role': '学生' if (rel_type == '师承' and role == '老师') else '',
            'note': note,
            'region': network[name]['region'],
            'rank': network[name]['rank'],
        })

# 合并反向推断关系
for name, rels in inferred.items():
    if name not in network:
        continue
    existing_names = {c['name'] for c in network[name]['connections']}
    for r in rels:
        if r['name'] not in existing_names:
            network[name]['connections'].append(r)
            existing_names.add(r['name'])

# 去重、排序、限制数量
for name in network:
    # 去重（保留 score 最高的）
    best = {}
    for c in network[name]['connections']:
        target = c['name']
        if target not in best or c['score'] > best[target]['score']:
            best[target] = c
    conns = sorted(best.values(), key=lambda c: c['score'], reverse=True)
    # 最多保留 15 个连接
    network[name]['connections'] = conns[:15]

# ─── 统计 ───
conn_counts = [len(v['connections']) for v in network.values()]
avg_conn = sum(conn_counts) / len(conn_counts) if conn_counts else 0
hot_conn_counts = [len(v['connections']) for v in network.values() if v['is_hot']]
hot_avg = sum(hot_conn_counts) / len(hot_conn_counts) if hot_conn_counts else 0
with_conn = sum(1 for c in conn_counts if c > 0)

print(f"\n网络统计:")
print(f"  总节点: {len(network)}")
print(f"  有关系的: {with_conn}")
print(f"  AI 直接关系: {direct_count}")
print(f"  反向推断: {sum(len(v) for v in inferred.values())}")
print(f"  平均连接: {avg_conn:.1f} (大热: {hot_avg:.1f})")

# 展示几个例子
for name in sorted(network, key=lambda n: network[n]['rank'], reverse=True)[:5]:
    v = network[name]
    print(f"\n{name} (rank={v['rank']}): {len(v['connections'])} 条关系")
    for c in v['connections'][:6]:
        print(f"  [{c['type']}] → {c['name']} {c.get('note','')}")

json.dump(network, open(OUT_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"\n输出: {OUT_PATH}")
print(f"文件大小: {os.path.getsize(OUT_PATH)/1024:.0f} KB")
