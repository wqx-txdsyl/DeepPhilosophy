"""fill_1000_v2.py — 增量补全bio到1000+，每批保存"""
import re, os, json, time
from openai import OpenAI
import config

json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'philosophers.json')
client = OpenAI(api_key=config.DEEPSEEK_API_KEY, base_url=config.DEEPSEEK_BASE_URL)

while True:
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    needs = [(n, len(v.get('bio',''))) for n,v in data.items() if len(v.get('bio','')) < 1000]
    if not needs:
        print('ALL DONE!')
        break
    needs.sort(key=lambda x: x[1])
    print(f'Remaining: {len(needs)}, taking 4 shortest...')

    batch = needs[:4]
    items = '\n'.join(
        f'{j+1}. {n}（{data[n].get("era","")}，{data[n].get("country","")}，{data[n].get("school","")}）'
        for j,(n,_) in enumerate(batch)
    )
    prompt = f'为以下哲学家撰写1000-1500字思想简介（生平+著作+核心思想+历史影响）:\n{items}\n\nJSON: [{{"index":1,"bio":"..."}},{{"index":2,"bio":"..."}}]'

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
                if 0 <= idx < len(batch) and r.get('bio',''):
                    if len(r['bio']) > len(data[batch[idx][0]].get('bio','')):
                        data[batch[idx][0]]['bio'] = r['bio']
            # Save after each batch
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            new_short = sum(1 for v in data.values() if len(v.get('bio','')) < 1000)
            print(f'  Batch OK, remaining: {new_short}')
        else:
            print(f'  Parse fail: {text[:80]}...')
    except Exception as e:
        print(f'  Error: {e}')
    time.sleep(0.3)
