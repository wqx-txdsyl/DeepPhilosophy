#!/usr/bin/env python3
"""
一键新增流派 —— 全流程自动化
用法: python add_school.py "流派名"
"""
import sys, os, json, re, shutil, requests
from PIL import Image
from datetime import datetime

# ── 配置 ──
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SD_FILE = os.path.join(ROOT, "app", "src", "pages", "SchoolDetailPage.jsx")
GEN_FILE = os.path.join(ROOT, "app", "src", "pages", "GenealogyPage.jsx")
TL_FILE = os.path.join(ROOT, "app", "src", "components", "PhilosophyTimeline.jsx")
WP_FILE = os.path.join(ROOT, "app", "src", "pages", "WorldPhilosophiesPage.jsx")
MAP_FILE = os.path.join(ROOT, "app", "src", "components", "WorldMap.jsx")
HP_FILE = os.path.join(ROOT, "app", "src", "pages", "HomePage.jsx")
ST_FILE = os.path.join(ROOT, "app", "src", "pages", "SettingsPage.jsx")
JSON_DIR = os.path.join(ROOT, "backend", "data")
SCHOOLS_DIR = os.path.join(ROOT, "app", "public", "schools")
_keys_path = os.path.join(os.path.dirname(__file__), "api_keys.json")
with open(_keys_path) as f: _keys = json.load(f)
DEEPSEEK_KEY = _keys["deepseek"]
DEEPSEEK_API = "https://api.deepseek.com/v1/chat/completions"
AGNES_KEY = _keys["agnes"]

def esc(s):
    return json.dumps(s, ensure_ascii=False)

def step(msg):
    print(f"\n{'='*50}\n  {msg}\n{'='*50}")

# ═══════════════════════════════════════════════
# Step 1: 读取数据
# ═══════════════════════════════════════════════
def load_school(name):
    jp = os.path.join(JSON_DIR, f"school_{name}.json")
    if os.path.exists(jp):
        with open(jp, "r", encoding="utf-8") as f:
            return json.load(f)

    print("  JSON 不存在，用 DeepSeek 自动生成数据...")
    r = requests.post(DEEPSEEK_API,
        headers={"Authorization":f"Bearer {DEEPSEEK_KEY}","Content-Type":"application/json"},
        json={"model":"deepseek-chat","messages":[{"role":"user","content":f"""请为哲学流派"{name}"生成一份完整的流派数据JSON。严格按以下格式输出（不要markdown代码块，只要纯JSON）：

{{
  "name": "{name}",
  "subtitle": "简短中文副标题",
  "overview": "500字以上的流派概述，包括起源背景、核心命题、主要分支、发展脉络",
  "conclusion": "500字以上的结语，包括当代意义、理论贡献、面临挑战、未来展望",
  "quote": "一句该流派代表性名言",
  "quoteAuthor": "名言作者",
  "timeline": [
    {{"year":"年份","event":"事件名","detail":"详细描述","type":"event"}}
  ],
  "thinkers": [
    {{"name":"思想家姓名","sub":"下属分支","era":"生卒年","influence":8,"key":"核心概念","works":["代表作1","代表作2"]}}
  ],
  "relations": [
    {{"from":"思想家A","to":"思想家B","label":"关系描述"}}
  ],
  "cihai": [
    {{"word":"术语","def":"定义","source":"出处"}}
  ],
  "quotes": [
    {{"text":"引文","author":"作者","exp":"阐释"}}
  ],
  "works": [
    {{"title":"书名","author":"作者","era":"年代","desc":"简介"}}
  ],
  "meta": {{"中文名":"{name}","英文名":"ENGLISH NAME"}},
  "region": "世界",
  "bg": "url(/schools/{name}.jpg)",
  "sub_schools": {{}}
}}

要求：timeline≥8条、thinkers≥8位、cihai≥20条、quotes≥20条、works数量不限。全部中文。"""}],
        "temperature":0.7,"max_tokens":8000}, timeout=300)
    content = r.json()["choices"][0]["message"]["content"]
    # 清理可能的 markdown 包裹
    content = re.sub(r'^```json\s*', '', content)
    content = re.sub(r'\s*```$', '', content)
    data = json.loads(content)
    os.makedirs(JSON_DIR, exist_ok=True)
    with open(jp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  ✓ DeepSeek 已生成 {jp}")
    return data

# ═══════════════════════════════════════════════
# Step 2: 图片处理
# ═══════════════════════════════════════════════
ASCII_MAP = {'萨满哲学':'shaman','北极原住民哲学':'arctic','南岛哲学':'austronesian','高加索哲学':'caucasus','高加索-草原哲学':'caucasus-steppe','太平洋原住民哲学':'pacific'}

def fix_image(name, data):
    """确保图片为 ASCII 文件名，生成缩略图"""
    ascii_name = ASCII_MAP.get(name)
    src_jpg = os.path.join(SCHOOLS_DIR, f"{name}.jpg")
    src_png = os.path.join(SCHOOLS_DIR, f"{name}.png")
    dst = os.path.join(SCHOOLS_DIR, f"{ascii_name}.jpg") if ascii_name else None

    if os.path.exists(src_jpg):
        img_path = src_jpg
    elif os.path.exists(src_png):
        img_path = src_png
    else:
        print(f"✗ 未找到图片: {name}.jpg/png")
        print("  请将图片放到 app/public/schools/")
        return

    img = Image.open(img_path).convert("RGB")
    if dst and img_path != dst:
        img.save(dst, "JPEG", quality=92)
        print(f"  ✓ 重命名: {os.path.basename(img_path)} → {os.path.basename(dst)}")
        img_path = dst

    # 缩略图
    thumb_dir = os.path.join(SCHOOLS_DIR, "thumb")
    os.makedirs(thumb_dir, exist_ok=True)
    thumb_name = os.path.basename(img_path)
    thumb_path = os.path.join(thumb_dir, thumb_name)
    thumb = img.copy()
    thumb.thumbnail((200, 280), Image.LANCZOS)
    thumb.save(thumb_path, "JPEG", quality=75)
    print(f"  ✓ 缩略图: {thumb_name}")

    # 更新 JSON bg
    data["bg"] = f"url(/schools/{os.path.basename(img_path)})"
    with open(os.path.join(JSON_DIR, f"school_{name}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return os.path.basename(img_path)

# ═══════════════════════════════════════════════
# Step 3: 内联 DATA + SCHOOL_MAP + ENG_NAMES
# ═══════════════════════════════════════════════
def build_js_const(name, data):
    """生成 JS const DATA 块，仿照现有格式"""
    vn = name.replace("-", "") + "_DATA"
    j = lambda x: json.dumps(x, ensure_ascii=False)
    ja = lambda arr: "[" + ", ".join(j(x) for x in arr) + "]"

    parts = [f"const {vn} = {{"]
    for k in ["name","subtitle","overview","quote","quoteAuthor","conclusion","closingQuote","region","bg"]:
        parts.append(f"  {k}: {j(data.get(k,''))},")
    # timeline
    parts.append("  timeline: [")
    for e in data.get("timeline",[]):
        parts.append(f"    {{year:{j(e.get('year',''))}, event:{j(e.get('event',''))}, detail:{j(e.get('detail',''))}, type:{j(e.get('type','event'))}}},")
    parts.append("  ],")
    # thinkers
    parts.append("  thinkers: [")
    for t in data.get("thinkers",[]):
        w = t.get("works",[]); w = w if isinstance(w,list) else []
        if w and isinstance(w[0], dict): w = [x.get("title","") for x in w]
        parts.append(f"    {{name:{j(t.get('name',''))}, sub:{j(t.get('sub',''))}, era:{j(t.get('era',''))}, influence:{t.get('influence',5) or 5}, key:{j(t.get('key',''))}, works:{ja(w)}}},")
    parts.append("  ],")
    # relations, cihai, quotes, works (school), meta
    for k in ["relations","cihai","quotes"]:
        parts.append(f"  {k}: [")
        for item in data.get(k,[]):
            if k == "relations":
                parts.append(f"    {{from:{j(item.get('from',''))}, to:{j(item.get('to',''))}, label:{j(item.get('label',''))}}},")
            elif k == "cihai":
                parts.append(f"    {{word:{j(item.get('word',''))}, def:{j(item.get('def',''))}, source:{j(item.get('source',''))}}},")
            elif k == "quotes":
                parts.append(f"    {{text:{j(item.get('text',''))}, author:{j(item.get('author',''))}, exp:{j(item.get('exp',''))}}},")
        parts.append("  ],")
    parts.append("  works: [")
    for w in data.get("works",[]):
        if isinstance(w, dict):
            parts.append(f"    {{title:{j(w.get('title',''))}, author:{j(w.get('author',''))}, era:{j(w.get('era',''))}, desc:{j(w.get('desc',''))}}},")
    parts.append("  ],")
    # meta
    meta = data.get("meta",{})
    if meta:
        parts.append("  meta: {")
        for mk, mv in meta.items(): parts.append(f"    {j(mk)}: {j(mv)},")
        parts.append("  },")
    # sub_schools
    ss = data.get("sub_schools",{})
    if ss:
        parts.append("  sub_schools: {")
        for sk, sv in ss.items(): parts.append(f"    {j(sk)}: {{name:{j(sv.get('name',sk))}, desc:{j(sv.get('desc',''))}}},")
        parts.append("  },")
    parts.append("};")
    return vn, "\n".join(parts)

def inject_sd(name, block, vn):
    """将 DATA 块注入 SchoolDetailPage.jsx"""
    with open(SD_FILE, "r", encoding="utf-8") as f:
        sd = f.read()

    # 移除旧的 _json 条目
    sd = re.sub(rf"\n  '{name}':.*?_json.*?\n", "", sd, flags=re.DOTALL)

    # DATA 插入点：const 黑人哲学_DATA 之后
    marker = "const 黑人哲学_DATA"
    pos = sd.find(marker)
    depth = 0
    for i in range(sd.index("{", pos), len(sd)):
        if sd[i] == "{": depth += 1
        elif sd[i] == "}":
            depth -= 1
            if depth == 0:
                pos = i + 2; break
    sd = sd[:pos] + "\n" + block + "\n" + sd[pos:]

    # SCHOOL_MAP 条目插入
    bg_name = ASCII_MAP.get(name, name)
    map_entry = f"  '{name}': {{ data:{vn}, sub:{{}}, ci:[], bg:'url(/schools/{bg_name}.jpg)' }},"
    black = "  '黑人哲学': { data:黑人哲学_DATA, sub:{}, ci:[], bg:'url(/schools/黑人哲学.jpg)' },\n"
    sd = sd.replace(black, black + map_entry + "\n")

    # ENG_NAMES 条目
    eng = data.get("meta",{}).get("英文名", name.upper())
    eng_entry = f"  '{name}': '{eng}',\n"
    eng_marker = "  '黑人哲学': 'BLACK PHILOSOPHY',\n"
    sd = sd.replace(eng_marker, eng_marker + eng_entry)

    with open(SD_FILE, "w", encoding="utf-8") as f:
        f.write(sd)
    print("  ✓ SchoolDetailPage.jsx 已更新")

# ═══════════════════════════════════════════════
# Step 4+5: 插入分页 + 谱系
# ═══════════════════════════════════════════════
def get_century(data):
    t = data.get("timeline",[])
    return t[0].get("year","20世纪") if t else "20世纪"

def inject_pages(name, data, school_century):
    """世界哲学分页 + Genealogy + Timeline"""
    desc = data.get("overview","")[:60].replace("\n","")
    century = get_century(data)
    region = data.get("region","世界")
    # WorldPhilosophiesPage
    color = hex(hash(name) % 0xFFFFFF)[2:].zfill(6)
    wp_entry = f"  {{ name: '{name}', color: '#{color}', desc: '{desc}' }},\n];"
    with open(WP_FILE, "r", encoding="utf-8") as f: wp = f.read()
    wp = wp.replace("\n];", f"\n{wp_entry}", 1)
    with open(WP_FILE, "w", encoding="utf-8") as f: f.write(wp)
    print("  ✓ WorldPhilosophiesPage")

    # GenealogyPage ALL_SCHOOLS
    gl_entry = f"  {{ century:'{century}', name:'{name}', region:'{region}', desc:'{desc}', tier:'B' }},"
    with open(GEN_FILE, "r", encoding="utf-8") as f: gl = f.read()
    # 插入到黑人哲学之前
    gl = gl.replace("  { century:'19世纪', name:'黑人哲学'", gl_entry + "\n  { century:'19世纪', name:'黑人哲学'")
    with open(GEN_FILE, "w", encoding="utf-8") as f: f.write(gl)
    print("  ✓ GenealogyPage")

    # PhilosophyTimeline
    tl_entry = f"  {{ century:'{century}', name:'{name}', region:'{region}', desc:'{desc}' }},"
    with open(TL_FILE, "r", encoding="utf-8") as f: tl = f.read()
    tl = tl.replace("  { century:'19世纪', name:'黑人哲学'", tl_entry + "\n  { century:'19世纪', name:'黑人哲学'")
    with open(TL_FILE, "w", encoding="utf-8") as f: f.write(tl)
    print("  ✓ PhilosophyTimeline")

    # GenealogyPage IMG_MAP
    ascii_name = ASCII_MAP.get(name, name)
    map_line = f" '{name}':'{ascii_name}',"
    with open(GEN_FILE, "r", encoding="utf-8") as f: gl = f.read()
    gl = gl.replace("const IMG_MAP = {", f"const IMG_MAP = {{\n  {map_line}")
    with open(GEN_FILE, "w", encoding="utf-8") as f: f.write(gl)
    print("  ✓ GenealogyPage IMG_MAP")

# ═══════════════════════════════════════════════
# Step 6: 世界地图定位
# ═══════════════════════════════════════════════
def add_to_worldmap(name, data):
    """使用 AI 定位流派在地图上的坐标"""
    if data.get("region") != "世界": return
    # 跳过无法锁定地区的流派
    skip_keywords = ["环境","技术","伦理","政治","宗教","女性","社群","后现代","解构","批判"]
    if any(k in name for k in skip_keywords):
        print("  - 非地区流派，跳过地图")
        return

    print("  正在用 Agnes 识图定位...")
    desc = data.get("overview","")[:200]
    r = requests.post("https://apihub.agnes-ai.com/v1/chat/completions",
        headers={"Authorization":f"Bearer {AGNES_KEY}","Content-Type":"application/json"},
        json={"model":"agnes-2.0-flash","messages":[{"role":"user","content":f"Analyze this philosophy school: {name}. {desc} Estimate its geographic center as percentage coordinates (x%, y%) on a world map. Return ONLY JSON: {{\"x\":NN,\"y\":NN}}. x=left edge, y=top edge."}],"temperature":0.1,"max_tokens":100}, timeout=60)
    content = r.json()["choices"][0]["message"]["content"]
    m = re.search(r'"x":\s*(\d+).*"y":\s*(\d+)', content)
    if m:
        x, y = int(m.group(1)), int(m.group(2))
    else:
        x, y = 50, 50
    print(f"  ✓ AI 定位: ({x}%, {y}%)")

    with open(MAP_FILE, "r", encoding="utf-8") as f: mp = f.read()
    entry = f"  {{ id: '{ASCII_MAP.get(name,name)}', name: '{name}', sub: '{name}', desc: '{desc[:40]}', x: {x}, y: {y}, r: 16, path: '/school/{name}' }},\n];"
    mp = mp.replace("\n];", f"\n{entry}")
    with open(MAP_FILE, "w", encoding="utf-8") as f: f.write(mp)
    print("  ✓ WorldMap")

# ═══════════════════════════════════════════════
# Step 7: 更新计数
# ═══════════════════════════════════════════════
def update_counts():
    # 计算总数：SCHOOL_MAP 条目数
    with open(SD_FILE, "r", encoding="utf-8") as f: sd = f.read()
    total = len(re.findall(r"'\S+': \{ data:", sd))
    western = len(re.findall(r"'(\S+)': \{ data:.*region.*西方", sd, re.DOTALL))
    eastern = len(re.findall(r"'(\S+)': \{ data:.*region.*东方", sd, re.DOTALL))
    world = total - western - eastern

    for fp in [HP_FILE, ST_FILE]:
        with open(fp, "r", encoding="utf-8") as f: c = f.read()
        c = re.sub(r"(流派.*?)(\d+)(.*流派)", lambda m: m.group(1) + str(total) + m.group(3), c)
        c = re.sub(r"(世界.*?)(\d+)(.*流派)", lambda m: m.group(1) + str(world) + m.group(3), c)
        with open(fp, "w", encoding="utf-8") as f: f.write(c)
    print(f"  ✓ 计数已更新: {total} 流派 (东{eastern}/西{western}/世{world})")

    # Genealogy 页脚
    with open(GEN_FILE, "r", encoding="utf-8") as f: gl = f.read()
    cn_num = {96:"九十六",97:"九十七",98:"九十八",99:"九十九",100:"一百",101:"一百零一",102:"一百零二",103:"一百零三",104:"一百零四",105:"一百零五"}
    gl = re.sub(r"(一百零二个哲学流派|九十六个哲学流派)", cn_num.get(total, f"{total}个") + "哲学流派", gl)
    with open(GEN_FILE, "w", encoding="utf-8") as f: f.write(gl)

# ═══════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════
def main():
    if len(sys.argv) < 2:
        print("用法: python add_school.py '流派名'")
        sys.exit(1)
    name = sys.argv[1]

    step("1/7 加载数据")
    data = load_school(name)

    step("2/7 处理图片")
    fix_image(name, data)

    step("3/7 内联 DATA + 更新 SchoolDetailPage")
    vn, block = build_js_const(name, data)
    inject_sd(name, block, vn)

    step("4/7 插入流派分页")
    step("5/7 插入谱系页")
    inject_pages(name, data, get_century(data))

    step("6/7 世界地图（如适用）")
    add_to_worldmap(name, data)

    step("7/7 更新计数")
    update_counts()

    print(f"\n{'='*50}")
    print(f"  流派「{name}」已全部构建完成！")
    print(f"  下一步: cd app && npm run build")
    print(f"  然后: rm -rf ../backend/app-dist ../backend/static && cp -r dist ../backend/app-dist && cp -r dist ../backend/static")
    print(f"  然后: git add -A && git commit -m 'feat: {name}' && git push")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
