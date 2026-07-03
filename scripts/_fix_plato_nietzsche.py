"""Expand Plato and Nietzsche bios to 1000+ chars."""
import ast, json, urllib.request, re, os

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_gen_east.py'), 'r', encoding='utf-8') as f:
    API_KEY = re.search(r'API_KEY\s*=\s*"([^"]+)"', f.read()).group(1)

DB = r"C:\Users\wqx_0\PyCharmProjects\Q&ASystem\DeepPhilosophy\backend\philosophers_db.py"
with open(DB, 'r', encoding='utf-8') as f:
    content = f.read()

ds = content.find('PHILOSOPHERS = {') + len('PHILOSOPHERS = ')
d, i = 0, ds
for i in range(ds, len(content)):
    if content[i] == '{': d += 1
    elif content[i] == '}': d -= 1
    if d == 0: break
p = ast.literal_eval(ast.parse('x = ' + content[ds:i+1]).body[0].value)

SP = '你是哲学史教授。请为这位哲学家撰写1000-1200字的思想深度剖析。结构：生平背景、3个核心概念剖析、历史地位、2-3部代表作。用\\n表示段落分隔。纯文本，直接输出正文。'

for name in ['柏拉图', '尼采']:
    info = p[name]
    print(f"Generating: {name} ({len(info['bio'])} chars)...")
    up = f"哲学家：{name}\n年代：{info['era']}\n国家：{info['country']}\n流派：{info['school']}"

    d2 = json.dumps({"model": "deepseek-chat", "messages": [{"role": "system", "content": SP}, {"role": "user", "content": up}], "temperature": 0.7, "max_tokens": 4000}).encode()
    r = urllib.request.Request("https://api.deepseek.com/chat/completions", data=d2,
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=120) as resp:
        raw = json.loads(resp.read().decode())["choices"][0]["message"]["content"]
    raw = raw.strip()
    if raw.startswith("```"): raw = re.sub(r"^```\w*\n?", "", raw).rstrip("```").strip()

    # Escape for Python string
    safe = raw.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    info['bio'] = safe
    print(f"  OK: {len(raw)} chars")

# Rebuild
lines = ['PHILOSOPHERS = {']
for n, inf in p.items():
    lines.append(f'    "{n}": {{')
    lines.append(f'        "era": "{inf["era"]}",')
    lines.append(f'        "country": "{inf["country"]}",')
    lines.append(f'        "school": "{inf["school"]}",')
    lines.append(f'        "bio": "{inf["bio"]}",')
    lines.append(f'        "wiki_url": "{inf["wiki_url"]}",')
    lines.append(f'    }},')
lines.append('}')

new_dict = '\n'.join(lines)
old_start = content.find('PHILOSOPHERS = {')
d = 0
old_end = old_start
for i in range(content.find('{', old_start), len(content)):
    if content[i] == '{': d += 1
    elif content[i] == '}': d -= 1
    if d == 0: old_end = i + 1; break
content = content[:old_start] + new_dict + content[old_end:]

try:
    ast.parse(content)
    print("Valid Python!")
except SyntaxError as e:
    print(f"ERROR: {e}")

with open(DB, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"Written: {len(content)} bytes")
