"""翻译英文 bio + 改中文名"""
import os, sys, json, io, re, time, urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PHIL_FILE = os.path.join(BASE, 'app', 'public', 'philosophers.json')

# API key
env_path = os.path.join(BASE, '.env')
for line in open(env_path, encoding='utf-8'):
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1)
        os.environ.setdefault(k.strip(), v.strip())
API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')

with open(PHIL_FILE, 'r', encoding='utf-8') as f:
    p = json.load(f)

# 需要翻译 bio 的（高英文占比）
to_translate = {
    'Paulo Freire': '保罗·弗莱雷',
    'José Enrique Rodó': '何塞·恩里克·罗多',
    'Enrique Dussel': '恩里克·杜塞尔',
    'Bartolomé de las Casas': '巴托洛梅·德·拉斯·卡萨斯',
    'Leopoldo Zea': '莱奥波尔多·塞亚',
}

# 只需改名的（bio已经是中文）
to_rename = {
    'G.H.冯·赖特': '冯·赖特',
    '斯托克利·卡迈克尔（Kwame Ture）': '斯托克利·卡迈克尔',
    '霍米·K·巴巴': '霍米·巴巴',
    '何塞·里萨尔': '何塞·里萨尔',
    '琳达·图希瓦·史密斯（Linda Tuhiwai Smith）': '琳达·图希瓦·史密斯',
    '理查德·怀特（Richard White）': '理查德·怀特',
    '阿合马·叶塞维（Ahmad Yasawi）': '阿合马·叶塞维',
    '埃里克·汤普森（J. Eric S. Thompson）': '埃里克·汤普森',
    '萨冈彻辰（Sagang Sechen）': '萨冈彻辰',
    '纳格什班德（Baha-ud-Din Naqshband）': '纳格什班德',
}

# 先翻译
for old_name, new_name in to_translate.items():
    if old_name not in p:
        print(f'{old_name}: 不存在，跳过')
        continue
    data = p[old_name]
    bio = data.get('bio', '')
    era = data.get('era', '')
    eng_ratio = len(re.findall(r'[a-zA-Z]', bio)) / max(len(bio), 1)
    print(f'{old_name}: 英文占比={eng_ratio:.0%}', end=' ', flush=True)

    if eng_ratio > 0.1:
        prompt = f"""Translate this philosopher biography to fluent Chinese, keep all information:

Philosopher: {new_name}
Era: {era}

Original: {bio}

Return only the Chinese translation."""

        payload = {
            'model': 'deepseek-chat',
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.3, 'max_tokens': 3000
        }
        req = urllib.request.Request(
            'https://api.deepseek.com/v1/chat/completions',
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {API_KEY}'}
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                r = json.loads(resp.read().decode('utf-8'))
                new_bio = r['choices'][0]['message']['content'].strip()
            print(f'-> {len(new_bio)}字')
            p[old_name]['bio'] = new_bio
        except Exception as e:
            print(f'FAIL: {e}')
            continue
    else:
        print('已中文')

    # 改名字
    p[new_name] = p.pop(old_name)
    if isinstance(p[new_name], dict):
        p[new_name]['name'] = new_name
    print(f'  改名: {old_name} -> {new_name}')
    time.sleep(0.3)

# 只改名
for old_name, new_name in to_rename.items():
    if old_name in p:
        p[new_name] = p.pop(old_name)
        if isinstance(p[new_name], dict):
            p[new_name]['name'] = new_name
        print(f'改名: {old_name} -> {new_name}')

with open(PHIL_FILE, 'w', encoding='utf-8') as f:
    json.dump(p, f, ensure_ascii=False, indent=2)

print(f'\n总数: {len(p)}')
