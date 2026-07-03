"""Generate Old/New Democracy school data."""
import re, json, urllib.request, os, time

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '_gen_east.py'), 'r', encoding='utf-8') as f:
    API_KEY = re.search(r'API_KEY\s*=\s*"([^"]+)"', f.read()).group(1)

TARGET = r"C:\Users\wqx_0\PyCharmProjects\Q&ASystem\DeepPhilosophy\app\src\pages\SchoolDetailPage.jsx"
with open(TARGET, 'r', encoding='utf-8') as f:
    content = f.read()

def call_api(sp, up, mt=8000):
    d = json.dumps({"model": "deepseek-chat", "messages": [{"role": "system", "content": sp}, {"role": "user", "content": up}], "temperature": 0.7, "max_tokens": mt}).encode()
    r = urllib.request.Request("https://api.deepseek.com/chat/completions", data=d, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=200) as resp:
        raw = json.loads(resp.read().decode())["choices"][0]["message"]["content"]
    raw = raw.strip()
    if raw.startswith("```"): raw = re.sub(r"^```\w*\n?", "", raw).rstrip("```").strip()
    return json.loads(raw)

def esc(s):
    if not isinstance(s, str): return str(s)
    return s.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")

def js_val(obj, indent=0):
    sp = "  " * indent; sp1 = "  " * (indent + 1)
    if isinstance(obj, dict):
        if not obj: return "{}"
        items = [f"{sp1}{k}: {js_val(v, indent+1)}" for k, v in obj.items()]
        return "{\n" + ",\n".join(items) + "\n" + sp + "}"
    elif isinstance(obj, list):
        if not obj: return "[]"
        if all(isinstance(x, str) and len(x) < 60 and "\n" not in x for x in obj):
            return "[" + ", ".join(f"'{x}'" for x in obj) + "]"
        return "[\n" + ",\n".join(js_val(x, indent+1) for x in obj) + "\n" + sp + "]"
    elif isinstance(obj, bool): return "true" if obj else "false"
    elif isinstance(obj, (int, float)): return str(obj)
    elif isinstance(obj, str): return "`" + esc(obj) + "`"
    return str(obj)

SCHOOLS = [
    ("旧民主主义", "OLD_DEMOCRACY", "旧民主主义革命时期的政治哲学，孙中山三民主义、五权宪法、权能分别、平均地权、节制资本。代表人物：孙中山、黄兴、宋教仁、章太炎。"),
    ("新民主主义", "NEW_DEMOCRACY", "毛泽东新民主主义论，革命分两步走，各革命阶级联合专政，民族的科学的大众的文化。代表人物：毛泽东、周恩来、刘少奇。"),
]

for name, var, outline in SCHOOLS:
    if f"const {var}_DATA" in content:
        print(f"SKIP {name}")
        continue

    print(f"Generating: {name}...")
    sp = f"""你是中国近现代哲学史教授。请为"{name}"这一中国近现代政治哲学流派生成完整学术数据。
输出严格JSON格式：
{{"quote":"代表性引文","quoteAuthor":"作者","subtitle":"一行精炼概括","overview":"400-800字多段落学术概述","thinkers":[{{"name":"人名","sub":"子流派","era":"年代","influence":1-10,"key":"核心思想","works":["著作"]}}],"relations":[{{"from":"来源","to":"目标","type":"师生/影响/继承/批判"}}],"conclusion":"300-600字总结","closingQuote":"结尾引文 —— 作者","sub_schools":[{{"name":"下属流派","era":"时代","desc":"描述"}}]}}
thinkers>=4, relations>=3。历史事实准确，客观学术性。"""
    up = f"""请为"{name}"生成完整数据。该流派的概要：{outline}"""
    try:
        result = call_api(sp, up, 8000)
    except Exception as e:
        print(f"  ERROR core: {e}")
        continue
    try:
        supp = call_api('你是中国哲学教授。输出严格合法JSON。', f'请为{name}生成cihai(20+),quotes(18+),works(6+),timeline(12+)。纯JSON。', 8000)
    except Exception as e:
        print(f"  ERROR supp: {e}")
        supp = {"cihai":[],"quotes":[],"works":[],"timeline":[]}
    result["cihai"] = supp.get("cihai", [])
    result["quotes"] = supp.get("quotes", [])
    result["works"] = supp.get("works", [])
    result["timeline"] = supp.get("timeline", [])
    result["name"] = name
    result.setdefault("sub_schools", [])
    print(f"  Overview: {len(result.get('overview',''))}c, Thinkers: {len(result.get('thinkers',[]))}, CIHAI: {len(supp.get('cihai',[]))}")

    js = f"\n// {name}\nconst {var}_DATA = {{\n  name: `{esc(name)}`,\n  quote: `{esc(result.get('quote',''))}`,\n  quoteAuthor: `{esc(result.get('quoteAuthor',''))}`,\n  subtitle: `{esc(result.get('subtitle',''))}`,\n  overview: `{esc(result.get('overview',''))}`,\n  thinkers: {js_val(result.get('thinkers',[]),1)},\n  relations: {js_val(result.get('relations',[]),1)},\n  timeline: {js_val(result.get('timeline',[]),1)},\n  conclusion: `{esc(result.get('conclusion',''))}`,\n  works: {js_val(result.get('works',[]),1)},\n  quotes: {js_val(result.get('quotes',[]),1)},\n  closingQuote: `{esc(result.get('closingQuote',''))}`\n}};\nconst {var}_CIHAI = {js_val(result.get('cihai',[]),0)};\nconst {var}_SUB_SCHOOLS = {js_val(result.get('sub_schools',[]),0)};\n"

    pos = content.find("function SchoolDetailPage()")
    content = content[:pos] + js + content[pos:]

    map_end = content.find("};", content.find("const SCHOOL_MAP = {"))
    entry = f"\n  '{name}': {{ data:{var}_DATA, sub:{var}_SUB_SCHOOLS, ci:{var}_CIHAI, bg:'url(/schools/default.jpg)' }},"
    content = content[:map_end] + entry + content[map_end:]
    print(f"  Injected!")
    time.sleep(1)

with open(TARGET, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"Final: {len(content)} bytes")
