"""fill_bio_prose.py — 用连贯散文格式补全bio，1000-1500字"""
import re, os, json, time, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

def main():
    from openai import OpenAI
    client = OpenAI(api_key=config.DEEPSEEK_API_KEY, base_url=config.DEEPSEEK_BASE_URL)
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'philosophers.json')

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Only update bios that are under 800 chars (clearly AI-generated short ones)
    # Keep the 1000+ prose ones (original 148)
    needs = [(n, len(v.get('bio',''))) for n,v in data.items()
             if len(v.get('bio','')) < 800 or '###' in v.get('bio','') or '**' in v.get('bio','')]
    needs.sort(key=lambda x: x[1])

    if not needs:
        print('All bios are good quality!')
        return

    total = len(needs)
    print(f'Need fix: {total}/{len(data)}')

    fixed = 0
    for i in range(0, len(needs), 2):
        batch = needs[i:i+2]
        items = '\n'.join(
            f'{j+1}. {n}（{data[n].get("era","")}，{data[n].get("country","")}，{data[n].get("school","")}）'
            for j,(n,_) in enumerate(batch)
        )

        prompt = f"""你是哲学思想史专家。请为以下哲学家撰写思想简介。

{items}

要求（非常重要）：
- 1000-1500字
- 必须是完整连贯的散文，段落流畅衔接，像一篇短文
- 绝对不要使用任何标题、分点、编号、列表符号、markdown格式
- 结构自然涵盖：生平时代、主要著作、核心哲学思想、历史地位与影响
- 学术性但不掉书袋，适合哲学爱好者阅读
- 语言平实流畅，有可读性

JSON格式（bio字段内是纯文本散文，不要任何格式标记）：
```json
[{{"index":1,"bio":"完整的散文简介..."}},{{"index":2,"bio":"完整的散文简介..."}}]
```"""

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
                        if 0 <= idx < len(batch) and r.get('bio',''):
                            bio = r['bio']
                            # Strip any markdown artifacts
                            bio = re.sub(r'^#{1,4}\s+', '', bio, flags=re.MULTILINE)
                            bio = re.sub(r'\*\*([^*]+)\*\*', r'\1', bio)
                            bio = re.sub(r'^\s*[-*]\s+', '', bio, flags=re.MULTILINE)
                            if len(bio) > len(data[batch[idx][0]].get('bio','')):
                                data[batch[idx][0]]['bio'] = bio
                                if len(bio) >= 800:
                                    fixed += 1
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    remaining = sum(1 for v in data.values() if len(v.get('bio','')) < 800 or '###' in v.get('bio',''))
                    print(f'  [{fixed}/{total}] remaining: {remaining}', flush=True)
                    break
                else:
                    print(f'  Parse retry {retry+1}', flush=True)
            except Exception as e:
                print(f'  Error retry {retry+1}: {e}', flush=True)
                time.sleep(2)
        time.sleep(0.2)

    good = sum(1 for v in data.values() if len(v.get('bio','')) >= 800 and '###' not in v.get('bio',''))
    print(f'\nDone! Good bios: {good}/{len(data)}')

if __name__ == '__main__':
    main()
