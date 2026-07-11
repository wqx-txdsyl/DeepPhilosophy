"""
补全书籍摘要 —— 对不足300字的摘要用AI扩展到300+字
"""
import os, sys, json, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

def main():
    api_key = config.DEEPSEEK_API_KEY
    if not api_key:
        print("错误: 未找到 DEEPSEEK_API_KEY")
        sys.exit(1)
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=config.DEEPSEEK_BASE_URL)

    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'book_summaries.json')
    with open(path, 'r', encoding='utf-8') as f:
        summaries = json.load(f)

    # 找出不足300字的
    shorts = []
    for key, val in summaries.items():
        s = val.get('summary', '') if isinstance(val, dict) else ''
        if len(s) < 300:
            shorts.append((key, s))

    print(f"总 {len(summaries)} 本，不足300字: {len(shorts)} 本")

    BATCH = 8
    fixed = 0
    for i in range(0, len(shorts), BATCH):
        batch = shorts[i:i+BATCH]
        books_text = "\n\n".join(
            f"【{j+1}】书名：《{k.split('||')[0]}》，作者：{k.split('||')[1] if '||' in k else '未知'}\n现有简介：{s[:200]}"
            for j, (k, s) in enumerate(batch)
        )

        prompt = f"""你是一个哲学编辑。以下是{BATCH}本哲学书籍的现有简介，每本简介不足300字。
请为每本书撰写一个300-400字的简介，要求：
- 保留原有的核心信息
- 补充该书的主要思想、历史地位、核心概念
- 语言平实流畅，适合哲学爱好者阅读
- 不要过度学术化

请以JSON格式输出：
```json
[
  {{"index": 1, "summary": "新的完整简介..."}},
  ...
]
```

书籍信息：
{books_text}"""

        try:
            resp = client.chat.completions.create(
                model=config.DEEPSEEK_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7, max_tokens=8192,
            )
            text = resp.choices[0].message.content
            import re
            json_match = re.search(r'\[.*\]', text, re.DOTALL)
            if json_match:
                results = json.loads(json_match.group(0))
                for r in results:
                    idx = r['index'] - 1
                    if 0 <= idx < len(batch):
                        key = batch[idx][0]
                        summaries[key] = {'summary': r['summary'], 'tags': summaries.get(key, {}).get('tags', []) if isinstance(summaries.get(key), dict) else []}
                        if len(r['summary']) >= 300:
                            fixed += 1
                print(f"  批次 {i//BATCH + 1}/{(len(shorts)+BATCH-1)//BATCH}: {len(results)} 本, 累计修复 {fixed}")
            else:
                print(f"  批次 {i//BATCH + 1}: JSON解析失败")
        except Exception as e:
            print(f"  批次 {i//BATCH + 1}: 错误 {e}")
        time.sleep(0.5)

    # 保存
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(summaries, f, ensure_ascii=False, indent=2)
    print(f"\n完成: {fixed}/{len(shorts)} 本补全到300+字，已保存")

if __name__ == '__main__':
    main()
