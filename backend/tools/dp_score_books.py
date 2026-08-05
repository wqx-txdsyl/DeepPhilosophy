# -*- coding: utf-8 -*-
"""
dp_score_books.py — 批量书籍评分（缺 rank 补全 → book_rankings.json）
- 每本即时写盘（断点续传：中断后重跑自动跳过已有）
- DeepSeek 5 维评分 → 加权综合分（与 score_item.py 同公式）
- 重试 3 次 + 0.3s 限速
"""
import sys, io, os, json, time, urllib.request

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/
env_path = os.path.join(os.path.dirname(BASE), ".env")
if os.path.exists(env_path):
    for line in open(env_path, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
if not API_KEY:
    print("No DEEPSEEK_API_KEY")
    sys.exit(1)

BOOKS = json.load(open(os.path.join(BASE, "..", "app", "public", "books.json"), encoding="utf-8"))
RANK_FILE = os.path.join(BASE, "data", "book_rankings.json")
BACKUP = os.path.join(BASE, "data", "rank_backup.json")
DIMS = "思想深度、历史影响力、学术地位、原创性、可读性"


def load_existing():
    existing, titles = set(), set()
    if os.path.exists(RANK_FILE):
        for r in json.load(open(RANK_FILE, encoding="utf-8")):
            existing.add((r.get("title"), r.get("author")))
            titles.add(r.get("title"))
    if os.path.exists(BACKUP):
        for k, v in json.load(open(BACKUP, encoding="utf-8")).items():
            if "||" in k:
                t, a = k.split("||", 1)
                existing.add((t, a))
                titles.add(t)
            elif k.startswith("T:") and v:
                titles.add(k[2:])
    return existing, titles


def score_book(title, author, region):
    prompt = (f"你是一位哲学史教授。请对以下哲学著作按5个维度打分(1-10整数)：\n"
              f"维度：{DIMS}\n书籍：{title}（作者：{author}，{region}哲学）\n"
              f"只返回 JSON 数组，如：[8,9,7,8,6]。不要解释。")
    payload = {"model": "deepseek-chat",
               "messages": [{"role": "user", "content": prompt}],
               "temperature": 0.3, "max_tokens": 200,
               "response_format": {"type": "json_object"}}
    req = urllib.request.Request(
        "https://api.deepseek.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {API_KEY}"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        r = json.loads(resp.read().decode("utf-8"))
        content = r["choices"][0]["message"]["content"].strip()
        scores = json.loads(content)
        if isinstance(scores, dict):
            scores = list(scores.values())[0] if list(scores.values()) else []
        scores = [int(s) for s in scores[:5]]
        if len(scores) != 5 or any(s < 1 or s > 10 for s in scores):
            raise ValueError(f"bad scores: {content[:100]}")
        composite = round(scores[0] * 1.2 + scores[1] * 1.3 + scores[2] * 1.0
                          + scores[3] * 1.1 + scores[4] * 0.4, 1)
        return scores, composite


def main():
    existing, titles = load_existing()
    todo = [b for b in BOOKS
            if (b["title"], b.get("author", "")) not in existing and b["title"] not in titles]
    print(f"to score: {len(todo)}/{len(BOOKS)}", flush=True)
    done, fail = 0, 0
    for i, b in enumerate(todo):
        ok = False
        for attempt in range(3):
            try:
                scores, rank = score_book(b["title"], b.get("author", ""), b.get("region", ""))
                rankings = json.load(open(RANK_FILE, encoding="utf-8"))
                rankings.append({"title": b["title"], "author": b.get("author", ""), "rank": rank})
                json.dump(rankings, open(RANK_FILE, "w", encoding="utf-8"),
                          ensure_ascii=False, indent=2)
                print(f"  [{i+1}/{len(todo)}] {b['title']} → {rank} {scores}", flush=True)
                done += 1
                ok = True
                break
            except Exception as e:
                print(f"  [{i+1}] attempt {attempt+1}: {e}", flush=True)
                time.sleep(5 * (attempt + 1))
        if not ok:
            fail += 1
        time.sleep(0.3)
    print(f"done {done}, fail {fail}", flush=True)


if __name__ == "__main__":
    main()
