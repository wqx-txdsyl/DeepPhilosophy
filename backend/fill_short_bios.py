"""Retry remaining short bios"""
import re, os, json, time
from openai import OpenAI
import config, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from philosophers_db import PHILOSOPHERS

client = OpenAI(api_key=config.DEEPSEEK_API_KEY, base_url=config.DEEPSEEK_BASE_URL)

short = [(n,v) for n,v in PHILOSOPHERS.items() if len(v.get('bio',''))<200]
print(f'Short bios: {len(short)}')

items = [f'{j+1}. {n}' for j,(n,v) in enumerate(short)]
prompt = '为以下哲学家写200-400字思想简介:\n' + '\n'.join(items) + '\n\nJSON: [{"index":1,"bio":"..."}]'

resp = client.chat.completions.create(model=config.DEEPSEEK_MODEL,messages=[{'role':'user','content':prompt}],temperature=0.7,max_tokens=8192)
text = resp.choices[0].message.content
m = re.search(r'\[.*\]', text, re.DOTALL)
if m:
    results = json.loads(m.group(0))
    for r in results:
        idx = r['index']-1
        if 0<=idx<len(short) and 'bio' in r:
            PHILOSOPHERS[short[idx][0]]['bio'] = r['bio']
    print(f'Filled {len(results)}')

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'philosophers_db.py')
with open(db_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for name, info in PHILOSOPHERS.items():
    for i, line in enumerate(lines):
        if line.strip().startswith(f'"{name}":'):
            for j in range(i, min(i+250, len(lines))):
                if '"bio":' in lines[j]:
                    indent = len(lines[j]) - len(lines[j].lstrip())
                    val = info['bio'].replace('\\','\\\\').replace('"','\\"').replace('\n','\\n').replace('\r','')
                    lines[j] = ' ' * indent + f'"bio": "{val}",\n'
                if lines[j].strip().startswith('},'):
                    break
            break

with open(db_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

import ast
ast.parse(''.join(lines))
short2 = sum(1 for v in PHILOSOPHERS.values() if len(v.get('bio',''))<200)
print(f'Remaining: {short2}, Syntax OK')
