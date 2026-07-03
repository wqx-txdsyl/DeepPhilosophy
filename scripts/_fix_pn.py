"""Fix Plato/Nietzsche bios with direct string replacement."""
import json, urllib.request, re, os, ast

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_gen_east.py'), 'r', encoding='utf-8') as f:
    API_KEY = re.search(r'API_KEY\s*=\s*"([^"]+)"', f.read()).group(1)

DB = r"C:\Users\wqx_0\PyCharmProjects\Q&ASystem\DeepPhilosophy\backend\philosophers_db.py"
with open(DB, 'r', encoding='utf-8') as f:
    c = f.read()

SP = "你是哲学史教授。撰写1000-1200字思想深度剖析。不要使用换行符，一整段连续输出。纯文本，直接输出正文。"

for name in ["柏拉图", "尼采"]:
    bio_start = c.find(f'"{name}":')
    if bio_start < 0:
        print(f"{name}: NOT FOUND")
        continue

    # Find bio field
    bio_field_start = c.find('"bio": "', bio_start)
    bio_field_end = c.find('"', bio_field_start + 8)
    old_bio_field = c[bio_field_start:bio_field_end+1]
    print(f"{name}: old bio = {len(old_bio_field)} chars")

    # Get context for prompting
    ctx = c[bio_start:bio_start+600]
    era_m = re.search(r'"era": "([^"]+)"', ctx)
    country_m = re.search(r'"country": "([^"]+)"', ctx)
    school_m = re.search(r'"school": "([^"]+)"', ctx)
    era = era_m.group(1) if era_m else ""
    country = country_m.group(1) if country_m else ""
    school = school_m.group(1) if school_m else ""

    up = f"{name}，{era}，{country}，{school}"
    d = json.dumps({"model": "deepseek-chat", "messages": [{"role": "system", "content": SP}, {"role": "user", "content": up}], "temperature": 0.7, "max_tokens": 4000}).encode()
    r = urllib.request.Request("https://api.deepseek.com/chat/completions", data=d,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=120) as resp:
        raw = json.loads(resp.read().decode())["choices"][0]["message"]["content"]
    raw = raw.strip()
    if raw.startswith("```"): raw = re.sub(r"^```\w*\n?", "", raw).rstrip("```").strip()

    # Escape for Python string - replace actual newlines with spaces
    safe = raw.replace("\\", "\\\\").replace('"', '\\"')
    # Replace all whitespace sequences with single space to avoid newline issues
    safe = " ".join(safe.split())

    new_bio_field = f'"bio": "{safe}"'
    c = c.replace(old_bio_field, new_bio_field)
    print(f"  New bio: {len(safe)} chars")

try:
    ast.parse(c)
    print("Valid Python!")
except SyntaxError as e:
    print(f"ERROR: {e}")

with open(DB, 'w', encoding='utf-8') as f:
    f.write(c)
print(f"Written: {len(c)} bytes")
