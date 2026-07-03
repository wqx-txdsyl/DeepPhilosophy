#!/usr/bin/env python3
"""
一键新增哲人：输入作者名 → DeepSeek 生成信息 → 插入数据库 → 更新标签系统
用法: python add_author.py "亚里士多德"
     python add_author.py "尼采" --folder "F:/philosophy/西方/尼采"
"""
import sys, os, json, re, requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_DIR = os.path.join(ROOT, "backend", "data")
PHILOSOPHERS_FILE = os.path.join(JSON_DIR, "philosophers.json")
ALIASES_FILE = os.path.join(JSON_DIR, "name_aliases.json")

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
DEEPSEEK_API = "https://api.deepseek.com/v1/chat/completions"

KNOWN_TAGS = [
    "古希腊哲学","教父哲学","经院哲学","理性主义","经验主义","启蒙运动","实在论",
    "唯心主义","自由主义","浪漫主义","德国古典哲学","功利主义","超验主义","实证主义",
    "马克思主义","生命哲学","实用主义","精神分析学","现象学","存在主义","分析哲学",
    "西方马克思主义","法兰克福学派","科学哲学","荒诞哲学","结构主义","政治哲学",
    "哲学诠释学","解构主义","后结构主义","后现代主义","伦理学","女性主义","技术哲学",
    "儒家","道家","墨家","法家","名家","阴阳家","兵家","两汉经学","魏晋玄学",
    "隋唐佛学","宋明理学","明清实学","乾嘉朴学","毛泽东思想","现代新儒家",
    "印度哲学","日本哲学","韩国哲学","伊斯兰哲学","阿拉伯哲学","非洲哲学"
]

def load_json(path, default={}):
    try:
        with open(path, "r", encoding="utf-8") as f: return json.load(f)
    except: return default

def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=2)

def normalize_tag(tag, norm_map):
    """标签归一化"""
    tag = tag.strip()
    # 基础清理
    for old, new in norm_map.items():
        if tag == old: return new
        if tag.startswith(old): return new
    # 相近匹配
    for known in KNOWN_TAGS:
        if tag in known or known in tag:
            return known
    return tag

def generate_author_info(name, extra_hint=""):
    """DeepSeek 生成哲人信息"""
    prompt = f"""你是哲学史专家。请为哲学家"{name}"生成完整的学术档案。{extra_hint}

输出 JSON（不要markdown代码块）：
{{
  "era": "生卒年，如'1770-1831年'或'约公元前624-前546年'",
  "country": "国家/地区",
  "school": "所属流派（从已知标签选择或提新），多个用' / '分隔。已知标签：{', '.join(KNOWN_TAGS)}",
  "bio": "1000字以上的哲学家生平与思想简介，必须是连贯散文，自然段落，绝对禁止分条列点/编号/加粗",
  "wiki_url": "英文Wikipedia链接",
  "baidu_url": "百度百科链接（如果有）"
}}

注意：bio必须流畅连贯，不要分点列出思想贡献，要以散文形式自然叙述。"""

    r = requests.post(DEEPSEEK_API,
        headers={"Authorization": f"Bearer {DEEPSEEK_KEY}", "Content-Type": "application/json"},
        json={"model": "deepseek-chat", "messages": [{"role": "user", "content": prompt}],
              "temperature": 0.5, "max_tokens": 3000}, timeout=120)
    content = r.json()["choices"][0]["message"]["content"]
    content = re.sub(r'^```json\s*', '', content).replace('```', '')
    return json.loads(content)

def add_author(name, folder_path=None):
    print(f"\n✒️ {name}")

    # 1. 检查是否已存在
    philosophers = load_json(PHILOSOPHERS_FILE, {})
    if name in philosophers:
        print(f"  - 已存在，跳过")
        return

    # 2. 生成信息
    hint = ""
    if folder_path and os.path.isdir(folder_path):
        books = [f for f in os.listdir(folder_path) if f.endswith(('.pdf','.epub','.txt'))]
        hint = f"该作者在本地有以下著作：{', '.join(books[:10])}"
    print(f"  DeepSeek 生成中...")
    info = generate_author_info(name, hint)
    era = info.get("era", "")
    country = info.get("country", "")
    school = info.get("school", "")
    bio = info.get("bio", "")
    wiki = info.get("wiki_url", f"https://en.wikipedia.org/wiki/{name.replace(' ', '_')}")
    baidu = info.get("baidu_url", f"https://baike.baidu.com/item/{name}")

    print(f"  时代: {era} | 国家: {country}")
    print(f"  流派: {school}")
    print(f"  简介: {len(bio)}字")

    # 3. 处理标签：标准化 + 合并 + 去重
    raw_tags = [t.strip() for t in school.replace("、", "/").replace("，", "/").split("/") if t.strip()]
    norm_map = {
        "存在主义先驱":"存在主义","柏拉图主义":"古希腊哲学","斯多葛主义":"斯多葛学派",
        "儒家创始人":"儒家","德国唯心论":"德国古典哲学","语言哲学":"分析哲学",
        "逻辑哲学":"分析哲学","存在哲学":"存在主义"
    }
    normalized = []
    new_tags = []
    for tag in raw_tags:
        n = normalize_tag(tag, norm_map)
        if n not in normalized:
            normalized.append(n)
        if n not in KNOWN_TAGS and n not in new_tags:
            new_tags.append(n)

    # 4. 保存
    philosophers[name] = {
        "era": era, "country": country, "school": " / ".join(normalized),
        "bio": bio, "wiki_url": wiki
    }
    save_json(PHILOSOPHERS_FILE, philosophers)
    print(f"  ✓ 已保存到 philosophers.json")

    # 5. 新标签
    if new_tags:
        print(f"  ⚠ 新标签: {new_tags}")
        print(f"    请手动添加到: backend/main.py _normalize_tag()")
        print(f"                  app/src/pages/AuthorsPage.jsx normMap")
        print(f"                  app/src/pages/BooksPage.jsx normMap")
        print(f"                  app/src/pages/HomePage.jsx normMap")

    # 6. 更新统计提示
    total = len(philosophers)
    print(f"  当前哲人总数: {total}")
    print(f"  下一步: cd app && npm run build && 同步 && 推送")
    # 如果前端计数硬编码，需手动更新 HomePage/Settings

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python add_author.py '哲人名' [--folder '路径']")
        sys.exit(1)
    name = sys.argv[1]
    folder = None
    if "--folder" in sys.argv:
        idx = sys.argv.index("--folder")
        folder = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else None
    add_author(name, folder)
