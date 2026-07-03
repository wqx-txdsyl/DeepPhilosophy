"""
Expand all philosopher bios to 1000+ chars.
Uses ast.literal_eval to parse philosophers_db.py properly.
"""
import ast, re, json, urllib.request, time, os, sys

EAST = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_gen_east.py')
API_KEY = None
if os.path.exists(EAST):
    with open(EAST, 'r', encoding='utf-8') as f:
        m = re.search(r'API_KEY\s*=\s*"([^"]+)"', f.read())
        if m: API_KEY = m.group(1)
if not API_KEY: print("ERROR: API key not found"); sys.exit(1)

DB_PATH = r"C:\Users\wqx_0\PyCharmProjects\Q&ASystem\DeepPhilosophy\backend\philosophers_db.py"

with open(DB_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

with open(DB_PATH + ".bak", 'w', encoding='utf-8') as f:
    f.write(content)

# Parse with ast
dict_start = content.find('PHILOSOPHERS = {')
dict_text = content[dict_start:]
depth = 0; end = 0
for i, c in enumerate(dict_text):
    if c == '{': depth += 1
    elif c == '}':
        depth -= 1
        if depth == 0: end = i + 1; break

dict_source = dict_text[:end]
tree = ast.parse(dict_source)
philosophers = ast.literal_eval(tree.body[0].value)

print(f"Found {len(philosophers)} philosophers")

def call_api(sp, up, mt=4000):
    d = json.dumps({"model":"deepseek-chat","messages":[{"role":"system","content":sp},{"role":"user","content":up}],"temperature":0.7,"max_tokens":mt}).encode()
    r = urllib.request.Request("https://api.deepseek.com/chat/completions", data=d,
        headers={"Authorization":f"Bearer {API_KEY}","Content-Type":"application/json"})
    with urllib.request.urlopen(r, timeout=200) as resp:
        raw = json.loads(resp.read().decode())["choices"][0]["message"]["content"]
    raw = raw.strip()
    if raw.startswith("```"): raw = re.sub(r"^```\w*\n?","",raw).rstrip("```").strip()
    return raw

SP = """你是哲学史教授。请为这位哲学家撰写1000-1200字的思想深度剖析。
结构要求：
1. 先介绍生平背景（1-2句，含生卒年）
2. 深入剖析其核心哲学思想（至少3个关键概念或理论）
3. 说明其在哲学史上的地位和对后世的影响
4. 提及其2-3部最重要的代表作
5. 语言学术性但可读性强，纯文本，不用markdown
6. 直接输出剖析正文，不要标题，不要署名"""

updated = 0
for name, info in philosophers.items():
    bio_len = len(info['bio'])
    era = info.get('era', '')
    country = info.get('country', '')
    school = info.get('school', '')

    if bio_len >= 200:
        print(f"  SKIP {name} ({bio_len} chars - already decent)")
        continue

    print(f"  Generating: {name} ({country}, {school}) [{bio_len} chars]...")

    up = f"""哲学家：{name}
年代：{era}
国家/地区：{country}
思想流派：{school}

请撰写1000-1200字的思想深度剖析。"""

    try:
        new_bio = call_api(SP, up, 4000)
        # Escape for Python string
        new_bio_escaped = new_bio.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')

        # Replace in parsed dict
        info['bio'] = new_bio
        # Update wiki_url to wikipedia
        wiki_name = name.replace(' ', '_')
        info['wiki_url'] = f"https://en.wikipedia.org/wiki/{wiki_name}"

        print(f"  OK: {len(new_bio)} chars")
        updated += 1
    except Exception as e:
        print(f"  ERROR: {str(e)[:80]}")
        continue

    time.sleep(0.3)

# Rebuild the file
print(f"\nUpdated {updated} philosophers. Rebuilding file...")

# Build new PHILOSOPHERS dict string
lines = []
lines.append('PHILOSOPHERS = {')

# Section comments
sections = {
    '西方哲学': ['柏拉图','亚里士多德','康德','黑格尔','叔本华','笛卡尔','斯宾诺莎','洛克','休谟','卢梭','海德格尔','尼采','维特根斯坦','克尔凯郭尔','萨特','加缪','马克思','恩格斯','霍布斯','密尔'],
    '东方哲学': ['孔子','老子','庄子','孟子','荀子','韩非','墨子','王阳明','朱熹','慧能','董仲舒'],
}

# Write with sections preserved
written = set()
current_section = None

# First pass: write section headers and their members
for section, members in sections.items():
    lines.append(f'    # ============================')
    lines.append(f'    # {section}')
    lines.append(f'    # ============================')
    for name in members:
        if name in philosophers:
            info = philosophers[name]
            bio = info['bio'].replace('\\', '\\\\').replace('"', '\\"')
            lines.append(f'    "{name}": {{')
            lines.append(f'        "era": "{info["era"]}",')
            lines.append(f'        "country": "{info["country"]}",')
            lines.append(f'        "school": "{info["school"]}",')
            lines.append(f'        "bio": "{bio}",')
            lines.append(f'        "wiki_url": "{info["wiki_url"]}",')
            lines.append(f'    }},')
            written.add(name)

# Second pass: remaining philosophers
remaining = {k: v for k, v in philosophers.items() if k not in written}
if remaining:
    lines.append(f'')
    lines.append(f'    # ============================')
    lines.append(f'    # 其他哲学家')
    lines.append(f'    # ============================')
    for name, info in remaining.items():
        bio = info['bio'].replace('\\', '\\\\').replace('"', '\\"')
        lines.append(f'    "{name}": {{')
        lines.append(f'        "era": "{info["era"]}",')
        lines.append(f'        "country": "{info["country"]}",')
        lines.append(f'        "school": "{info["school"]}",')
        lines.append(f'        "bio": "{bio}",')
        lines.append(f'        "wiki_url": "{info["wiki_url"]}",')
        lines.append(f'    }},')

lines.append('}')

new_dict = '\n'.join(lines)

# Replace in content
old_dict_start = content.find('PHILOSOPHERS = {')
old_dict_end = content.find('\n}', old_dict_start) + 2
# Actually find the matching }
depth = 0
for i in range(content.find('{', old_dict_start), len(content)):
    if content[i] == '{': depth += 1
    elif content[i] == '}':
        depth -= 1
        if depth == 0:
            old_dict_end = i + 1
            break

content = content[:old_dict_start] + new_dict + content[old_dict_end:]

# Keep the rest of the file (functions, aliases, etc.) intact after the dict
# Find where the new dict ends in content
new_end = content.find('\n\n', content.find('PHILOSOPHERS = {'))
# The functions/aliases after the dict should still be there

with open(DB_PATH, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"Written: {len(content)} bytes")
print("DONE!")
