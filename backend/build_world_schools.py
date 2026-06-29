"""build_world_schools.py — 构建9个新世界哲学流派数据"""
import re, os, json, time, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config

SCHOOLS = [
    {"name": "韩国哲学", "english": "Korean Philosophy", "region": "世界"},
    {"name": "西藏哲学", "english": "Tibetan Philosophy", "region": "世界"},
    {"name": "北欧哲学", "english": "Nordic Philosophy", "region": "世界"},
    {"name": "玛雅哲学", "english": "Mayan Philosophy", "region": "世界"},
    {"name": "阿兹特克哲学", "english": "Aztec Philosophy", "region": "世界"},
    {"name": "澳洲原住民哲学", "english": "Australian Aboriginal Philosophy", "region": "世界"},
    {"name": "蒙古中亚哲学", "english": "Mongolian & Central Asian Philosophy", "region": "世界"},
    {"name": "东欧斯拉夫哲学", "english": "Eastern European & Slavic Philosophy", "region": "世界"},
    {"name": "北美哲学", "english": "North American Philosophy", "region": "世界"},
]

from openai import OpenAI
client = OpenAI(api_key=config.DEEPSEEK_API_KEY, base_url=config.DEEPSEEK_BASE_URL)

for school in SCHOOLS:
    name = school['name']
    eng = school['english']
    print(f'\n=== {name} ===')

    prompt = f"""你是世界哲学专家。请为"{name}"（{eng}）流派撰写完整数据，用于哲学知识网站。

JSON格式：
{{
  "subtitle": "简短副标题（10-20字）",
  "overview": "流派概述（500-800字）：起源背景、核心命题、主要分支、发展脉络",
  "quote": "一句代表性格言",
  "quoteAuthor": "格言出处（人名或典籍名）",
  "timeline": [{{"year":"年份","event":"事件","detail":"描述","type":"birth/book/idea/event"}}] (5-8条关键事件),
  "thinkers": [{{"name":"思想家","sub":"所属分支","era":"年代","influence":1-10,"key":"核心概念","works":["著作"]}}] (8-15位代表人物),
  "relations": [{{"from":"来源","to":"目标","label":"关系类型"}}] (5-8条思想关系),
  "cihai": [{{"word":"术语","def":"定义","source":"出处"}}] (8-12个核心术语),
  "quotes": [{{"text":"引文","author":"作者","exp":"阐释"}}] (8-12条经典引文),
  "works": [{{"title":"书名","author":"作者","era":"年代","desc":"简介"}}] (8-15部代表著作),
  "conclusion": "结语（500-800字）：当代意义与反思"
}}

要求：全部中文输出，信息准确丰富，适合知识网站展示。"""

    try:
        resp = client.chat.completions.create(
            model=config.DEEPSEEK_MODEL,
            messages=[{"role":"user","content":prompt}],
            temperature=0.7, max_tokens=16384,
        )
        text = resp.choices[0].message.content
        m = re.search(r'\{.*\}', text, re.DOTALL)
        if m:
            data = json.loads(m.group(0))
            data['name'] = name
            data['region'] = '世界'
            data['bg'] = 'url(/schools/default.jpg)'
            # Save to file
            out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', f'school_{name}.json')
            with open(out_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f'  OK: {len(data.get("thinkers",[]))} thinkers, {len(data.get("works",[]))} works')
        else:
            print(f'  Parse fail: {text[:100]}')
    except Exception as e:
        print(f'  Error: {e}')
    time.sleep(0.3)

print('\nAll done!')
