"""终极bio填充——1500-2000字纯散文，无格式标记"""
import re, os, json, time, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'philosophers.json')

def main():
    from openai import OpenAI
    client = OpenAI(api_key=config.DEEPSEEK_API_KEY, base_url=config.DEEPSEEK_BASE_URL)

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Load bad list
    bad_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'bad_bios.json')
    with open(bad_path, 'r', encoding='utf-8') as f:
        bad_names = set(json.load(f))

    # Build batch list from bad names
    needs = [(n, len(data.get(n, {}).get('bio', ''))) for n in bad_names if n in data]
    needs.sort(key=lambda x: x[1])

    if not needs:
        print('No bad bios to fix!')
        return

    total = len(needs)
    print(f'Fixing {total} bad bios (1500-2000字纯散文)...')

    fixed = 0
    SAMPLE = """泰勒斯，约公元前624年至公元前546年，是古希腊米利都学派的奠基人。他生于小亚细亚的米利都城邦，活跃于前6世纪，被后世尊为西方哲学的开端。泰勒斯的生平事迹多由亚里士多德等后代学者记载，他不仅是一位哲学家，还是一位天文学家、数学家和政治家。

泰勒斯的哲学核心在于他提出"水是万物的本原"。这一命题看似简单，却蕴含深刻的哲学革命。首先，泰勒斯试图用一个自然元素来解释宇宙的多样性和统一性，而非诉诸神话中的神祇或超自然力量。他观察到水的变化形态：水能凝固为冰，蒸发为气，滋养生命，似乎具备转化为万物的潜能。这种"本原"概念不仅是物质上的起源，更是宇宙持续存在的原则。

其次，泰勒斯的"万物充满神灵"这一论断常被误解为原始迷信，实则体现其哲学的另一维度。他并非指神祇栖居于万物，而是强调自然本身具有活力和动因。例如，他观察到磁石能吸引铁，便认为磁石有"灵魂"，即内在的生命力。

泰勒斯的哲学史地位不可撼动。他被亚里士多德称为"哲学之父"，因为他是第一个提出"本原"问题的人。他的思想直接影响了米利都学派的阿那克西曼德和阿那克西美尼。在更广的文明史中，泰勒斯的理性精神为希腊科学、逻辑学和伦理学奠定了基础。他证明了哲学始于惊异，也始于对世界秩序的信任。"""

    for i in range(0, len(needs), 2):
        batch = needs[i:i+2]
        items = '\n'.join(
            f'{j+1}. {n}（{data[n].get("era","")}，{data[n].get("country","")}，{data[n].get("school","")}）'
            for j,(n,_) in enumerate(batch)
        )

        prompt = f"""你是哲学思想史专家。为以下哲学家写1500-2000字思想简介。

{items}

格式要求（极其重要）：
- 必须是流畅连贯的散文，像一篇优美的短文
- 绝对禁止：标题(#)、加粗(**)、编号列表(1.)、项目符号(-或*)、表格
- 只能用自然段落，段落之间空行分隔
- 结构：生平→著作→核心思想→历史影响，自然过渡
- 1500-2000字，语言平实但有深度

参考以下格式（注意这是纯段落散文，没有任何标记符号）：

{SAMPLE[:500]}...

JSON: [{{"index":1,"bio":"..."}},{{"index":2,"bio":"..."}}]"""

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
                            bio = r['bio']
                            # Strip any markdown
                            bio = re.sub(r'^#{1,4}\s+', '', bio, flags=re.MULTILINE)
                            bio = re.sub(r'\*\*([^*]+)\*\*', r'\1', bio)
                            bio = re.sub(r'^\s*[-*•]\s+', '', bio, flags=re.MULTILINE)
                            bio = re.sub(r'^\d+[\.\)]\s+', '', bio, flags=re.MULTILINE)
                            if len(bio) > len(data[batch[idx][0]].get('bio', '')):
                                data[batch[idx][0]]['bio'] = bio
                                if len(bio) >= 1000:
                                    fixed += 1
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    bad_left = sum(1 for n in bad_names if n in data and (
                        len(data[n].get('bio','')) < 1000 or
                        re.search(r'^#{1,4}\s', data[n].get('bio',''), re.MULTILINE) or
                        re.search(r'\*\*', data[n].get('bio',''))
                    ))
                    print(f'  [{fixed}/{total}] {bad_left} bad remaining', flush=True)
                    break
            except Exception as e:
                print(f'  Err: {e}', flush=True)
                time.sleep(2)
        time.sleep(0.2)

    good = sum(1 for v in data.values() if len(v.get('bio','')) >= 1000 and
               not re.search(r'^#{1,4}\s', v.get('bio',''), re.MULTILINE) and
               not re.search(r'\*\*', v.get('bio','')))
    print(f'Done! Good bios: {good}/{len(data)}')

if __name__ == '__main__':
    main()
