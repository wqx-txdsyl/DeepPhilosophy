"""AI 补全缺失的星丛 relations"""
import re, json
from _lib import get_deepseek_key
from openai import OpenAI

client = OpenAI(api_key=get_deepseek_key(), base_url='https://api.deepseek.com')

with open('../app/src/pages/SchoolDetailPage.jsx', encoding='utf-8') as f:
    content = f.read()

school_names = ['CONFUCIANISM','MILITARY_SCHOOL','NEW_DEMOCRACY','OLD_DEMOCRACY',
                'POSTMODERNISM','伊壁鸠鲁学派','前苏格拉底哲学','印度哲学','犬儒学派']

for school_name in school_names:
    var = f'{school_name}_DATA'
    pat = re.compile(rf'const {re.escape(var)}\s*=\s*(\{{.*?\}};)\s*$', re.MULTILINE | re.DOTALL)
    m = pat.search(content)
    if not m:
        print(f'{school_name}: DATA NOT FOUND')
        continue
    block = m.group(1)

    thinkers_block = re.search(r'thinkers:\s*\[(.*?)\]', block, re.DOTALL)
    if not thinkers_block:
        continue
    names = re.findall(r'name:\s*"([^"]+)"', thinkers_block.group(1))
    print(f'{school_name}: {len(names)} thinkers')

    prompt = f'以下是哲学流派「{school_name}」的代表人物：\n' + '\n'.join(f'{i+1}. {n}' for i, n in enumerate(names)) + '\n\n请生成这些人物之间的思想关系（relations），每条关系指定type为以下之一：师生、继承、影响、批判、合作、学术交流。至少生成{len(names)}条关系，确保每位思想家至少有一条连线。返回纯JSON数组：\n[{{"from":"思想家A","to":"思想家B","type":"师生"}}, ...]'

    resp = client.chat.completions.create(
        model='deepseek-chat',
        messages=[{'role': 'user', 'content': prompt}],
        temperature=0.3, max_tokens=2000
    )
    text = resp.choices[0].message.content
    json_match = re.search(r'\[[\s\S]*\]', text)
    if json_match:
        relations = json.loads(json_match.group(0))
        js_rels = ',\n    '.join(
            '{from: "' + r['from'] + '", to: "' + r['to'] + '", type: "' + r.get('type', '影响') + '"}'
            for r in relations if r.get('from') and r.get('to')
        )
        new_relations = f'relations: [\n    {js_rels}\n  ],'

        old = re.search(r'relations:\s*\[.*?\]', block, re.DOTALL)
        if old:
            content = content.replace(old.group(0), new_relations)
            print(f'  -> {len(relations)} relations generated')

with open('../app/src/pages/SchoolDetailPage.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done')
