"""AI 多维度评分 → 书籍按重要性排序"""
import json, os, sys, time

BASE = os.path.dirname(__file__)
BOOKS_PATH = os.path.join(BASE, "..", "app", "public", "books.json")

# ─── API 配置 ───
def _load_env():
    """从 backend/.env 读取配置"""
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

books = json.load(open(BOOKS_PATH, "r", encoding="utf-8"))

# 跳过特殊条目
skip_ids = {'合集&概述'}
to_score = [b for b in books if b['author'] not in skip_ids and b.get('title')]

print(f"待评分: {len(to_score)} 本")

# ─── 维度定义 ───
DIMENSIONS = [
    ("思想深度", "哲学论证的严谨性、理论体系的完整度"),
    ("历史影响力", "对后世哲学/思想/文化的实际影响"),
    ("学术地位", "在哲学史教材和学术研究中的核心程度"),
    ("原创性", "思想的独创程度，是否开辟新领域或范式"),
    ("可读性", "对普通读者的友好程度，入门价值"),
]

SCORE_PROMPT = """你是一位哲学史教授。请对以下哲学著作按5个维度打分(1-10整数)：

维度：
1. 思想深度 — 哲学论证的严谨性、理论体系的完整度
2. 历史影响力 — 对后世哲学/思想/文化的实际影响
3. 学术地位 — 在哲学史教材和学术研究中的核心程度
4. 原创性 — 思想的独创程度，是否开辟新领域或范式
5. 可读性 — 对普通读者的友好程度，入门价值

只返回 JSON 对象，格式：{"书名": [深度, 影响力, 学术, 原创, 可读], ...}
不要解释，不要 markdown，只返回纯 JSON。"""

BATCH_SIZE = 40

def score_batch(batch, batch_num):
    """调用 AI 对一批书评分"""
    book_list = "\n".join(
        f"- {b['title']}（{b['author']}） tags: {', '.join(b.get('tags', [])[:4])}"
        for b in batch
    )

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": SCORE_PROMPT},
            {"role": "user", "content": f"请为以下哲学著作评分：\n\n{book_list}"},
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
                # 清理可能的 markdown 包裹
                content = content.strip()
                if content.startswith("```"):
                    content = content.split("\n", 1)[1].rsplit("```", 1)[0]
                scores = json.loads(content)
                print(f"  batch {batch_num}: scored {len(scores)} books")
                return scores
        except Exception as e:
            print(f"  batch {batch_num} attempt {attempt+1} failed: {e}")
            time.sleep(5)
    return {}

# ─── 逐批评分 ───
all_scores = {}
batches = [to_score[i:i+BATCH_SIZE] for i in range(0, len(to_score), BATCH_SIZE)]

for bi, batch in enumerate(batches):
    print(f"\nBatch {bi+1}/{len(batches)} ({len(batch)} books)...")
    scores = score_batch(batch, bi+1)
    all_scores.update(scores)
    if bi < len(batches) - 1:
        time.sleep(2)  # rate limit

# ─── 匹配并写入 ───
def match_score(book):
    """模糊匹配书名到评分"""
    title = book['title']
    # 精确匹配
    if title in all_scores:
        return all_scores[title]
    # 去除括号匹配
    clean = title.split('（')[0].split('[')[0].strip()
    for k, v in all_scores.items():
        if clean in k or k in clean:
            return v
    return None

ranked = 0
for b in books:
    s = match_score(b)
    if s and len(s) == 5:
        # 综合分 = 加权平均（深度×1.2 + 影响力×1.3 + 学术×1.0 + 原创×1.1 + 可读×0.4）
        composite = round(
            s[0] * 1.2 + s[1] * 1.3 + s[2] * 1.0 + s[3] * 1.1 + s[4] * 0.4,
            1
        )
        b['rank'] = composite
        b['_scores'] = s  # 保留明细
        ranked += 1

# 按 rank 降序排列
books.sort(key=lambda b: b.get('rank', 0), reverse=True)

# 写入（去除 _scores 内部字段）
for b in books:
    b.pop('_scores', None)

json.dump(books, open(BOOKS_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# ─── 输出 Top 30 ───
print(f"\n{'='*60}")
print(f"评分完成: {ranked}/{len(books)} 本")
print(f"\nTop 30:")
for i, b in enumerate(books[:30]):
    r = b.get('rank', 0)
    print(f"  {i+1:2d}. [{r:4.1f}] {b['title'][:30]} — {b['author']}")

# 保存评分明细供检查
detail_path = os.path.join(BASE, "data", "book_rankings.json")
json.dump([{
    "title": b["title"], "author": b["author"], "rank": b.get("rank", 0)
} for b in books], open(detail_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"\n详情: {detail_path}")
