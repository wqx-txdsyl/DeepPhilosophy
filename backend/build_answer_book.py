"""
从 dailyQuotes.js 中筛选 150 条适合答案之书的金句，并生成 AI 解释
"""
import os, sys, json, re

# 确保能找到 config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

def main():
    # 1. 读取 dailyQuotes.js
    quotes_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'app', 'src', 'data', 'dailyQuotes.js'
    )
    with open(quotes_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取所有 { text: '...', author: '...' } 对象
    pattern = r"\{\s*text:\s*'([^']+)'\s*,\s*author:\s*'([^']+)'\s*\}"
    matches = re.findall(pattern, content)
    quotes = [{"text": t, "author": a} for t, a in matches]
    print(f"从 dailyQuotes.js 读取到 {len(quotes)} 条金句")

    # 2. 分批发送给 DeepSeek 筛选和生成解释
    api_key = config.DEEPSEEK_API_KEY
    if not api_key:
        print("错误: 未找到 DEEPSEEK_API_KEY")
        sys.exit(1)

    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=config.DEEPSEEK_BASE_URL)

    # 每批 80 条 → 选 18 条，分 9 批，共可得 ~162 条
    BATCH_SIZE = 80
    SELECT_PER_BATCH = 18
    batches = [quotes[i:i+BATCH_SIZE] for i in range(0, len(quotes), BATCH_SIZE)]
    print(f"分为 {len(batches)} 批，每批 {BATCH_SIZE} 条，要求选出 {SELECT_PER_BATCH} 条")

    selected = {}  # text -> {"author": ..., "explanation": ...}

    for bi, batch in enumerate(batches):
        print(f"\n--- 批次 {bi+1}/{len(batches)} ---")
        quotes_text = "\n".join(
            f"{i+1}. 「{q['text']}」—— {q['author']}"
            for i, q in enumerate(batch)
        )

        prompt = f"""你是一个哲学编辑。以下是 {len(batch)} 条哲学金句。请从中选出 {SELECT_PER_BATCH} 条最适合放在"答案之书"中的句子。

"答案之书"的功能：当人们心中有疑问时，随机抽取一条金句作为启示和解答。所以适合的句子应该：
- 能给人启发、安慰、方向或新的思考角度
- 涉及人生困惑、选择、痛苦、希望、努力、命运、爱、自我认知等普遍人生议题
- 既可以是积极励志的，也可以是冷静反思甚至略带悲观的（有时候直面现实本身就是答案）
- 避免过于学术化、纯知识性、特定历史背景的句子
- 避免极端负面/绝望的句子

请以JSON格式输出，每条包含你选中的原句序号和一段2-3句的中文解释（解释这句话如何应用于人生困惑，作为答案之书的解惑文字）：

```json
[
  {{"index": 序号, "explanation": "解释文字（2-3句，平实温暖，不说教）"}},
  ...
]
```

金句列表：
{quotes_text}"""

        try:
            resp = client.chat.completions.create(
                model=config.DEEPSEEK_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=4096,
            )
            response_text = resp.choices[0].message.content
            # 提取 JSON
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if json_match:
                results = json.loads(json_match.group(0))
                for r in results:
                    idx = r["index"] - 1  # 转为0-based
                    if 0 <= idx < len(batch):
                        q = batch[idx]
                        if q["text"] not in selected:
                            selected[q["text"]] = {
                                "author": q["author"],
                                "explanation": r["explanation"],
                            }
                print(f"  本批选出 {len(results)} 条，累计 {len(selected)} 条")
            else:
                print(f"  警告: 无法从响应中解析 JSON")
                print(f"  响应前200字: {response_text[:200]}")
        except Exception as e:
            print(f"  错误: {e}")

    print(f"\n=== 完成: 共选出 {len(selected)} 条 ===")

    # 3. 组装最终数据
    answer_book = [
        {"text": text, "author": info["author"], "explanation": info["explanation"]}
        for text, info in selected.items()
    ]

    # 4. 保存
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'answer_book.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(answer_book, f, ensure_ascii=False, indent=2)
    print(f"已保存到 {output_path}，共 {len(answer_book)} 条")

if __name__ == '__main__':
    main()
