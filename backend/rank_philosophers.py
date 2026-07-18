"""AI 多维度评分 → 哲学家按重要性排序"""
import json, os, sys, io, time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(__file__)
PHILO_PATH = os.path.join(BASE, "..", "app", "public", "philosophers.json")

# ─── API 配置 ───
def _load_env():
    env_path = os.path.join(BASE, ".env")
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
    print("未找到 DEEPSEEK_API_KEY，请在 backend/.env 中设置")
    sys.exit(1)

philosophers_dict = json.load(open(PHILO_PATH, "r", encoding="utf-8"))
philosophers = []
for name, p in philosophers_dict.items():
    p["_name"] = name
    philosophers.append(p)

print(f"待评分: {len(philosophers)} 位哲学家")

# ─── 维度定义 ───
DIMENSIONS = [
    ("思想深度", "哲学论证的严谨性、理论体系的完整度与创新性"),
    ("历史影响力", "对后世哲学、思想、文化、政治的实际影响范围和深度"),
    ("学术地位", "在哲学史教材和学术研究中的核心程度与引用频率"),
    ("原创性", "思想的独创程度，是否开辟新领域或范式转移"),
    ("传播广度", "著作和思想在全球范围内的传播与认知度"),
]

SCORE_PROMPT = """你是一位哲学史教授。请对以下哲学家按5个维度打分(1-10整数)：

维度：
1. 思想深度 — 哲学论证的严谨性、理论体系的完整度与创新性
2. 历史影响力 — 对后世哲学、思想、文化、政治的实际影响范围和深度
3. 学术地位 — 在哲学史教材和学术研究中的核心程度与引用频率
4. 原创性 — 思想的独创程度，是否开辟新领域或范式转移
5. 传播广度 — 著作和思想在全球范围内的传播与认知度

只返回 JSON 对象，格式：{"哲学家姓名": [深度, 影响力, 学术, 原创, 传播], ...}
不要解释，不要 markdown，只返回纯 JSON。"""

BATCH_SIZE = 50

def score_batch(batch, batch_num):
    """调用 AI 对一批哲学家评分"""
    lines = []
    for p in batch:
        parts = [p["_name"]]
        if p.get("era"): parts.append(p["era"])
        if p.get("country"): parts.append(p["country"])
        if p.get("school"): parts.append(p["school"])
        lines.append(" · ".join(parts))

    book_list = "\n".join(f"- {line}" for line in lines)

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": SCORE_PROMPT},
            {"role": "user", "content": f"请为以下哲学家评分：\n\n{book_list}"},
        ],
        "temperature": 0.3,
        "max_tokens": 4096,
        "response_format": {"type": "json_object"},
    }

    import urllib.request
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
                scores = json.loads(content)
                print(f"  batch {batch_num}: scored {len(scores)} philosophers")
                return scores
        except Exception as e:
            print(f"  batch {batch_num} attempt {attempt+1} failed: {e}")
            time.sleep(5)
    return {}

# ─── 逐批评分 ───
all_scores = {}
batches = [philosophers[i:i+BATCH_SIZE] for i in range(0, len(philosophers), BATCH_SIZE)]

for bi, batch in enumerate(batches):
    print(f"\nBatch {bi+1}/{len(batches)} ({len(batch)} philosophers)...")
    scores = score_batch(batch, bi+1)
    all_scores.update(scores)
    if bi < len(batches) - 1:
        time.sleep(2)

# ─── 匹配并写入 ───
def match_score(phil):
    """模糊匹配哲学家姓名到评分"""
    name = phil["_name"]
    # 精确匹配
    if name in all_scores:
        return all_scores[name]
    # 去除括号匹配
    clean = name.split("（")[0].split("[")[0].strip()
    for k, v in all_scores.items():
        if clean in k or k in clean:
            return v
    # 英文名匹配
    for k, v in all_scores.items():
        if len(clean) < 3: continue
        if clean.lower() in k.lower() or k.lower() in clean.lower():
            return v
    return None

ranked = 0
for p in philosophers:
    s = match_score(p)
    if s and len(s) == 5:
        # 综合分 = 加权平均
        # 深度×1.2 + 影响力×1.3 + 学术×1.0 + 原创×1.1 + 传播×0.4
        composite = round(
            s[0] * 1.2 + s[1] * 1.3 + s[2] * 1.0 + s[3] * 1.1 + s[4] * 0.4,
            1
        )
        p['rank'] = composite
        p['_scores'] = s
        ranked += 1

# ─── 重新构建 dict 并保存 ───
# 先排序（同一哲学家在不同 region 里排序其实无所谓，因为前端会分 region）
new_dict = {}
for p in philosophers:
    name = p.pop("_name")
    p.pop("_scores", None)
    new_dict[name] = p

json.dump(new_dict, open(PHILO_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# ─── 输出统计 ───
print(f"\n{'='*60}")
print(f"评分完成: {ranked}/{len(philosophers)} 位")

# Top 20 by region
for region in ["东方", "西方", "世界"]:
    region_phils = [(p.get("rank", 0), p["_name"] if "_name" in p else n, p)
                    for n, p in new_dict.items() if p.get("region") == region]
    # Actually new_dict doesn't have _name anymore. Let me fix.
    region_phils = [(p.get("rank", 0), n, p) for n, p in new_dict.items() if p.get("region") == region]
    region_phils.sort(key=lambda x: x[0], reverse=True)
    print(f"\n{region} Top 20:")
    for i, (rank, name, p) in enumerate(region_phils[:20]):
        era = p.get("era", "")[:15]
        print(f"  {i+1:2d}. [{rank:4.1f}] {name[:20]}  {era}")

# 保存评分明细
detail_path = os.path.join(BASE, "data", "philosopher_rankings.json")
json.dump([{
    "name": n, "rank": p.get("rank", 0), "region": p.get("region", ""),
    "country": p.get("country", ""), "school": p.get("school", "")
} for n, p in new_dict.items()], open(detail_path, "w", encoding="utf-8"),
    ensure_ascii=False, indent=2)
print(f"\n详情: {detail_path}")
