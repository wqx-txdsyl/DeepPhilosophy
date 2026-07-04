"""
补全缺失的哲学家数据并存入 philosophers.json
"""
import json, os, re, requests, sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(SCRIPT_DIR, "..", "backend", "data", "philosophers.json")
ALIAS_FILE = os.path.join(SCRIPT_DIR, "..", "backend", "data", "name_aliases.json")
KEYS_FILE = os.path.join(SCRIPT_DIR, "api_keys.json")

# Load API keys
DEEPSEEK_KEY = ""
if os.path.exists(KEYS_FILE):
    with open(KEYS_FILE) as f:
        keys = json.load(f)
    DEEPSEEK_KEY = keys.get("deepseek", "")

# Load current DB
with open(DB_FILE, "r", encoding="utf-8") as f:
    db = json.load(f)

# Known data for authors with books (from API or common knowledge)
# era, country, school
known_meta = {
    "伯特兰·罗素": ("1872-1970", "英国", "分析哲学"),
    "勒内·笛卡尔": ("1596-1650", "法国", "理性主义"),
    "卡尔·古斯塔夫·荣格": ("1875-1961", "瑞士", "精神分析学"),
    "卡尔·马克思": ("1818-1883", "德国", "马克思主义"),
    "古斯塔夫·勒庞": ("1841-1931", "法国", "社会学"),
    "大卫·休谟": ("1711-1776", "英国", "经验主义"),
    "威拉德·范·奥曼·蒯因": ("1908-2000", "美国", "分析哲学"),
    "尤尔根·哈贝马斯": ("1929-", "德国", "法兰克福学派"),
    "巴鲁赫·斯宾诺莎": ("1632-1677", "荷兰", "理性主义"),
    "布莱兹·帕斯卡尔": ("1623-1662", "法国", "理性主义"),
    "弗朗茨·卡夫卡": ("1883-1924", "奥匈帝国(捷克)", "存在主义"),
    "弗里德里希·尼采": ("1844-1900", "德国", "生命哲学"),
    "托马斯·阿奎那": ("1225-1274", "意大利", "经院哲学"),
    "托马斯·霍布斯": ("1588-1679", "英国", "政治哲学"),
    "汉娜·阿伦特": ("1906-1975", "德国/美国", "政治哲学"),
    "汉斯-格奥尔格·伽达默尔": ("1900-2002", "德国", "哲学诠释学"),
    "理查德·罗蒂": ("1931-2007", "美国", "实用主义"),
    "瓦尔特·本雅明": ("1892-1940", "德国", "法兰克福学派"),
    "索伦·克尔凯郭尔": ("1813-1855", "丹麦", "存在主义"),
    "约翰·杜威": ("1859-1952", "美国", "实用主义"),
    "莫里斯·梅洛-庞蒂": ("1908-1961", "法国", "现象学"),
    "西格蒙德·弗洛伊德": ("1856-1939", "奥地利", "精神分析学"),
    "西蒙娜·德·波伏娃": ("1908-1986", "法国", "存在主义/女性主义"),
    "让-保罗·萨特": ("1905-1980", "法国", "存在主义"),
    "让-雅克·卢梭": ("1712-1778", "法国", "启蒙运动"),
    "费奥多尔·陀思妥耶夫斯基": ("1821-1881", "俄国", "存在主义"),
    "阿图尔·叔本华": ("1788-1860", "德国", "生命哲学"),
    "雅克·德里达": ("1930-2004", "法国", "后结构主义/解构主义"),
}

# Add entries
added, skipped = 0, 0
for name, (era, country, school) in known_meta.items():
    if name in db:
        skipped += 1
        continue
    db[name] = {
        "era": era,
        "country": country,
        "school": school,
    }
    added += 1
    print("Added: " + name + " [" + country + " " + era + "]")

print("\nAdded: " + str(added) + ", Already in DB: " + str(skipped))
print("DB total: " + str(len(db)))

with open(DB_FILE, "w", encoding="utf-8") as f:
    json.dump(db, f, ensure_ascii=False, indent=2)

print("\nNow need bios for: " + str(added) + " authors")
print("Use DeepSeek to generate? API key " + ("FOUND" if DEEPSEEK_KEY else "NOT FOUND"))

# If we have DeepSeek, generate bios in batch
if DEEPSEEK_KEY and added > 0:
    print("\n=== Generating bios with DeepSeek ===")
    for name, (era, country, school) in known_meta.items():
        if name not in db:
            continue
        if db[name].get("bio", "").strip():
            print("  SKIP (has bio): " + name)
            continue

        print("  Generating: " + name + "...")
        prompt = f"""请为哲学家"{name}"写一段1000字以上的人物介绍。必须严格按以下JSON格式输出（不要markdown代码块，只要纯JSON）：

{{
  "bio": "1000字以上的连贯人物介绍散文。自然段落，禁止分条列点/编号/加粗/标题。涵盖：生平背景、核心哲学思想、主要著作与贡献、历史影响",
  "wiki_url": "该哲学家在维基百科上的URL（如https://en.wikipedia.org/wiki/...或https://baike.baidu.com/item/...）"
}}

已知信息：
- 时代：{era}
- 国家：{country}
- 流派：{school}

全部中文输出。"""
        try:
            r = requests.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={"Authorization": "Bearer " + DEEPSEEK_KEY, "Content-Type": "application/json"},
                json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}],
                      "temperature": 0.7, "max_tokens": 2000},
                timeout=120
            )
            content = r.json()["choices"][0]["message"]["content"]
            content = re.sub(r'^```json\s*', '', content)
            content = re.sub(r'\s*```$', '', content)
            data = json.loads(content)
            db[name]["bio"] = data.get("bio", "")
            db[name]["wiki_url"] = data.get("wiki_url", "")
            print("    bio: " + str(len(db[name]["bio"])) + " chars, wiki: " + str(db[name].get("wiki_url", ""))[:60])
        except Exception as e:
            print("    FAIL: " + str(e)[:100])

        # Save incrementally
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=2)

    print("\nDone! DB saved with " + str(len(db)) + " entries.")
