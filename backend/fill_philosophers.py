"""fill_philosophers.py — 用DeepSeek补全缺失bio/era/country/school"""
import re, os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

def main():
    from openai import OpenAI
    client = OpenAI(api_key=config.DEEPSEEK_API_KEY, base_url=config.DEEPSEEK_BASE_URL)

    from philosophers_db import PHILOSOPHERS
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'philosophers_db.py')

    # Find entries needing updates (only those with very short bio)
    needs = []
    for name, info in PHILOSOPHERS.items():
        bio_len = len(info.get('bio', ''))
        has_era = bool(info.get('era'))
        has_country = bool(info.get('country'))
        has_school = bool(info.get('school'))
        if bio_len < 200 or not has_era or not has_country or not has_school:
            needs.append((name, bio_len, not has_era, not has_country, not has_school))

    print(f'Need filling: {len(needs)} philosophers')

    BATCH = 15
    filled = 0
    for i in range(0, len(needs), BATCH):
        batch = needs[i:i+BATCH]
        items = []
        for j, (name, blen, no_era, no_country, no_school) in enumerate(batch):
            info = PHILOSOPHERS[name]
            parts = [f'{j+1}. {name}']
            if no_era: parts.append('[缺年代]')
            if no_country: parts.append('[缺国家]')
            if no_school: parts.append('[缺流派]')
            if blen < 200: parts.append('[缺简介]')
            items.append(' '.join(parts))

        prompt = f"""你是哲学史专家。为以下哲学家补全信息，JSON格式：

{chr(10).join(items)}

每条输出：
- index: 序号
- era: 生卒年（如"前427-前347年"或"1889-1951年"）
- country: 国家/地区
- school: 主要流派（多个用/分隔）
- bio: 思想简介200-500字（著作+核心思想+历史地位）

```json
[{{"index":1,"era":"...","country":"...","school":"...","bio":"..."}}]
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
                        for field in ['era','country','school','bio']:
                            if field in r and r[field]:
                                PHILOSOPHERS[name][field] = r[field]
                        filled += 1
                print(f'  Batch {i//BATCH+1}/{ (len(needs)+BATCH-1)//BATCH }: {len(results)} filled')
            else:
                print(f'  Batch {i//BATCH+1}: parse fail ({text[:100]}...)')
        except Exception as e:
            print(f'  Batch {i//BATCH+1}: error {e}')
        time.sleep(0.3)

    # Write back
    with open(db_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for name, info in PHILOSOPHERS.items():
        for i, line in enumerate(lines):
            if line.strip().startswith(f'"{name}":'):
                for j in range(i, min(i+250, len(lines))):
                    for field in ['era','country','school','bio']:
                        fkey = f'"{field}":'
                        if fkey in lines[j]:
                            indent = len(lines[j]) - len(lines[j].lstrip())
                            val = info[field].replace('\\','\\\\').replace('"','\\"').replace('\n','\\n').replace('\r','')
                            lines[j] = ' ' * indent + f'"{field}": "{val}",\n'
                    if lines[j].strip().startswith('},'):
                        break
                break

    with open(db_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    import ast
    ast.parse(''.join(lines))
    print(f'\nDone: {filled} filled, syntax OK')

if __name__ == '__main__':
    main()
