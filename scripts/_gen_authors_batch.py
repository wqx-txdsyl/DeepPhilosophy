"""One-pass: generate 1000+ char bios for all philosophers via API."""
import ast, re, json, urllib.request, time, os, sys

# API key
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_gen_east.py'), 'r', encoding='utf-8') as f:
    API_KEY = re.search(r'API_KEY\s*=\s*"([^"]+)"', f.read()).group(1)

DB = r"C:\Users\wqx_0\PyCharmProjects\Q&ASystem\DeepPhilosophy\backend\philosophers_db.py"
with open(DB, 'r', encoding='utf-8') as f:
    content = f.read()

# Parse PHILOSOPHERS dict
ds = content.find('PHILOSOPHERS = {') + len('PHILOSOPHERS = ')
depth = 0; end = ds
for i in range(ds, len(content)):
    if content[i] == '{': depth += 1
    elif content[i] == '}':
        depth -= 1
        if depth == 0: end = i + 1; break
phil = ast.literal_eval(ast.parse('x = ' + content[ds:end]).body[0].value)
print(f"Found {len(phil)} philosophers")

# Filter ones needing expansion
todo = [(n, i) for n, i in phil.items() if len(i['bio']) < 200]
print(f"Need expansion: {len(todo)}")

SP = """你是哲学史教授。请为这位哲学家撰写1000-1200字的思想深度剖析。
结构：
1. 生平背景（1-2句，含生卒年）
2. 核心哲学思想（深入剖析至少3个关键概念或理论）
3. 哲学史地位和对后世的影响
4. 2-3部最重要的代表作
纯文本，不用markdown格式，直接输出剖析正文，不要标题和署名。"""

OK = 0
FAIL = 0

for name, info in todo:
    era = info.get('era',''); country = info.get('country',''); school = info.get('school','')
    print(f"\n[{OK+FAIL+1}/{len(todo)}] {name} ({country}) [{len(info['bio'])} chars]...", end=' ', flush=True)

    up = f"""哲学家：{name}
年代：{era}
国家/地区：{country}
思想流派：{school}
请撰写1000-1200字的思想深度剖析。"""

    try:
        d = json.dumps({"model":"deepseek-chat","messages":[{"role":"system","content":SP},{"role":"user","content":up}],"temperature":0.7,"max_tokens":4000}).encode()
        r = urllib.request.Request("https://api.deepseek.com/chat/completions", data=d,
            headers={"Authorization":f"Bearer {API_KEY}","Content-Type":"application/json"})
        with urllib.request.urlopen(r, timeout=120) as resp:
            raw = json.loads(resp.read().decode())["choices"][0]["message"]["content"]
        raw = raw.strip()
        if raw.startswith("```"): raw = re.sub(r"^```\w*\n?","",raw).rstrip("```").strip()

        if len(raw) >= 200:
            info['bio'] = raw
            OK += 1
            print(f"OK ({len(raw)} chars)")
        else:
            FAIL += 1
            print(f"TOO SHORT ({len(raw)} chars)")
    except Exception as e:
        FAIL += 1
        print(f"ERROR: {str(e)[:60]}")

    time.sleep(0.2)

print(f"\n\nDone: {OK} OK, {FAIL} FAIL")

# Rebuild file
lines = ['PHILOSOPHERS = {']
for name, info in phil.items():
    bio = info['bio'].replace('\\','\\\\').replace('"','\\"').replace('\n','\\n')
    lines.append(f'    "{name}": {{')
    lines.append(f'        "era": "{info["era"]}",')
    lines.append(f'        "country": "{info["country"]}",')
    lines.append(f'        "school": "{info["school"]}",')
    lines.append(f'        "bio": "{bio}",')
    lines.append(f'        "wiki_url": "{info["wiki_url"]}",')
    lines.append(f'    }},')
lines.append('}')

new_dict = '\n'.join(lines)
old_start = content.find('PHILOSOPHERS = {')
depth = 0; old_end = old_start
for i in range(content.find('{', old_start), len(content)):
    if content[i] == '{': depth += 1
    elif content[i] == '}':
        depth -= 1
        if depth == 0: old_end = i + 1; break

content = content[:old_start] + new_dict + content[old_end:]

with open(DB, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"Written: {len(content)} bytes")
