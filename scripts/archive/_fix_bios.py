"""Regenerate bios with list/markdown formatting issues"""
import json, requests, re, time, os
from _lib import get_deepseek_key

KEY = get_deepseek_key()
if not KEY: raise SystemExit("错误: 未设置 DEEPSEEK_API_KEY 环境变量")
API = "https://api.deepseek.com/v1/chat/completions"
DB = os.path.join(os.path.dirname(__file__), "..", "backend", "data", "philosophers.json")
LIST = os.path.join(os.path.dirname(__file__), "_regenerate_bios.txt")

with open(DB, "r", encoding="utf-8") as f:
    db = json.load(f)

# Only regenerate if list file exists
if not os.path.exists(LIST):
    print("No _regenerate_bios.txt found")
    exit()

with open(LIST, "r", encoding="utf-8") as f:
    bad = [l.strip() for l in f if l.strip()]

print("Regenerating " + str(len(bad)) + " bios...")
ok = fail = 0

for i, name in enumerate(bad):
    info = db.get(name, {})
    era = info.get("era", "")
    country = info.get("country", "")
    school = info.get("school", "")
    old_len = len(info.get("bio", ""))

    print("[" + str(i+1) + "/" + str(len(bad)) + "] " + name + " (" + str(old_len) + " chars)")

    prompt = "你是哲学史专家。请为哲学家《" + name + "》写一段1000字以上的生平与思想简介。\n\n"
    prompt += "必须严格按JSON格式输出（不要markdown代码块）：\n"
    prompt += '{"bio": "连贯散文，自然段落。禁止分条列点(1.2.3.)、编号、加粗(**text**)、markdown标题(##)、项目符号(- o)。流畅叙述。用\\\\n表示段落分隔。"}\n\n'
    prompt += "已知: 时代=" + era + ", 国家=" + country + ", 流派=" + school

    try:
        r = requests.post(API,
            headers={"Authorization": "Bearer " + KEY, "Content-Type": "application/json"},
            json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}],
                  "temperature": 0.7, "max_tokens": 2000},
            timeout=120)
        content = r.json()["choices"][0]["message"]["content"]
        content = re.sub(r'^```json\s*', '', content)
        content = re.sub(r'\s*```$', '', content)
        data = json.loads(content)
        bio = data.get("bio", "")
        if len(bio) > 500:
            db[name]["bio"] = bio
            ok += 1
            print("  -> " + str(len(bio)) + " chars OK")
        else:
            fail += 1
            print("  -> too short: " + str(len(bio)))
    except Exception as e:
        fail += 1
        print("  -> FAIL: " + str(e)[:80])

    if i % 5 == 0:
        with open(DB, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=2)

    time.sleep(1.5)

with open(DB, "w", encoding="utf-8") as f:
    json.dump(db, f, ensure_ascii=False, indent=2)

print("\nDone: " + str(ok) + " OK, " + str(fail) + " FAIL")
