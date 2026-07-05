"""Simplify long relation labels to short type keywords via DeepSeek"""
import re, json
from _lib import get_deepseek_key
from openai import OpenAI

client = OpenAI(api_key=get_deepseek_key(), base_url='https://api.deepseek.com')

with open('../app/src/pages/SchoolDetailPage.jsx', encoding='utf-8') as f:
    c = f.read()

# Find both label: and type: values
all_types = re.findall(r'(?:label|type):\s*"([^"]+)"', c)
long_types = list(set(t for t in all_types if len(t) > 10))
print(f'Long types/labels: {len(long_types)}')

if long_types:
    prompt = '将以下哲学思想关系归类为以下类型之一：师生、继承、影响、批判、合作、学术交流。返回JSON：{"原始描述":"简化类型"}\n\n' + '\n'.join(f'{i+1}. {t}' for i, t in enumerate(long_types[:50]))
    resp = client.chat.completions.create(
        model='deepseek-chat',
        messages=[{'role': 'user', 'content': prompt}],
        temperature=0.1, max_tokens=2000
    )
    text = resp.choices[0].message.content
    m = re.search(r'\{[\s\S]*\}', text)
    if m:
        mapping = json.loads(m.group(0))
        fixed = 0
        valid = {'师生', '继承', '影响', '批判', '合作', '学术交流'}
        for old, new in mapping.items():
            if old in c and new in valid:
                c = c.replace(f'label: "{old}"', f'type: "{new}"')
                c = c.replace(f'type: "{old}"', f'type: "{new}"')
                fixed += 1
                print(f'  {old[:40]} -> {new}')
        print(f'Fixed: {fixed}')

        with open('../app/src/pages/SchoolDetailPage.jsx', 'w', encoding='utf-8') as f:
            f.write(c)
        print('Saved')
    else:
        print(f'No JSON found in: {text[:200]}')
