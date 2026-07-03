"""Fix unescaped newlines in philosopher bios."""
import ast

DB = r"C:\Users\wqx_0\PyCharmProjects\Q&ASystem\DeepPhilosophy\backend\philosophers_db.py"

with open(DB, 'r', encoding='utf-8') as f:
    content = f.read()

# Parse
ds = content.find('PHILOSOPHERS = {') + len('PHILOSOPHERS = ')
d, i = 0, ds
for i in range(ds, len(content)):
    if content[i] == '{': d += 1
    elif content[i] == '}':
        d -= 1
        if d == 0: break
phil = ast.literal_eval(ast.parse('x = ' + content[ds:i+1]).body[0].value)

print(f"Fixing {len(phil)} philosophers...")

# Fix: properly escape newlines in bio strings
fixed = 0
for name, info in phil.items():
    bio = info['bio']
    # Replace \ with \\, " with \", and actual newlines with \n
    bio = bio.replace('\\', '\\\\')
    bio = bio.replace('"', '\\"')
    bio = bio.replace('\n', '\\n')
    info['bio'] = bio
    if '\\n' in bio:
        fixed += 1

print(f"Fixed {fixed} bios with newlines")

# Rebuild
lines = ['PHILOSOPHERS = {']
for name, info in phil.items():
    lines.append(f'    "{name}": {{')
    lines.append(f'        "era": "{info["era"]}",')
    lines.append(f'        "country": "{info["country"]}",')
    lines.append(f'        "school": "{info["school"]}",')
    lines.append(f'        "bio": "{info["bio"]}",')
    lines.append(f'        "wiki_url": "{info["wiki_url"]}",')
    lines.append(f'    }},')
lines.append('}')

new_dict = '\n'.join(lines)
old_start = content.find('PHILOSOPHERS = {')
d = 0
old_end = old_start
for i in range(content.find('{', old_start), len(content)):
    if content[i] == '{': d += 1
    elif content[i] == '}':
        d -= 1
        if d == 0:
            old_end = i + 1
            break

content = content[:old_start] + new_dict + content[old_end:]

# Verify
try:
    ast.parse(content)
    print("File is valid Python! ✓")
except SyntaxError as e:
    print(f"ERROR: {e}")

with open(DB, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"Written: {len(content)} bytes")
