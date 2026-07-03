"""
Generate Old/New Democracy schools with FULL format validation.
Every API response is checked and fixed before injection.
"""
import json, urllib.request, re, os, time

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_gen_east.py'), 'r', encoding='utf-8') as f:
    API_KEY = re.search(r'API_KEY\s*=\s*"([^"]+)"', f.read()).group(1)

TARGET = r"C:\Users\wqx_0\PyCharmProjects\Q&ASystem\DeepPhilosophy\app\src\pages\SchoolDetailPage.jsx"
with open(TARGET, 'r', encoding='utf-8') as f:
    content = f.read()

def call_api(sp, up, mt=4000):
    d = json.dumps({"model":"deepseek-chat","messages":[{"role":"system","content":sp},{"role":"user","content":up}],"temperature":0.7,"max_tokens":mt}).encode()
    r = urllib.request.Request("https://api.deepseek.com/chat/completions",data=d,
        headers={"Authorization":f"Bearer {API_KEY}","Content-Type":"application/json"})
    with urllib.request.urlopen(r,timeout=120) as resp:
        raw = json.loads(resp.read().decode())["choices"][0]["message"]["content"]
    raw = raw.strip()
    if raw.startswith("```"): raw = re.sub(r"^```\w*\n?","",raw).rstrip("```").strip()
    return json.loads(raw)

def esc(s):
    if not isinstance(s,str): return str(s)
    return s.replace("\\","\\\\").replace('"','\\"')

def validate_and_fix(obj, field, expected_keys):
    """Ensure field array contains objects with expected keys. If strings, convert."""
    arr = obj.get(field, [])
    if not arr: return arr
    # Check if first item is a string (bad) or dict (good)
    if isinstance(arr[0], str):
        # Convert string array to object array
        fixed = []
        for s in arr:
            entry = {k: "" for k in expected_keys}
            entry[expected_keys[0]] = s  # Put string as first key value
            fixed.append(entry)
        print(f"  WARNING: {field} was string array, auto-fixed to objects")
        return fixed
    return arr

SCHOOLS = [
    ("旧民主主义", "OLD_DEMOCRACY", "旧民主主义革命时期(约1894-1919)的政治哲学思潮。以孙中山三民主义为核心，包含资产阶级民主共和理想、五权宪法、权能分别、平均地权、节制资本。代表人物：孙中山、黄兴、宋教仁、章太炎。"),
    ("新民主主义", "NEW_DEMOCRACY", "毛泽东提出的新民主主义革命理论。1940年《新民主主义论》系统阐述：中国革命分两步走，各革命阶级联合专政，建设民族的科学的大众的文化。代表人物：毛泽东、周恩来、刘少奇。"),
]

for name, var, outline in SCHOOLS:
    print(f"\n{'='*50}")
    print(f"Generating: {name} ({var})")

    # --- Core data ---
    sp = f"""你是中国哲学史教授。请为"{name}"生成完整学术数据。输出严格JSON：
{{"quote":"代表性引文15-30字","quoteAuthor":"作者","subtitle":"一行概括20-40字","overview":"400-800字概述","thinkers":[{{"name":"人名","sub":"子流派","era":"生卒年","influence":1-10,"key":"核心思想5-10字","works":["著作1","著作2"]}}],"relations":[{{"from":"来源","to":"目标","type":"师生/影响/继承/批判"}}],"conclusion":"300-600字总结","closingQuote":"结尾引文 —— 作者"}}"""
    result = call_api(sp, f"请为{name}生成数据。概要：{outline}", 8000)
    print(f"  Thinkers: {len(result.get('thinkers',[]))}, Relations: {len(result.get('relations',[]))}")

    # --- CIHAI ---
    sp2 = "你是中国哲学教授。输出严格JSON。"
    up2 = f'请为"{name}"列出20个核心术语。格式：{{"cihai":[{{"word":"术语","def":"50-80字定义","source":"出处"}}]}}'
    cihai_data = call_api(sp2, up2, 4000)
    cihai_data["cihai"] = validate_and_fix(cihai_data, "cihai", ["word","def","source"])
    print(f"  CIHAI: {len(cihai_data.get('cihai',[]))} entries")

    # --- Works ---
    up3 = f'请列出"{name}"时期最重要的6-8部著作文献。书名不加《》。格式：{{"works":[{{"title":"书名","author":"作者","era":"年代","desc":"50-80字简介"}}]}}'
    works_data = call_api(sp2, up3, 2000)
    works_data["works"] = validate_and_fix(works_data, "works", ["title","author","era","desc"])
    print(f"  Works: {len(works_data.get('works',[]))} entries")

    # --- Quotes ---
    up4 = f'请列出"{name}"最具代表性的18-20条名言。格式：{{"quotes":[{{"text":"引文","author":"作者出处","exp":"50-80字阐释"}}]}}'
    quotes_data = call_api(sp2, up4, 3000)
    quotes_data["quotes"] = validate_and_fix(quotes_data, "quotes", ["text","author","exp"])
    print(f"  Quotes: {len(quotes_data.get('quotes',[]))} entries")

    # --- Timeline ---
    up5 = f'请列出"{name}"12-16个关键历史事件。格式：{{"timeline":[{{"year":"年份","event":"事件标题","detail":"50-80字描述","type":"birth/death/book/idea/event"}}]}}'
    timeline_data = call_api(sp2, up5, 3000)
    timeline_data["timeline"] = validate_and_fix(timeline_data, "timeline", ["year","event","detail","type"])
    print(f"  Timeline: {len(timeline_data.get('timeline',[]))} entries")

    # --- Build JSX in EXACT correct format ---
    def build_arr(field, entries, keys):
        if not entries: return f"{field}:[]"
        parts = []
        for e in entries:
            kvs = []
            for k in keys:
                v = esc(e.get(k, ""))
                kvs.append(f'"{k}": "{v}"')
            parts.append("{" + ", ".join(kvs) + "}")
        return f"{field}:[" + ",".join(parts) + "]"

    def arr_str(entries, keys):
        if not entries: return "[]"
        parts = []
        for e in entries:
            kvs = [f'"{k}": "{esc(e.get(k, ""))}"' for k in keys]
            parts.append("{" + ", ".join(kvs) + "}")
        return "[" + ",".join(parts) + "]"

    thinkers_js = arr_str(result.get('thinkers',[]), ['name','sub','era','influence','key','works'])
    relations_js = arr_str(result.get('relations',[]), ['from','to','type'])
    timeline_js = arr_str(timeline_data.get('timeline',[]), ['year','event','detail','type'])
    works_js = arr_str(works_data.get('works',[]), ['title','author','era','desc'])
    quotes_js = arr_str(quotes_data.get('quotes',[]), ['text','author','exp'])
    cihai_js = arr_str(cihai_data.get('cihai',[]), ['word','def','source'])

    js = f"""
// {name}
const {var}_DATA = {{
  name: "{esc(name)}",
  quote: "{esc(result.get('quote',''))}",
  quoteAuthor: "{esc(result.get('quoteAuthor',''))}",
  subtitle: "{esc(result.get('subtitle',''))}",
  overview: "{esc(result.get('overview',''))}",
  thinkers: {thinkers_js},
  relations: {relations_js},
  timeline: {timeline_js},
  conclusion: "{esc(result.get('conclusion',''))}",
  works: {works_js},
  quotes: {quotes_js},
  closingQuote: "{esc(result.get('closingQuote',''))}"
}};
const {var}_CIHAI = {cihai_js};
const {var}_SUB_SCHOOLS = [];
"""

    # Inject before function
    pos = content.find("function SchoolDetailPage()")
    content = content[:pos] + js + content[pos:]

    # Add to SCHOOL_MAP
    map_end = content.find("};", content.find("const SCHOOL_MAP = {"))
    entry = f"\n  '{name}': {{ data:{var}_DATA, sub:{var}_SUB_SCHOOLS, ci:{var}_CIHAI, bg:'url(/schools/{name}.jpg)' }},"
    content = content[:map_end] + entry + content[map_end:]

    print(f"  OK Injected")
    time.sleep(1)

with open(TARGET, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"\nFinal: {len(content)} bytes")
print("DONE!")
