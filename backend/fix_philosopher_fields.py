"""用 DeepSeek 补全哲学家缺失字段：era/country/school/bio/wiki"""
import os, sys, json, re, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

def main():
    from openai import OpenAI
    client = OpenAI(api_key=config.DEEPSEEK_API_KEY, base_url=config.DEEPSEEK_BASE_URL)

    from philosophers_db import PHILOSOPHERS
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'philosophers_db.py')

    # Find philosophers needing updates
    needs_update = []
    for name, info in PHILOSOPHERS.items():
        missing = []
        if not info.get('era'): missing.append('era')
        if not info.get('country'): missing.append('country')
        if not info.get('school'): missing.append('school')
        if len(info.get('bio', '')) < 1000: missing.append('bio')
        wiki = info.get('wiki_url', '')
        if not wiki or 'wikipedia.org/wiki/' not in wiki: missing.append('wiki_url')
        if missing:
            needs_update.append((name, missing, info))

    print(f'需更新: {len(needs_update)} 位哲学家')

    BATCH = 10
    updated = 0
    for i in range(0, len(needs_update), BATCH):
        batch = needs_update[i:i+BATCH]
        items = []
        for j, (name, _, info) in enumerate(batch):
            existing = json.dumps({k: info.get(k, '') for k in ['era', 'country', 'school']}, ensure_ascii=False)
            items.append(f'{j+1}. {name}（现有：{existing}）')
        names_list = '\n'.join(items)

        prompt = f"""你是哲学史专家。请为以下哲学家补全缺失的信息。

{names_list}

请以JSON数组格式输出，每条包含：
- index: 序号
- era: 生卒年代（格式如"前427-前347年"或"1889-1976年"）
- country: 所属国家/地区
- school: 主要哲学流派（可多选，用/分隔，如"古希腊哲学/柏拉图学派"）
- bio: 1000-2000字的思想简介（包括主要著作、核心思想、历史影响）
- wiki_url: 英文Wikipedia链接

```json
[{{"index":1,"era":"...","country":"...","school":"...","bio":"...","wiki_url":"..."}}]
```"""

        try:
            resp = client.chat.completions.create(
                model=config.DEEPSEEK_MODEL,
                messages=[{"role": "user", "content": prompt}],
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
                        for field in ['era','country','school','bio','wiki_url']:
                            if field in r and r[field]:
                                PHILOSOPHERS[name][field] = r[field]
                        updated += 1
                print(f'  批次{i//BATCH+1}: {len(results)}位')
            else:
                print(f'  批次{i//BATCH+1}: 解析失败')
        except Exception as e:
            print(f'  批次{i//BATCH+1}: 错误 {e}')
        time.sleep(0.5)

    # Write back
    with open(db_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Find each philosopher entry and update fields
    for name, info in PHILOSOPHERS.items():
        for line_idx, line in enumerate(lines):
            if line.strip().startswith(f'"{name}":'):
                # Find the entry block
                for j in range(line_idx, min(line_idx+15, len(lines))):
                    for field in ['era', 'country', 'school', 'bio', 'wiki_url']:
                        field_pattern = f'"{field}":'
                        if field_pattern in lines[j]:
                            # Replace the line
                            indent = len(lines[j]) - len(lines[j].lstrip())
                            val = info[field].replace('\\', '\\\\').replace('"', '\\"')
                            lines[j] = ' ' * indent + f'"{field}": "{val}",\n'
                break

    with open(db_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)

    # Verify
    import ast
    ast.parse(''.join(lines))
    print(f'\nDone: {updated} philosophers updated, syntax OK')

if __name__ == '__main__':
    main()
