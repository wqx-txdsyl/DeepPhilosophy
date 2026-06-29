"""fill_bio_robust.py — 健壮的1000+ bio补全，每批保存"""
import re, os, json, time, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
from openai import OpenAI

def main():
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'philosophers.json')
    client = OpenAI(api_key=config.DEEPSEEK_API_KEY, base_url=config.DEEPSEEK_BASE_URL)

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    needs = [(n, len(v.get('bio',''))) for n,v in data.items() if len(v.get('bio','')) < 1000]
    needs.sort(key=lambda x: x[1])

    if not needs:
        print('ALL DONE - every philosopher has 1000+ bio!')
        return

    total = len(needs)
    print(f'Need: {total} philosophers')

    fixed = 0
    for i in range(0, len(needs), 3):
        batch = needs[i:i+3]
        items = '\n'.join(
            f'{j+1}. {n} ({data[n].get("era","")}, {data[n].get("country","")}, {data[n].get("school","")})'
            for j,(n,_) in enumerate(batch)
        )

        prompt = (
            f'为以下3位哲学家各撰写1000-1500字思想简介：\n{items}\n\n'
            f'要求：生平背景、主要著作、核心哲学思想、历史地位与影响。学术但不掉书袋。\n'
            f'JSON: [{{"index":1,"bio":"..."}},{{"index":2,"bio":"..."}},{{"index":3,"bio":"..."}}]'
        )

        success = False
        for retry in range(3):
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
                        if 0 <= idx < len(batch) and r.get('bio', ''):
                            if len(r['bio']) > len(data[batch[idx][0]].get('bio', '')):
                                data[batch[idx][0]]['bio'] = r['bio']
                                if len(r['bio']) >= 1000:
                                    fixed += 1
                    # Save after each batch
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    remaining = sum(1 for v in data.values() if len(v.get('bio','')) < 1000)
                    print(f'  [{fixed}/{total}] {remaining} remaining')
                    success = True
                    break
                else:
                    print(f'  Parse fail, retry {retry+1}')
            except Exception as e:
                print(f'  Error retry {retry+1}: {e}')
                time.sleep(2)
        if not success:
            print(f'  FAILED batch after 3 retries')
        time.sleep(0.3)

        # Stop early if all done
        if fixed >= total:
            break

    remaining = sum(1 for v in data.values() if len(v.get('bio','')) < 1000)
    print(f'\nDone! {len(data)-remaining}/{len(data)} have 1000+ bio')
    if remaining == 0:
        print('ALL COMPLETE!')

if __name__ == '__main__':
    main()
