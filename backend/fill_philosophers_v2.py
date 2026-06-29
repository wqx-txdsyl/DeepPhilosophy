"""fill_philosophers_v2.py — 补全bio，直接写JSON"""
import re, os, json, time
from openai import OpenAI
import config

def main():
    client = OpenAI(api_key=config.DEEPSEEK_API_KEY, base_url=config.DEEPSEEK_BASE_URL)
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'philosophers.json')
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    needs = [(n, len(v.get('bio','')), not v.get('era'), not v.get('country'), not v.get('school'))
             for n,v in data.items()
             if len(v.get('bio',''))<200 or not v.get('era') or not v.get('country') or not v.get('school')]

    print(f'Need filling: {len(needs)}')
    if not needs:
        return

    BATCH = 15
    filled = 0
    for i in range(0, len(needs), BATCH):
        batch = needs[i:i+BATCH]
        items = []
        for j, (name, blen, no_era, no_country, no_school) in enumerate(batch):
            parts = [f'{j+1}. {name}']
            if no_era: parts.append('[缺年代]')
            if no_country: parts.append('[缺国家]')
            if no_school: parts.append('[缺流派]')
            if blen < 200: parts.append('[缺简介]')
            items.append(' '.join(parts))

        prompt = '为以下哲学家补全信息，JSON:\n' + '\n'.join(items) + '\n\n[{"index":1,"era":"前427-前347年","country":"古希腊","school":"古希腊哲学","bio":"200-500字思想简介..."}]'

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
                        for field in ['era','country','school','bio']:
                            if field in r and r[field]:
                                data[name][field] = r[field]
                        filled += 1
                print(f'  Batch {i//BATCH+1}/{(len(needs)+BATCH-1)//BATCH}: {len(results)}')
            else:
                print(f'  Batch {i//BATCH+1}: parse fail')
        except Exception as e:
            print(f'  Batch {i//BATCH+1}: error {e}')
        time.sleep(0.3)

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    short = sum(1 for v in data.values() if len(v.get('bio',''))<200)
    no_era = sum(1 for v in data.values() if not v.get('era'))
    no_cty = sum(1 for v in data.values() if not v.get('country'))
    no_sch = sum(1 for v in data.values() if not v.get('school'))
    print(f'Done: {filled} filled, remaining short: {short}, no_era: {no_era}, no_country: {no_cty}, no_school: {no_sch}')

if __name__ == '__main__':
    main()
