"""
Generate complete data for Western philosophy schools using DeepSeek API.
Same pattern as _gen_east.py and _gen_world.py.
Reads API key from _gen_east.py at runtime.
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

def call_api(sp, up, mt=8000):
    d = json.dumps({"model":"deepseek-chat","messages":[{"role":"system","content":sp},{"role":"user","content":up}],"temperature":0.7,"max_tokens":mt}).encode()
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
    v = school["var"]; n = school["name"]
    lines = [f"// {n}", f"const {v}_DATA = {{",
        f"  name: `{esc(n)}`,",
        f"  quote: `{esc(school.get('quote',''))}`,",
        f"  quoteAuthor: `{esc(school.get('quoteAuthor',''))}`,",
        f"  subtitle: `{esc(school.get('subtitle',''))}`,",
        f"  overview: `{esc(school.get('overview',''))}`,",
        f"  thinkers: {js_val(school.get('thinkers',[]), 1)},",
        f"  relations: {js_val(school.get('relations',[]), 1)},",
        f"  timeline: {js_val(school.get('timeline',[]), 1)},",
        f"  conclusion: `{esc(school.get('conclusion',''))}`,",
        f"  works: {js_val(school.get('works',[]), 1)},",
        f"  quotes: {js_val(school.get('quotes',[]), 1)},",
        f"  closingQuote: `{esc(school.get('closingQuote',''))}`",
        f"}};",
        f"const {v}_CIHAI = {js_val(school.get('cihai',[]), 0)};",
        f"const {v}_SUB_SCHOOLS = {js_val(school.get('sub_schools',[]), 0)};"]
    return "\n".join(lines)

# Complete list of 43 Western schools with brief outlines
WESTERN_SCHOOLS = [
    ("古希腊哲学", "GREEK", "前苏格拉底到亚里士多德。泰勒斯、赫拉克利特、巴门尼德、苏格拉底、柏拉图、亚里士多德。"),
    ("斯多葛学派", "STOICISM", "芝诺创立于雅典画廊。爱比克泰德、塞涅卡、马可·奥勒留。顺应自然而生活。"),
    ("怀疑论", "SKEPTICISM", "皮浪创立。悬搁判断、不动心。塞克斯都·恩披里柯。"),
    ("教父哲学", "PATRISTIC", "早期基督教教父的哲学。奥古斯丁、奥利金。信仰与理性。"),
    ("经院哲学", "SCHOLASTIC", "中世纪大学哲学。托马斯·阿奎那、安瑟伦。亚里士多德与基督教融合。"),
    ("唯名论", "NOMINALISM", "共相问题。奥卡姆的威廉。奥卡姆剃刀。"),
    ("理性主义", "RATIONALISM", "笛卡尔、斯宾诺莎、莱布尼茨。天赋观念、演绎推理。"),
    ("经验主义", "EMPIRICISM", "洛克、贝克莱、休谟。白板说、存在即被感知、因果怀疑。"),
    ("启蒙运动", "ENLIGHTENMENT", "伏尔泰、卢梭、孟德斯鸠、狄德罗。理性、自由、进步。"),
    ("实在论", "REALISM", "共相实在。柏拉图式与亚里士多德式实在论。"),
    ("唯心主义", "IDEALISM", "贝克莱的主观唯心、黑格尔的绝对唯心。"),
    ("自由主义", "LIBERALISM", "洛克、密尔。个人自由、权利、宽容。"),
    ("浪漫主义", "ROMANTICISM", "卢梭、赫尔德、施莱格尔。情感、自然、民族精神。"),
    ("女性主义", "FEMINISM", "沃斯通克拉夫特、波伏娃、巴特勒。性别平等、社会建构。"),
    ("德国古典哲学", "GERMAN_IDEALISM", "康德、费希特、谢林、黑格尔。批判哲学到绝对精神。"),
    ("生命哲学", "PHILOSOPHY_OF_LIFE", "柏格森、狄尔泰。生命冲动、绵延、体验。"),
    ("马克思主义", "MARXISM", "马克思、恩格斯。历史唯物主义、阶级斗争、剩余价值。"),
    ("存在主义", "EXISTENTIALISM", "克尔凯郭尔、海德格尔、萨特、加缪。存在先于本质。"),
    ("精神分析学", "PSYCHOANALYSIS", "弗洛伊德、荣格、拉康。无意识、原型、镜像阶段。"),
    ("结构主义", "STRUCTURALISM", "索绪尔、列维-斯特劳斯。语言结构、深层语法。"),
    ("现象学", "PHENOMENOLOGY", "胡塞尔、海德格尔、梅洛-庞蒂。回到事物本身。"),
    ("分析哲学", "ANALYTIC_PHILOSOPHY", "弗雷格、罗素、维特根斯坦。语言分析、逻辑。"),
    ("法兰克福学派", "FRANKFURT_SCHOOL", "阿多诺、霍克海默、马尔库塞、哈贝马斯。批判理论。"),
    ("荒诞哲学", "ABSURDISM", "加缪。西西弗神话。荒诞与反抗。"),
    ("后结构主义", "POSTSTRUCTURALISM", "德里达、福柯、德勒兹。解构、权力-知识。"),
    ("功利主义", "UTILITARIANISM", "边沁、密尔。最大幸福原理。"),
    ("超验主义", "TRANSCENDENTALISM", "爱默生、梭罗。自力更生、自然。"),
    ("实证主义", "POSITIVISM", "孔德。科学三阶段。"),
    ("社会学", "SOCIOLOGY", "孔德、涂尔干、韦伯。社会事实、理想类型。"),
    ("实用主义", "PRAGMATISM", "皮尔士、威廉·詹姆士、杜威。实际效果检验真理。"),
    ("过程哲学", "PROCESS_PHILOSOPHY", "怀特海。过程与实在。"),
    ("哲学人类学", "PHILOSOPHICAL_ANTHROPOLOGY", "舍勒、普莱斯纳。人在宇宙中的位置。"),
    ("科学哲学", "PHILOSOPHY_OF_SCIENCE", "波普尔、库恩、费耶阿本德。证伪、范式、怎么都行。"),
    ("西方马克思主义", "WESTERN_MARXISM", "卢卡奇、葛兰西、阿尔都塞。物化、霸权。"),
    ("政治哲学", "POLITICAL_PHILOSOPHY", "罗尔斯、诺齐克。正义论。"),
    ("伦理学", "ETHICS", "摩尔、黑尔、麦金太尔。元伦理学到德性伦理。"),
    ("基督教哲学", "CHRISTIAN_PHILOSOPHY", "存在主义神学到过程神学。蒂利希、朋霍费尔。"),
    ("哲学诠释学", "HERMENEUTICS", "伽达默尔、利科。视域融合。"),
    ("后现代主义", "POSTMODERNISM", "利奥塔、鲍德里亚。宏大叙事终结、拟像。"),
    ("批判理论", "CRITICAL_THEORY", "法兰克福学派延续。解放兴趣。"),
    ("社群主义", "COMMUNITARIANISM", "麦金太尔、桑德尔、泰勒。嵌入的自我。"),
    ("技术哲学", "PHILOSOPHY_OF_TECHNOLOGY", "海德格尔、埃吕尔、斯蒂格勒。技术本质。"),
    ("宗教哲学", "RELIGION_PHILOSOPHY", "宗教语言、宗教体验、恶的问题。希克、普兰丁格。"),
]

if __name__ == "__main__":
    with open(TARGET, "r", encoding="utf-8") as f:
        content = f.read()
    with open(TARGET + ".west_bak", "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Target: {len(content)} bytes, backup saved\n")

    for name, var, outline in WESTERN_SCHOOLS:
        # Skip if already exists
        if f"const {var}_DATA" in content:
            print(f"SKIP {name}: already exists")
            continue

        print(f"Generating: {name} ({var})...")

        system_prompt = f"""你是西方哲学史教授。请为"{name}"生成完整的学术性数据。
输出严格JSON，格式：
{{"quote":"代表性引文15-30字","quoteAuthor":"作者","subtitle":"一行精炼概括20-40字","overview":"400-800字多段落概述","thinkers":[{{"name":"人名","sub":"子流派","era":"生卒年","influence":1-10,"key":"核心思想","works":["著作2-5部"]}}],"relations":[{{"from":"来源","to":"目标","type":"师生/影响/继承/批判/友谊/对立"}}],"conclusion":"300-600字当代意义","closingQuote":"结尾引文 —— 作者《著作》","sub_schools":[{{"name":"下属流派","era":"时代","desc":"50-100字"}}]}}
thinkers>=5, relations>=5。历史事实准确。"""

        try:
            result = call_api(system_prompt, f"请为{name}生成完整数据。概要：{outline}", 8000)
            print(f"  Overview: {len(result.get('overview',''))} chars, Thinkers: {len(result.get('thinkers',[]))}")

            # Generate supplementary
            sp = "你是西方哲学教授。输出严格合法JSON。"
            up = f"""请为"{name}"生成辞海、金句、著作和时间轴。
{{"cihai":[{{"word":"术语","def":"定义50-80字","source":"出处"}}],"quotes":[{{"text":"引文","author":"出处","exp":"阐释80-120字"}}],"works":[{{"title":"书名","author":"作者","era":"年代","desc":"简介80-120字"}}],"timeline":[{{"year":"年份","event":"标题","detail":"描述50-80字","type":"birth/death/book/idea/event"}}]}}
cihai>=20, quotes>=18, works>=6, timeline>=12。"""
            supp = call_api(sp, up, 8000)
            result["cihai"] = supp.get("cihai",[])
            result["quotes"] = supp.get("quotes",[])
            result["works"] = supp.get("works",[])
            result["timeline"] = supp.get("timeline",[])
            print(f"  CIHAI: {len(result['cihai'])}, Quotes: {len(result['quotes'])}, Works: {len(result['works'])}, Timeline: {len(result['timeline'])}")
        except Exception as e:
            print(f"  ERROR: {str(e)[:80]}")
            continue

        result["name"] = name; result["var"] = var
        result.setdefault("sub_schools", [])
        js = build_js(result)

        # Inject before function
        pos = content.find("function SchoolDetailPage()")
        content = content[:pos] + "\n\n" + js + "\n\n" + content[pos:]

        # Add to SCHOOL_MAP
        map_pos = content.find("const SCHOOL_MAP = {")
        map_end = content.find("};", map_pos)
        entry = f"\n  '{name}': {{ data:{var}_DATA, sub:{var}_SUB_SCHOOLS, ci:{var}_CIHAI, bg:'url(/schools/greek.jpg)' }},"
        content = content[:map_end] + entry + content[map_end:]

        print(f"  ✓ Injected\n")
        time.sleep(1)

    with open(TARGET, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"DONE! Final size: {len(content)} bytes")
