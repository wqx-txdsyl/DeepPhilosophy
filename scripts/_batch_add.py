"""
批量入库星丛哲人：AI生成信息(批量10人/次) + 数据库更新
用法: python _batch_add.py           # dry-run, 仅生成信息
     python _batch_add.py --apply   # 实际写入DB
"""
import json, os, re, sys
from _lib import PHILOSOPHERS_FILE, ALIASES_FILE, get_deepseek_key, load_json, save_json, ROOT
from _normalize_tags import normalize_philosopher, normalize_all

philo = load_json(PHILOSOPHERS_FILE)
aliases = load_json(ALIASES_FILE)

# Load unmatched list
with open(os.path.join(os.path.dirname(__file__), "_not_in_db.txt"), "r", encoding="utf-8") as f:
    targets = [l.strip() for l in f if l.strip() and not l.startswith("Total")]

print(f"Target philosophers to add: {len(targets)}")

# Skip ones already added
targets = [t for t in targets if t not in philo and t not in aliases]
print(f"Still need to add: {len(targets)}")

BATCH_SIZE = 10
api_key = get_deepseek_key()
if not api_key:
    print("ERROR: No API key found!")
    sys.exit(1)

from openai import OpenAI
client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

added = 0
batches = [targets[i:i+BATCH_SIZE] for i in range(0, len(targets), BATCH_SIZE)]

for batch_idx, batch in enumerate(batches):
    names_list = "\n".join(f"{i+1}. {n}" for i, n in enumerate(batch))
    prompt = f"""为以下哲学家生成JSON格式的信息。每条包含: era(年代), country(国家), school(流派,可多个用/分隔), bio(中文简介≥800字), wiki_url(维基百科URL)。

哲学家名单:
{names_list}

请返回纯JSON数组，格式:
[{{"name":"哲人名","era":"1889-1976","country":"德国/美国","school":"现象学/存在主义","bio":"详细介绍...(≥800中文字)","wiki_url":"https://en.wikipedia.org/wiki/..."}}, ...]

注意：
- era格式: YYYY-YYYY 或 约YYYY-YYYY年 或 YYYY-
- country: 不要括号注释，多国用/分隔
- school: 标准流派名，不要组合标签
- bio: ≥800中文字，包含生平、思想、著作、影响
- wiki_url: 优先英文Wikipedia，没有则中文Wikipedia"""

    print(f"\nBatch {batch_idx+1}/{len(batches)}: {len(batch)} philosophers")
    try:
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3, max_tokens=8000,
        )
        text = resp.choices[0].message.content

        # Extract JSON array
        json_match = re.search(r'\[[\s\S]*\]', text)
        if json_match:
            data = json.loads(json_match.group(0))
            for entry in data:
                name = entry.get("name", "")
                if not name or name in philo: continue
                info = {
                    "era": entry.get("era", ""),
                    "country": entry.get("country", ""),
                    "school": entry.get("school", ""),
                    "bio": entry.get("bio", ""),
                    "wiki_url": entry.get("wiki_url", f"https://en.wikipedia.org/wiki/{name.replace(' ', '_')}"),
                }
                if "--apply" in sys.argv:
                    philo[name] = info
                    added += 1
                    print(f"  + {name}")
                else:
                    print(f"  [DRY] {name}")
        else:
            print(f"  Failed to parse JSON from response")
            print(f"  Response[:200]: {text[:200]}")
    except Exception as e:
        print(f"  ERROR: {e}")

if "--apply" in sys.argv:
    # Auto-normalize all tags after batch add
    tag_fixes = normalize_all(philo)
    save_json(PHILOSOPHERS_FILE, philo)
    print(f"\nAdded {added} philosophers. Tag fixes: {tag_fixes}. Total: {len(philo)}")
else:
    print(f"\nDry run complete. {added} would be added. Run with --apply to save.")
