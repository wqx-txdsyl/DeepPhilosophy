"""AI 补全星丛 relations — v2: 支持 backtick 字符串和嵌套 JSON"""
import re, json
from _lib import get_deepseek_key
from openai import OpenAI

client = OpenAI(api_key=get_deepseek_key(), base_url='https://api.deepseek.com')

with open('../app/src/pages/SchoolDetailPage.jsx', encoding='utf-8') as f:
    c = f.read()

# Find ALL DATA blocks and count relations
blocks = re.findall(r'const (\w+_DATA)\s*=', c)
all_vars = [b for b in blocks]

for var in all_vars:
    idx = c.find(f'const {var} =')
    if idx < 0: continue

    # Find relations block
    rel_start = c.find('relations:', idx)
    if rel_start < 0: continue
    rel_end = c.find('],', rel_start)
    rel_block = c[rel_start:rel_end+2]
    rel_count = len(re.findall(r'from:', rel_block))

    if rel_count >= 3: continue  # Already has enough

    # Extract thinkers: everything between const and relations
    section = c[idx:rel_start]
    # Match double-quoted AND backtick names
    names_dq = re.findall(r'name:\s*"([^"]+)"', section)
    names_bt = re.findall(r'name:\s*`([^`]+)`', section)
    names = names_dq + names_bt
    # Deduplicate
    seen = set()
    thinkers = []
    for n in names:
        if n not in seen:
            seen.add(n)
            thinkers.append(n)

    sn = var.replace('_DATA', '')
    print(f'{sn}: {len(thinkers)} thinkers, {rel_count} relations')

    if len(thinkers) < 3: continue

    prompt = f'为哲学流派「{sn}」的代表人物生成思想关系，type为以下之一：师生、继承、影响、批判、合作、学术交流。确保每人至少一条连线。返回纯JSON数组。\n\n' + '\n'.join(f'{i+1}. {n}' for i, n in enumerate(thinkers)) + '\n\n[{"from":"A","to":"B","type":"师生"}, ...]'

    try:
        resp = client.chat.completions.create(
            model='deepseek-chat',
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.3, max_tokens=2000
        )
        text = resp.choices[0].message.content
        m = re.search(r'\[[\s\S]*\]', text)
        if m:
            rels = json.loads(m.group(0))
            js = ',\n    '.join(
                '{from: "' + r['from'] + '", to: "' + r['to'] + '", type: "' + r.get('type', '影响') + '"}'
                for r in rels if r.get('from') and r.get('to')
            )
            new = f'relations: [\n    {js}\n  ],'
            c = c.replace(rel_block, new)
            print(f'  -> {len(rels)} relations')
    except Exception as e:
        print(f'  ERROR: {e}')

with open('../app/src/pages/SchoolDetailPage.jsx', 'w', encoding='utf-8') as f:
    f.write(c)
print('Done')
