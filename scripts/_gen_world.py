"""
Generate complete detail data for 8 world philosophies.
Reads API key from _gen_east.py at runtime.
Uses user's detailed outlines as API prompts.
"""
import re, json, urllib.request, time, os, sys

EAST3 = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_gen_east.py')
API_KEY = None
if os.path.exists(EAST3):
    with open(EAST3, 'r', encoding='utf-8') as f:
        m = re.search(r'API_KEY\s*=\s*"([^"]+)"', f.read())
        if m: API_KEY = m.group(1)
if not API_KEY: print("ERROR: API key not found"); sys.exit(1)

TARGET = r"C:\Users\wqx_0\PyCharmProjects\Q&ASystem\DeepPhilosophy\app\src\pages\SchoolDetailPage.jsx"

with open(TARGET, "r", encoding="utf-8") as f:
    target_content = f.read()
with open(TARGET + ".world_bak", "w", encoding="utf-8") as f:
    f.write(target_content)
print(f"Target: {len(target_content)} bytes, backup saved")

def call_api(sp, up, mt=8000):
    d = json.dumps({"model":"deepseek-chat","messages":[{"role":"system","content":sp},{"role":"user","content":up}],"temperature":0.65,"max_tokens":mt}).encode()
    r = urllib.request.Request("https://api.deepseek.com/chat/completions", data=d,
        headers={"Authorization":f"Bearer {API_KEY}","Content-Type":"application/json"})
    with urllib.request.urlopen(r, timeout=300) as resp:
        raw = json.loads(resp.read().decode())["choices"][0]["message"]["content"]
    raw = raw.strip()
    if raw.startswith("```"): raw = re.sub(r"^```\w*\n?","",raw).rstrip("```").strip()
    return json.loads(raw)

def esc(s):
    if not isinstance(s,str): return str(s)
    return s.replace("\\","\\\\").replace("`","\\`").replace("${","\\${")

def js_val(obj, indent=0):
    sp="  "*indent; sp1="  "*(indent+1)
    if isinstance(obj, dict):
        if not obj: return "{}"
        items=[f"{sp1}{k}: {js_val(v,indent+1)}" for k,v in obj.items()]
        return "{\n" + ",\n".join(items) + "\n" + sp + "}"
    elif isinstance(obj, list):
        if not obj: return "[]"
        if all(isinstance(x,str) and len(x)<60 and "\n" not in x for x in obj):
            return "[" + ", ".join(f"'{x}'" for x in obj) + "]"
        return "[\n" + ",\n".join(js_val(x,indent+1) for x in obj) + "\n" + sp + "]"
    elif isinstance(obj, bool): return "true" if obj else "false"
    elif isinstance(obj, (int,float)): return str(obj)
    elif isinstance(obj, str): return "`" + esc(obj) + "`"
    return str(obj)

def build_js(school):
    """Generate JS const blocks for a school."""
    v = school["var"]; n = school["name"]
    lines = []
    lines.append(f"// {n}")
    lines.append(f"const {v}_DATA = {{")
    lines.append(f"  name: `{esc(n)}`,")
    lines.append(f"  quote: `{esc(school.get('quote',''))}`,")
    lines.append(f"  quoteAuthor: `{esc(school.get('quoteAuthor',''))}`,")
    lines.append(f"  subtitle: `{esc(school.get('subtitle',''))}`,")
    lines.append(f"  overview: `{esc(school.get('overview',''))}`,")
    lines.append(f"  thinkers: {js_val(school.get('thinkers',[]), 1)},")
    lines.append(f"  relations: {js_val(school.get('relations',[]), 1)},")
    lines.append(f"  timeline: {js_val(school.get('timeline',[]), 1)},")
    lines.append(f"  conclusion: `{esc(school.get('conclusion',''))}`,")
    lines.append(f"  works: {js_val(school.get('works',[]), 1)},")
    lines.append(f"  quotes: {js_val(school.get('quotes',[]), 1)},")
    lines.append(f"  closingQuote: `{esc(school.get('closingQuote',''))}`")
    lines.append(f"}};")
    lines.append(f"const {v}_CIHAI = {js_val(school.get('cihai',[]), 0)};")
    lines.append(f"const {v}_SUB_SCHOOLS = {js_val(school.get('sub_schools',[]), 0)};")
    return "\n".join(lines)

# ═══════════════════════════════════════════
# 8 WORLD PHILOSOPHIES - outlines for API
# ═══════════════════════════════════════════

OUTLINES = [
    ("印度哲学", "INDIAN_PHILOSOPHY", """追求解脱的宗教哲学，以Moksha为终极目标。
正统六派（承认吠陀）：吠檀多派探讨Atman与Brahman关系；数论派建立宇宙演化二元论；瑜伽派提供身心修行方法；胜论派原子论自然哲学；正理派逻辑辩论术；弥曼差派祭祀仪轨解释。
非正统派（否定吠陀）：佛教以缘起性空为核心；耆那教强调非暴力Ahimsa和苦行；顺世论是彻底的唯物主义。
代表人物：商羯罗（不二论）、龙树（中观）、世亲（唯识）、帕坦伽利（瑜伽经）、迦毗罗（数论）。"""),

    ("日本哲学", "JAPANESE_PHILOSOPHY", """融合与转化的无之哲思。古代吸收中国儒家和佛教并发展出禅宗等日本特色流派。
近现代京都学派是最高代表：西田几多郎以纯粹经验和场所逻辑为核心，将禅宗绝对无与西方哲学对话；田边元提出种的逻辑和忏悔道；九鬼周造以粹的美学进行现象学分析；和辻哲郎以风土和间柄创立日本伦理学。
代表人物：西田几多郎、田边元、九鬼周造、和辻哲郎、道元（曹洞宗）、空海（真言宗）、西谷启治。"""),

    ("伊斯兰阿拉伯哲学", "ISLAMIC_PHILOSOPHY", """承前启后的理性之光。中世纪保存和发展希腊哲学，深刻影响欧洲经院哲学。
法尔萨法(Falsafa)：受希腊哲学尤其是亚里士多德影响深远的哲学传统。铿迪、法拉比、阿维森纳(伊本·西那)的必然存在论证、阿威罗伊(伊本·鲁世德)的双重真理论。
凯拉姆(Kalam)：伊斯兰思辨神学，用理性辩论捍卫教义。
苏非主义：神秘主义维度，通过内在修行直观体验神。
代表人物：铿迪、法拉比、伊本·西那(阿维森纳)、伊本·鲁世德(阿威罗伊)、安萨里、伊本·阿拉比、伊本·赫勒敦。"""),

    ("非洲哲学", "AFRICAN_PHILOSOPHY", """扎根土地与社群的生命智慧。强调口述传统、社群价值和生命体验。
政治哲学：由于长期殖民历史，政治独立和身份建构是核心议题。恩克鲁马提出泛非主义。
部族文化哲学：通过研究特定民族语言谚语挖掘哲学思想。核心概念Ubuntu乌班图，强调我在因我们同在的社群关联。
智者哲学：关注部落中智者的智慧和口述传统。
代表人物：恩克鲁马、桑戈尔（黑人性Negritude）、阿皮亚（认同哲学）、维雷杜（概念去殖民化）。"""),

    ("犹太哲学", "JEWISH_PHILOSOPHY", """理性与信仰的永恒对话。核心是用希腊哲学的理性概念来阐释犹太教信仰。
古代：亚历山大城的斐洛是第一位重要的犹太哲学家，用柏拉图主义解释圣经。
中世纪：生活在伊斯兰和基督教世界的犹太思想家们与阿拉伯哲学和经院哲学深度互动。迈蒙尼德的迷途指津调和亚里士多德与犹太教。
近现代：门德尔松、罗森茨维格、马丁·布伯的我与你、列维纳斯的他者的面孔。
代表人物：斐洛、萨阿迪亚·高恩、迈蒙尼德、斯宾诺莎、门德尔松、马丁·布伯、列维纳斯。"""),

    ("波斯哲学", "PERSIAN_PHILOSOPHY", """连接东西方的神秘之光。超过两千五百年连续哲学传统。
前伊斯兰时期：哲学思想蕴含在琐罗亚斯德教经典如伽萨等之中。善恶二元宇宙论和自由意志问题。
伊斯兰时期：波斯哲学家在法尔萨法传统中扮演核心角色。伊本·西那(阿维森纳)、苏赫拉瓦迪的光照哲学(ishraq)——以光为宇宙本原，以在场知识超越推理知识，将柏拉图理念论与琐罗亚斯德光明智慧融合。
代表人物：琐罗亚斯德、伊本·西那、苏赫拉瓦迪、拉齐、伊本·米斯卡韦、穆拉·萨德拉。"""),

    ("拉丁美洲哲学", "LATIN_AMERICAN_PHILOSOPHY", """具有强烈应用哲学色彩，专注于文化认同和解放政治。
殖民时期：巴托洛梅·德·拉斯·卡萨斯为印第安人权利辩护。
19世纪：独立和认同为主题。何塞·马蒂提出我们的美洲。
20世纪：解放哲学以杜塞尔为代表；被压迫者的教育学以弗莱雷为代表。将哲学从书斋转向穷人、原住民和被殖民者的声音。
代表人物：拉斯·卡萨斯、何塞·马蒂、杜塞尔、弗莱雷、罗多。"""),

    ("东南亚哲学", "SOUTHEAST_ASIAN_PHILOSOPHY", """深受传入的佛教、伊斯兰教、基督教等归化宗教影响，与本土文化融合形成独特面貌。
印度教和佛教从印度传入，在缅甸、泰国、柬埔寨、印尼等地扎根。伊斯兰教从阿拉伯和波斯传入马来半岛和印尼群岛。儒家思想在越南影响深远。本土万物有灵论作为基础层。
印尼潘查希拉建国五原则将多元统一上升为政治哲学。泰国适足经济哲学以中道和知足为核心。菲律宾kapwa共享身份概念。
代表人物：潘查希拉思想、素拉·西瓦拉克（泰国佛教社会主义）、穆尔雅纳（印尼哲学）。"""),
]

# ═══════════════════════════════════════════
# MAIN GENERATION LOOP
# ═══════════════════════════════════════════

print("\n" + "="*60)
print("Generating 8 world philosophy datasets via DeepSeek API")
print("="*60)

generated = {}

for name, var, outline in OUTLINES:
    print(f"\n{'='*50}")
    print(f"Generating: {name} ({var})")

    system_prompt = f"""你是世界哲学史教授。请为"{name}"生成完整的学术性数据。

输出严格合法的JSON。格式：
{{"quote":"代表性引文15-30字","quoteAuthor":"作者","subtitle":"一行精炼概括20-40字","overview":"400-800字多段落学术概述，涵盖起源、核心思想、主要流派、代表人物、历史贡献","thinkers":[{{"name":"人名","sub":"子流派/时期","era":"生卒年或时代","influence":影响力1-10,"key":"核心思想关键词5-10字","works":["代表著作2-5部"]}}],"relations":[{{"from":"来源","to":"目标","type":"关系类型(师生/影响/继承/批判/友谊/对立)"}}],"conclusion":"300-600字总结当代意义和历史地位","closingQuote":"结尾引文格式 引文 —— 作者《著作》","sub_schools":[{{"name":"下属流派","era":"时代","desc":"50-100字描述"}}]}}

要求：thinkers>=5, relations>=5, sub_schools>=2。历史事实准确。"""

    user_prompt = f"""请为"{name}"生成完整数据。该流派的概要：
{outline}

请确保：
1. overview至少400字，conclusion至少300字
2. thinkers必须是真实历史人物，至少5位
3. quote必须来自该流派的真实经典
4. 所有内容客观学术性"""

    try:
        result = call_api(system_prompt, user_prompt, 8000)
        result["cihai"] = []
        result["quotes"] = []
        result["works"] = []
        result["timeline"] = []
        result["name"] = name
        result["var"] = var
        result["sub_schools"] = result.get("sub_schools", [])
        print(f"  Overview: {len(result.get('overview',''))} chars")
        print(f"  Thinkers: {len(result.get('thinkers',[]))}")
        print(f"  Relations: {len(result.get('relations',[]))}")
        print(f"  Sub-schools: {len(result.get('sub_schools',[]))}")
        generated[name] = result
    except Exception as e:
        print(f"  ERROR: {str(e)[:100]}")
        continue
    time.sleep(1)

# ═══════════════════════════════════════════
# GENERATE CIHAI + QUOTES + WORKS + TIMELINE
# ═══════════════════════════════════════════

print("\n" + "="*60)
print("Generating cihai/quotes/works/timeline via API")
print("="*60)

for name, var, outline in OUTLINES:
    if name not in generated:
        continue

    prompt = f"""请为"{name}"这一哲学流派生成辞海、金句、著作和时间轴。

输出纯JSON：
{{"cihai":[{{"word":"术语","def":"定义50-80字","source":"出处"}}],"quotes":[{{"text":"引文","author":"作者出处","exp":"阐释80-120字"}}],"works":[{{"title":"书名","author":"作者","era":"年代","desc":"简介80-120字"}}],"timeline":[{{"year":"年份","event":"标题","detail":"描述50-80字","type":"birth/death/book/idea/event"}}]}}

要求：cihai>=20, quotes>=18, works>=6, timeline>=12。历史事实准确。"""

    for attempt in range(2):
        try:
            data = call_api("你是世界哲学教授。输出严格合法JSON。", prompt, 8000)
            c_cnt = len(data.get("cihai",[]))
            q_cnt = len(data.get("quotes",[]))
            w_cnt = len(data.get("works",[]))
            t_cnt = len(data.get("timeline",[]))
            print(f"  {name}: {c_cnt}cihai/{q_cnt}quotes/{w_cnt}works/{t_cnt}tl")
            if c_cnt >= 15 and q_cnt >= 12:
                generated[name]["cihai"] = data.get("cihai",[])
                generated[name]["quotes"] = data.get("quotes",[])
                generated[name]["works"] = data.get("works",[])
                generated[name]["timeline"] = data.get("timeline",[])
                break
        except Exception as e:
            if attempt == 0: time.sleep(2)
            else: print(f"  {name}: FAILED supplementary - {str(e)[:80]}")

# ═══════════════════════════════════════════
# INJECT INTO SchoolDetailPage.jsx
# ═══════════════════════════════════════════

print("\n" + "="*60)
print("Injecting into SchoolDetailPage.jsx")
print("="*60)

func_pos = target_content.find("function SchoolDetailPage()")
if func_pos < 0:
    print("ERROR: function SchoolDetailPage() not found!")
    sys.exit(1)

for name, var, outline in OUTLINES:
    if name not in generated:
        print(f"  SKIP {name}: not generated")
        continue

    g = generated[name]
    js_block = build_js(g)

    # Insert before function
    insertion = "\n\n" + js_block + "\n\n"
    target_content = target_content[:func_pos] + insertion + target_content[func_pos:]
    func_pos += len(insertion)  # Adjust for next insertion

    # Add to SCHOOL_MAP
    map_start = target_content.find("const SCHOOL_MAP = {")
    map_entry_end = target_content.find("};", map_start)
    map_entry = f"\n  '{name}': {{ data:{var}_DATA, sub:{var}_SUB_SCHOOLS, ci:{var}_CIHAI, bg:'url(/schools/greek.jpg)' }},"
    target_content = target_content[:map_entry_end] + map_entry + target_content[map_entry_end:]

    print(f"  OK: {name}")

# Write
with open(TARGET, "w", encoding="utf-8") as f:
    f.write(target_content)
print(f"\nFinal size: {len(target_content)} bytes")
print("DONE! Run build to verify.")
