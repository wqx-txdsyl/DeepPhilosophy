#!/usr/bin/env python3
"""
一键新增下属流派（sub-school）—— 轻量级自动化
与 add_school 的区别：
  - 不插入 world-philosophies / genealogy / timeline / worldmap
  - 不更新主页流派计数（subschool 不计入总数）
  - SCHOOL_MAP 使用 _json 动态加载（不内联 DATA）
用法: python add_subschool.py "流派名" "父流派名"
示例: python add_subschool.py "伊壁鸠鲁学派" "古希腊哲学"
"""
import sys, os, json, re, shutil, requests
from PIL import Image
from datetime import datetime

# ── 配置 ──
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SD_FILE = os.path.join(ROOT, "app", "src", "pages", "SchoolDetailPage.jsx")
JSON_DIR = os.path.join(ROOT, "backend", "data")
SCHOOLS_DIR = os.path.join(ROOT, "app", "public", "schools")
_keys_path = os.path.join(os.path.dirname(__file__), "api_keys.json")
_keys = {}
if os.path.exists(_keys_path):
    with open(_keys_path) as f: _keys = json.load(f)
DEEPSEEK_KEY = _keys.get("deepseek", "")
DEEPSEEK_API = "https://api.deepseek.com/v1/chat/completions"
if not DEEPSEEK_KEY:
    _east = os.path.join(ROOT, "_gen_east.py")
    if os.path.exists(_east):
        with open(_east, "r", encoding="utf-8") as f:
            m = re.search(r'API_KEY\s*=\s*"([^"]+)"', f.read())
            if m: DEEPSEEK_KEY = m.group(1)

def esc(s):
    return json.dumps(s, ensure_ascii=False)

def step(msg):
    print(f"\n{'='*50}\n  {msg}\n{'='*50}")

# ═══════════════════════════════════════════════
# Step 1: 生成/读取数据
# ═══════════════════════════════════════════════
def load_school(name):
    jp = os.path.join(JSON_DIR, f"school_{name}.json")
    if os.path.exists(jp):
        with open(jp, "r", encoding="utf-8") as f:
            return json.load(f)

    print("  JSON 不存在，用 DeepSeek 自动生成数据...")
    r = requests.post(DEEPSEEK_API,
        headers={"Authorization":f"Bearer {DEEPSEEK_KEY}","Content-Type":"application/json"},
        json={"model":"deepseek-chat","messages":[{"role":"user","content":f"""请为哲学下属流派"{name}"生成一份完整的流派数据JSON。严格按以下格式输出（不要markdown代码块，只要纯JSON）：

{{
  "name": "{name}",
  "subtitle": "简短中文副标题",
  "overview": "500字以上的流派概述，必须是散文连贯的哲学思想文本，自然段落，绝对禁止分条列点/编号/加粗/标题格式。内容涵盖起源背景、核心命题、主要分支、发展脉络",
  "conclusion": "500字以上的结语，必须是散文连贯的哲学思想文本，自然段落，绝对禁止分条列点/编号/加粗/标题格式。内容涵盖当代意义、理论贡献、面临挑战、未来展望",
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
  "closingQuote": "结语名言（取quotes最后一条，格式：'名言。——作者'）",
  "works": [
    {{"title":"书名","author":"作者","era":"年代","desc":"简介"}}
  ],
  "meta": {{"中文名":"{name}","英文名":"ENGLISH NAME"}},
  "region": "西方",
  "bg": "url(/schools/{name}.jpg)",
  "sub_schools": {{}}
}}

要求：timeline≥6条、thinkers≥6位、cihai≥12条、quotes≥12条、works数量不限。sub_schools为空对象（下属流派通常不再细分）。全部中文。"""}],
        "temperature":0.7,"max_tokens":6000}, timeout=300)
    content = r.json()["choices"][0]["message"]["content"]
    content = re.sub(r'^```json\s*', '', content)
    content = re.sub(r'\s*```$', '', content)
    data = json.loads(content)
    # 确保 closingQuote 不为空
    if not data.get("closingQuote") or not data["closingQuote"].strip():
        quotes = data.get("quotes", [])
        if quotes:
            last = quotes[-1]
            data["closingQuote"] = f"{last.get('text','')}——{last.get('author','')}"
        else:
            data["closingQuote"] = f"{data.get('quote','')}——{data.get('quoteAuthor','')}"
        print(f"  [FIX] closingQuote 缺失，已自动补全: {data['closingQuote'][:60]}...")
    os.makedirs(JSON_DIR, exist_ok=True)
    with open(jp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  [OK] DeepSeek 已生成 {jp}")
    return data

# ═══════════════════════════════════════════════
# Step 2: 图片处理
# ═══════════════════════════════════════════════
def fix_image(name, data):
    """确保图片存在，生成缩略图"""
    src_jpg = os.path.join(SCHOOLS_DIR, f"{name}.jpg")
    src_png = os.path.join(SCHOOLS_DIR, f"{name}.png")

    if os.path.exists(src_jpg):
        img_path = src_jpg
    elif os.path.exists(src_png):
        img_path = src_png
    else:
        print(f"[FAIL] 未找到图片: {name}.jpg/png")
        print("  请将图片放到 app/public/schools/")
        return None

    img = Image.open(img_path).convert("RGB")
    thumb_dir = os.path.join(SCHOOLS_DIR, "thumb")
    os.makedirs(thumb_dir, exist_ok=True)
    thumb_path = os.path.join(thumb_dir, os.path.basename(img_path))
    thumb = img.copy()
    thumb.thumbnail((200, 280), Image.LANCZOS)
    thumb.save(thumb_path, "JPEG", quality=75)
    print(f"  [OK] 缩略图: {os.path.basename(img_path)}")

    data["bg"] = f"url(/schools/{os.path.basename(img_path)})"
    with open(os.path.join(JSON_DIR, f"school_{name}.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return os.path.basename(img_path)

# ═══════════════════════════════════════════════
# Step 3: 复制 JSON 到 public/schools（供前端动态加载）
# ═══════════════════════════════════════════════
def copy_json_to_public(name):
    src = os.path.join(JSON_DIR, f"school_{name}.json")
    dst = os.path.join(SCHOOLS_DIR, f"school_{name}.json")
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"  [OK] JSON 已复制到 public/schools/")

# ═══════════════════════════════════════════════
# Step 4: 更新 SchoolDetailPage.jsx
# ═══════════════════════════════════════════════
def inject_sd(name, data, parent_name):
    """在 SCHOOL_MAP 中添加 _json 条目"""
    with open(SD_FILE, "r", encoding="utf-8") as f:
        sd = f.read()

    # 移除旧条目
    sd = re.sub(rf"\n  '{name}':.*?_json.*?\n", "\n", sd, flags=re.DOTALL)

    # 在父流派之后插入 SCHOOL_MAP 条目
    map_entry = f"  '{name}': {{ _json:'school_{name}.json', sub:{{}}, ci:[], bg:'url(/schools/{name}.jpg)' }},"
    parent_pattern = f"'{parent_name}': {{ data:"
    pos = sd.find(parent_pattern)
    if pos == -1:
        print(f"  [WARN] 未找到父流派 '{parent_name}' 的 SCHOOL_MAP 条目，附加到末尾")
        sd = sd.replace("\n};", f"\n{map_entry}\n}};", 1)
    else:
        # 找到父流派条目的结尾（下一个换行后的逗号）
        end = sd.index("\n", pos)
        depth = 0
        for i in range(end, len(sd)):
            if sd[i] == "{": depth += 1
            elif sd[i] == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        sd = sd[:end] + "\n" + map_entry + sd[end:]

    with open(SD_FILE, "w", encoding="utf-8") as f:
        f.write(sd)
    print("  [OK] SchoolDetailPage.jsx SCHOOL_MAP 已更新")

# ═══════════════════════════════════════════════
# Step 5: 更新父流派的 sub_schools
# ═══════════════════════════════════════════════
def update_parent_sub_schools(name, data, parent_name):
    """在父流派的 sub_schools 中添加该下属流派"""
    parent_jp = os.path.join(JSON_DIR, f"school_{parent_name}.json")
    desc = data.get("overview", "")[:80].replace("\n", " ")

    if os.path.exists(parent_jp):
        with open(parent_jp, "r", encoding="utf-8") as f:
            parent_data = json.load(f)
        if "sub_schools" not in parent_data:
            parent_data["sub_schools"] = {}
        parent_data["sub_schools"][name] = {"name": name, "desc": desc}
        with open(parent_jp, "w", encoding="utf-8") as f:
            json.dump(parent_data, f, ensure_ascii=False, indent=2)
        print(f"  [OK] 父流派 '{parent_name}' 的 sub_schools 已更新")

        # 同时更新 public 副本
        pub_parent = os.path.join(SCHOOLS_DIR, f"school_{parent_name}.json")
        if os.path.exists(pub_parent):
            shutil.copy2(parent_jp, pub_parent)

    # 更新 GREEK_SUB_SCHOOLS（如果是古希腊哲学的子流派）
    with open(SD_FILE, "r", encoding="utf-8") as f:
        sd = f.read()

    era_map = {
        "古希腊哲学": "前4世纪-4世纪",
        "教父哲学": "2世纪-8世纪",
        "经院哲学": "11世纪-15世纪",
    }
    era = era_map.get(parent_name, "古代")

    sub_entry = f"  {{ name:'{name}', era:'{era}', desc:'{desc}' }},"
    parent_sub_var = None
    if parent_name == "古希腊哲学":
        parent_sub_var = "GREEK_SUB_SCHOOLS"
    elif parent_name == "教父哲学":
        parent_sub_var = "PATRISTIC_SUB_SCHOOLS"

    if parent_sub_var:
        # 在对应的 SUB_SCHOOLS 数组末尾插入
        marker = f"const {parent_sub_var} = ["
        pos = sd.find(marker)
        if pos != -1:
            # 找到数组结束的 ];
            end_pos = sd.find("];", pos)
            if end_pos != -1:
                sd = sd[:end_pos] + "\n" + sub_entry + "\n" + sd[end_pos:]
                with open(SD_FILE, "w", encoding="utf-8") as f:
                    f.write(sd)
                print(f"  [OK] {parent_sub_var} 数组已更新")

# ═══════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════
def main():
    if len(sys.argv) < 2:
        print("用法: python add_subschool.py '下属流派名' ['父流派名']")
        print("示例: python add_subschool.py '伊壁鸠鲁学派' '古希腊哲学'")
        sys.exit(1)

    name = sys.argv[1]
    parent_name = sys.argv[2] if len(sys.argv) > 2 else "古希腊哲学"

    step(f"1/5 加载数据 - {name}")
    data = load_school(name)

    step("2/5 处理图片")
    fix_image(name, data)

    step("3/5 复制 JSON 到 public")
    copy_json_to_public(name)

    step("4/5 更新 SchoolDetailPage")
    inject_sd(name, data, parent_name)

    step("5/5 更新父流派 sub_schools")
    update_parent_sub_schools(name, data, parent_name)

    print(f"\n{'='*50}")
    print(f"  下属流派「{name}」已构建完成！")
    print(f"  注意：subschool 不计入流派总数，不显示在 genealogy/世界地图。")
    print(f"  下一步: cd app && npm run build")
    print(f"  然后: rm -rf ../backend/app-dist ../backend/static && cp -r dist ../backend/app-dist && cp -r dist ../backend/static")
    print(f"  然后: git add -A && git commit -m 'feat: subschool {name}' && git push")
    print(f"{'='*50}")

if __name__ == "__main__":
    main()
