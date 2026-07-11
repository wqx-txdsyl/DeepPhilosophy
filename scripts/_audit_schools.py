"""
AI 流派标签审计 + 自动修正
用 Agnes 2.0 Flash 核对每位哲人的 era+country → 推断正确 school 标签
"""
import json, requests, time, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lib import get_agnes_key

AGNES_KEY = get_agnes_key()
if not AGNES_KEY: raise SystemExit("错误: 未设置 AGNES_API_KEY 环境变量")
AGNES_API = "https://apihub.agnes-ai.com/v1/chat/completions"

DB_FILE = os.path.join(os.path.dirname(__file__), "..", "backend", "data", "philosophers.json")
KNOWN_SCHOOLS = [
    "古希腊哲学", "教父哲学", "经院哲学", "理性主义", "经验主义", "启蒙运动",
    "德国古典哲学", "马克思主义", "生命哲学", "实用主义", "精神分析学",
    "现象学", "存在主义", "分析哲学", "西方马克思主义", "法兰克福学派",
    "科学哲学", "荒诞哲学", "结构主义", "后结构主义", "后现代主义",
    "解构主义", "政治哲学", "伦理学", "女性主义", "技术哲学", "宗教哲学",
    "哲学诠释学", "自由主义", "浪漫主义", "实在论", "唯心主义", "功利主义",
    "超验主义", "实证主义", "社会学", "过程哲学", "哲学人类学",
    "唯名论", "批判理论", "社群主义", "基督教哲学",
    "儒家", "道家", "墨家", "法家", "名家", "阴阳家", "兵家",
    "两汉经学", "魏晋玄学", "隋唐佛学", "宋明理学", "明清实学", "乾嘉朴学",
    "毛泽东思想", "现代新儒家", "中国马克思主义哲学", "三民主义",
    "印度哲学", "日本哲学", "韩国哲学", "伊斯兰哲学", "阿拉伯哲学", "非洲哲学",
    "犹太哲学", "波斯哲学", "拉丁美洲哲学", "东南亚哲学",
    "斯多葛学派", "伊壁鸠鲁学派", "怀疑论", "犬儒学派", "新柏拉图主义",
]

with open(DB_FILE, "r", encoding="utf-8") as f:
    db = json.load(f)

total = len(db)
checked = ok = fixed = fail = 0

for name, info in db.items():
    checked += 1
    era = info.get("era", "")
    country = info.get("country", "")
    school = info.get("school", "")

    # Quick heuristic: if country clearly contradicts school, flag it
    # Build prompt for AI
    schools_str = ", ".join(KNOWN_SCHOOLS)
    prompt = f"""你是哲学史专家。请根据以下信息，从已知标签列表中选择最合适的流派标签。

哲学家: {name}
时代: {era}
国家/地区: {country}
当前标签: {school}

已知标签列表: {schools_str}

规则:
1. 如果当前标签已正确，返回当前标签
2. 如果标签错误，返回正确的标签（必须从已知列表中选择）
3. 德国哲学家+18-19世纪→德国古典哲学，不是古希腊哲学
4. 法国哲学家+20世纪→可能是存在主义/结构主义/后现代主义等
5. 中国哲学家→通常对应中国哲学相关标签
6. 希腊/意大利古代哲学家→古希腊哲学或罗马相关
7. 只返回标签名，不要解释

返回格式: 只输出一个标签名，如"德国古典哲学"，不要引号不要解释。"""

    try:
        r = requests.post(AGNES_API,
            headers={"Authorization": f"Bearer {AGNES_KEY}", "Content-Type": "application/json"},
            json={"model": "agnes-2.0-flash", "messages": [{"role": "user", "content": prompt}],
                  "temperature": 0.1, "max_tokens": 50},
            timeout=15)
        result = r.json()["choices"][0]["message"]["content"].strip()
        # Clean result
        result = result.replace('"', '').replace("'", "").strip()

        if result == school:
            ok += 1
        elif result in KNOWN_SCHOOLS:
            print(f"FIX: {name}  {school} -> {result}  ({era}, {country})")
            db[name]["school"] = result
            fixed += 1
        else:
            # AI returned something not in our list — keep original
            print(f"SKIP: {name}  AI suggested '{result}' (not in known list), keeping '{school}'")
            fail += 1
    except Exception as e:
        fail += 1
        if checked % 20 == 0:
            print(f"  [{checked}/{total}] ...")

    if checked % 10 == 0:
        print(f"[{checked}/{total}] ok={ok} fixed={fixed} fail={fail}")
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=2)

    time.sleep(0.15)

# Final save
with open(DB_FILE, "w", encoding="utf-8") as f:
    json.dump(db, f, ensure_ascii=False, indent=2)

print(f"\n{'='*50}")
print(f"Total: {total}, OK: {ok}, Fixed: {fixed}, Failed: {fail}")
print(f"Saved to {DB_FILE}")
