"""哲学家 bio 批量扩充至 1000+ 字"""
import os, sys, io, json, time, urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env_path = os.path.join(BASE, '.env')
for line in open(env_path, encoding='utf-8'):
    line = line.strip()
    if line and not line.startswith('#') and '=' in line:
        k, v = line.split('=', 1)
        os.environ.setdefault(k.strip(), v.strip())

API_KEY = os.environ.get('DEEPSEEK_API_KEY', '')
if not API_KEY:
    print('错误: 未找到 DEEPSEEK_API_KEY'); sys.exit(1)

PHIL_FILE = os.path.join(BASE, 'app', 'public', 'philosophers.json')
BAK_FILE = os.path.join(BASE, 'app', 'public', 'philosophers_backup.json')

with open(PHIL_FILE, 'r', encoding='utf-8') as f:
    philosophers = json.load(f)

with open(BAK_FILE, 'w', encoding='utf-8') as f:
    json.dump(philosophers, f, ensure_ascii=False, indent=2)
print(f'已备份 philosophers_backup.json')

need_expand = []
for name, data in philosophers.items():
    if isinstance(data, dict) and len(data.get('bio', '')) < 900:
        need_expand.append((name, data.get('bio', ''), data.get('era', ''), data.get('school', '')))

print(f'需扩充: {len(need_expand)} / {len(philosophers)} 人')

SUCCESS, FAIL, SKIP = 0, 0, 0
BATCH_SIZE = 20

def expand_bio(name, short_bio, era, school):
    context = f'年代：{era}' if era else ''
    if school:
        context += f'；学派：{school}'

    prompt = f"""你是哲学史教授。请为哲学家撰写一篇详细的介绍（中文，600-800字），必须涵盖以下四个方面：

1. 生平关键节点（生卒年、师承、重要经历）
2. 核心思想贡献（主要理论、概念创新）
3. 主要著作简介
4. 对后世哲学的影响

哲学家：{name}
{context}

参考素材（可改写扩充）：{short_bio}

只返回正文，不要标题和标注。"""

    payload = {
        'model': 'deepseek-chat',
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 0.7, 'max_tokens': 2000,
    }
    req = urllib.request.Request(
        'https://api.deepseek.com/v1/chat/completions',
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {API_KEY}'},
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        r = json.loads(resp.read().decode('utf-8'))
        return r['choices'][0]['message']['content'].strip()


for i, (name, old_bio, era, school) in enumerate(need_expand, 1):
    try:
        old_len = len(old_bio)
        print(f'[{i}/{len(need_expand)}] {name} ({old_len}→', end='', flush=True)
        new_bio = expand_bio(name, old_bio, era, school)
        new_len = len(new_bio)

        if new_len < 300:
            print(f'{new_len} 太短，跳过) ')
            SKIP += 1
            continue

        philosophers[name]['bio'] = new_bio
        print(f'{new_len})')
        SUCCESS += 1

        if i % BATCH_SIZE == 0:
            with open(PHIL_FILE, 'w', encoding='utf-8') as f:
                json.dump(philosophers, f, ensure_ascii=False, indent=2)
            print(f'  --- 已保存 ({i}/{len(need_expand)}), 成功{SUCCESS} 失败{FAIL} ---')

        time.sleep(0.3)

    except Exception as e:
        msg = str(e)[:100]
        print(f'FAIL: {msg}')
        FAIL += 1
        time.sleep(2)

with open(PHIL_FILE, 'w', encoding='utf-8') as f:
    json.dump(philosophers, f, ensure_ascii=False, indent=2)

print(f'\n=== 完成 ===')
print(f'成功: {SUCCESS}, 失败: {FAIL}, 跳过: {SKIP}')
print(f'备份: philosophers_backup.json')
