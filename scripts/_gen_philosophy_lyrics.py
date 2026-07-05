"""为哲学入词生成正确数据"""
import json, re
from _lib import get_deepseek_key
from openai import OpenAI

client = OpenAI(api_key=get_deepseek_key(), base_url='https://api.deepseek.com')

definition = (
    '哲学入词从未在任何意义上被称为一个流派，'
    '但出于@txdsyl_的个人意愿与流行学术相结合的独特人文气息，仍选择将其收录。'
    '哲学入词，指的是上世纪90年代以来尤其在中国香港以林夕、黄伟文为代表的一批作词人以哲学入词，于歌词中见哲思。'
    '他们将存在主义、佛学、结构主义、后现代等哲学思想融入粤语流行歌词。'
    '林夕受佛教哲学影响深远，黄伟文则以社会批判见长，此外还有周耀辉等词人。'
)

prompt = f'''请为以下自定义哲学条目生成完整的流派数据JSON。

定义：{definition}

返回纯JSON（不要markdown代码块），所有文本字段用中文：
{{
  "name": "哲学入词",
  "subtitle": "简短副标题",
  "overview": "把上述定义作为第一段，然后展开论述，总字数>=500",
  "quote": "一句代表性歌词",
  "quoteAuthor": "作者",
  "region": "东方",
  "bg": "url(/schools/哲学入词.png)",
  "timeline": [{{"year":"1995","event":"事件","detail":"描述","type":"event"}}],
  "thinkers": [
    {{"name":"林夕","sub":"佛学入词","era":"1961-","influence":10,"key":"缘起性空","works":["富士山下","明年今日"]}},
    {{"name":"黄伟文","sub":"存在主义批判","era":"1969-","influence":10,"key":"荒诞与孤独","works":["浮夸","沙龙"]}},
    {{"name":"周耀辉","sub":"后现代解构","era":"1961-","influence":8,"key":"性别流动","works":["爱在瘟疫蔓延时"]}}
  ],
  "relations": [{{"from":"林夕","to":"黄伟文","type":"学术交流"}}],
  "cihai": [{{"word":"术语","def":"定义","source":"出处"}}],
  "quotes": [{{"text":"真实歌词","author":"作者","exp":"哲学阐释"}}],
  "works": [{{"title":"作品","author":"作者","era":"年代","desc":"简介"}}],
  "conclusion": "结语>=500字",
  "closingQuote": "名言——作者"
}}

要求：timeline>=8条(1980s-2020s香港词坛大事)，cihai>=15条，quotes>=15条(真实歌词)，works>=5部，relations>=6条。
'''

resp = client.chat.completions.create(
    model='deepseek-chat',
    messages=[{'role': 'user', 'content': prompt}],
    temperature=0.4, max_tokens=8000
)
text = resp.choices[0].message.content
m = re.search(r'\{[\s\S]*\}', text)
if m:
    data = json.loads(m.group(0))
    with open('../backend/data/school_哲学入词.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'Keys: {list(data.keys())}')
    print(f'Overview: {data.get("overview","")[:100]}...')
    print(f'Thinkers: {len(data.get("thinkers",[]))}')
    print(f'Timeline: {len(data.get("timeline",[]))}')
    print(f'Quotes: {len(data.get("quotes",[]))}')
    print(f'Cihai: {len(data.get("cihai",[]))}')
    print(f'Relations: {len(data.get("relations",[]))}')
    print('Saved')
else:
    print(f'No JSON found. Response: {text[:300]}')
