"""fill_1000_bios.py — 补全所有bio到1000+字"""
import re, os, json, time
from openai import OpenAI
import config

def main():
    client = OpenAI(api_key=config.DEEPSEEK_API_KEY, base_url=config.DEEPSEEK_BASE_URL)
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'philosophers.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    needs = [(n, len(v.get('bio',''))) for n,v in data.items() if len(v.get('bio','')) < 1000]
    needs.sort(key=lambda x: x[1])  # shortest first
    print(f'Need 1000+: {len(needs)}')

    BATCH = 5  # smaller batch for longer bios
    filled = 0
    for i in range(0, len(needs), BATCH):
        batch = needs[i:i+BATCH]
        items = '\n'.join(
            f'{j+1}. {n}（era={data[n].get("era","")}，country={data[n].get("country","")}，school={data[n].get("school","")}）'
            for j,(n,_) in enumerate(batch)
        )

        prompt = f"""你是哲学史专家。请为以下{BATCH}位哲学家撰写思想简介。

{items}

要求：
- 每位1000-1500字
- 包括：生平时代背景、主要著作、核心哲学思想、历史地位与影响
- 学术性但不掉书袋，适合哲学爱好者阅读

JSON格式：
```json
[{{"index":1,"bio":"简介内容..."}},{{"index":2,"bio":"简介内容..."}}]
```"""

        try:
            resp = client.chat.completions.create(
                model=config.DEEPSEEK_MODEL,
                messages=[{"role":"user","content": prompt}],
                temperature=0.7, max_tokens=16384,
            )
            text = resp.choices[0].message.content
            m = re.search(r'\[.*\]', text, re.DOTALL)
            if m:
                results = json.loads(m.group(0))
                for r in results:
                    idx = r['index'] - 1
                    if 0 <= idx < len(batch):
                        name = batch[idx][0]
                        new_bio = r.get('bio','')
                        if len(new_bio) > len(data[name].get('bio','')):
                            data[name]['bio'] = new_bio
                        filled += 1
                print(f'  {i//BATCH+1}/{(len(needs)+BATCH-1)//BATCH}: {len(results)}')
            else:
                print(f'  {i//BATCH+1}: parse fail')
        except Exception as e:
            print(f'  {i//BATCH+1}: error {e}')
        time.sleep(0.3)

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    short = sum(1 for v in data.values() if len(v.get('bio','')) < 1000)
    print(f'Done: {filled} filled, remaining <1000: {short}')

if __name__ == '__main__':
    main()
