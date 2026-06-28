"""
生成 PHTI 沙雕版题库 —— 轻松诙谐的哲学人格测试题
"""
import os, sys, json, re, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

DIMENSIONS = [
    {"key": "Rationalism", "label": "理性主义 vs 经验主义",
     "high_topics": "遇到bug先查文档再凭直觉、认为数学比诗歌更接近真理、做菜严格按照食谱绝不freestyle、吵架时列出一二三点、出门前做攻略精确到分钟",
     "low_topics": "看人第一眼就决定喜不喜欢、觉得'感觉对了'比逻辑论证重要、做菜全凭手感咸淡随缘、旅行不做攻略走到哪算哪、相信第六感"},
    {"key": "Stoicism", "label": "斯多葛 vs 伊壁鸠鲁",
     "high_topics": "被老板骂了内心毫无波动甚至有点想笑、延迟满足大师、感冒不吃药硬扛、觉得痛苦是成长的养料、对奢侈品完全无感",
     "low_topics": "今朝有酒今朝醉、双十一忍不住剁手、觉得人生苦短必须及时行乐、一顿美食能治愈一切、为什么要吃苦我又不是苦行僧"},
    {"key": "Essentialism", "label": "本质主义 vs 存在主义",
     "high_topics": "相信每个人生来就有命中注定的使命、认为世界上有绝对的对错、觉得'天生我材必有用'、相信灵魂伴侣的存在",
     "low_topics": "人生就是瞎JB过、意义是自己编的开心就好、不相信命中注定只相信自己选择、'我就是我颜色不一样的烟火'"},
    {"key": "Communitarian", "label": "社群主义 vs 个人主义",
     "high_topics": "过年回家七大姑八大姨催婚虽然烦但能理解、团建虽然尴尬但觉得有意义、为了家人可以放弃自己的梦想、朋友圈一定要分组可见",
     "low_topics": "亲戚是种负担、团建能不去就不去、结不结婚关你屁事、独居是最好的生活方式、不想被任何群体定义"},
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
        print(f"\n维度: {dim['label']}")

        for direction in ["high", "low"]:
            label = dim[direction + '_topics']
            target = 25  # 每类25题，总计200题

            print(f"  方向: {direction}, 目标 {target} 题...")

            topics_parts = label.split('、')
            topics_str = '\n'.join(f'{i+1}. {t}' for i, t in enumerate(topics_parts))

            prompt = f"""你是一个幽默的测试题设计师。请为'沙雕哲学人格测试'生成{target}道测试题。

测试维度：{dim['label']}
题目方向：{direction}（高分=同意这些说法）

参考话题：
{topics_str}

要求：
- 每题是一句俏皮的、有共鸣的生活陈述（15-30字）
- 语气轻松幽默、自嘲、网感强，像朋友间的吐槽
- 不要严肃学术，要'沙雕但又有那么一点哲学道理'
- 覆盖：吃饭、睡觉、工作、恋爱、社交、网购、追剧、朋友圈等日常场景

以JSON数组输出：
```json
[{{"text": "题目"}}, ...]
```"""

            try:
                resp = client.chat.completions.create(
                    model=config.DEEPSEEK_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.95,
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
                    print(f"    获得 {len(items)} 题")
                else:
                    print(f"    解析失败，响应前200字: {text[:200]}")
            except Exception as e:
                print(f"    错误: {e}")

    print(f"\n总计: {len(all_questions)} 题")
    random.shuffle(all_questions)

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'phti_silly_questions.json')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_questions, f, ensure_ascii=False, indent=2)
    print(f"已保存到 {output_path}")

if __name__ == '__main__':
    main()
