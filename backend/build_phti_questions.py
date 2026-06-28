"""
生成 PHTI 500题题库 —— 哲学人格测试
4维度 × 正反方向 = 8类，每类 ~63题
"""
import os, sys, json, re, csv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

DIMENSIONS = [
    {"key": "Rationalism", "label": "理性主义 vs 经验主义",
     "high": "理性主义倾向（相信逻辑、先验推理、系统思考）",
     "low": "经验主义倾向（相信感觉、具体经验、实践智慧）",
     "high_samples": "遇到问题时总是先分析逻辑而非凭直觉行动；认为一个论证的有效性比它的感染力更重要",
     "low_samples": "做决定时更相信自己的直觉和身体感受；认为再好的理论如果不能落地就是无用的"},
    {"key": "Stoicism", "label": "斯多葛 vs 伊壁鸠鲁",
     "high": "斯多葛倾向（克制、坚韧、延迟满足、控制可控的）",
     "low": "伊壁鸠鲁倾向（追求快乐、感官享受、活在当下、接纳欲望）",
     "high_samples": "感到焦虑时告诉自己'困扰人的不是事物而是对事物的看法'；愿意为了长期目标忍受当下的不适",
     "low_samples": "认为人生的意义在于体验快乐和美好；觉得过度克制和苦行是对生命的浪费"},
    {"key": "Essentialism", "label": "本质主义 vs 存在主义",
     "high": "本质主义倾向（相信有客观意义/秩序/目的，人有先天的本质）",
     "low": "存在主义倾向（认为意义是人创造的，存在先于本质）",
     "high_samples": "相信每个人都有与生俱来的使命和天性；认为世界上存在客观的道德法则",
     "low_samples": "认为人生的意义完全由自己定义；觉得'命中注定'是逃避自由的借口"},
    {"key": "Communitarian", "label": "社群主义 vs 个人主义",
     "high": "社群主义倾向（重视集体、传统、责任、归属）",
     "low": "个人主义倾向（重视个人自由、独立、自我实现）",
     "high_samples": "觉得个人的成就离不开社会的支持；愿意为家庭或社区牺牲部分个人自由",
     "low_samples": "认为个人自由高于一切集体利益；不喜欢被'我们'这个词绑架自己的想法"},
]

def main():
    api_key = config.DEEPSEEK_API_KEY
    if not api_key:
        print("错误: 未找到 DEEPSEEK_API_KEY")
        sys.exit(1)

    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=config.DEEPSEEK_BASE_URL)

    all_questions = []

    for dim in DIMENSIONS:
        print(f"\n{'='*50}")
        print(f"维度: {dim['label']}")

        for direction in ["high", "low"]:
            direction_label = dim[direction]
            target_count = 63
            print(f"  生成 {direction_label} ({target_count} 题)...")

            # 分两批生成，每批~31题
            for batch_num in range(2):
                prompt = f"""你是一个哲学人格测试的设计专家。请为以下人格维度生成{target_count // 2}道测试题。

维度：{dim['label']}
题目方向：{direction_label}
参考样例：{dim[direction + '_samples']}

每道题是一个简短的情境陈述或观点陈述（一句话，20-40字），测试者用1-5分表示同意程度。
题目应该覆盖日常生活、工作学习、人际关系、价值判断、情绪处理等多个场景。

请以JSON数组格式输出，每道题包含text字段：

```json
[
  {{"text": "题目内容"}},
  ...
]
```

只输出JSON数组，不要有其他内容。"""

                try:
                    resp = client.chat.completions.create(
                        model=config.DEEPSEEK_MODEL,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.8,
                        max_tokens=4096,
                    )
                    text = resp.choices[0].message.content
                    json_match = re.search(r'\[.*\]', text, re.DOTALL)
                    if json_match:
                        items = json.loads(json_match.group(0))
                        for item in items:
                            if isinstance(item, dict) and "text" in item:
                                all_questions.append({
                                    "text": item["text"],
                                    "dimension": dim["key"],
                                    "direction": direction,
                                })
                        print(f"    批次{batch_num+1}: 获得 {len(items)} 题")
                    else:
                        print(f"    批次{batch_num+1}: 无法解析JSON")
                except Exception as e:
                    print(f"    错误: {e}")

    print(f"\n{'='*50}")
    print(f"总计: {len(all_questions)} 题")

    # Shuffle and save
    import random
    random.shuffle(all_questions)

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'phti_questions.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_questions, f, ensure_ascii=False, indent=2)
    print(f"已保存到 {output_path}")

if __name__ == '__main__':
    main()
