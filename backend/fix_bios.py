"""批量修复 <1000 字的哲学家 bio"""
import json, os, sys, io, time, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(os.path.dirname(BASE), '.env')
if os.path.exists(env_path):
    for line in open(env_path, encoding='utf-8'):
        if '=' in line: k,v=line.strip().split('=',1); os.environ.setdefault(k.strip(),v.strip())

API_KEY = os.environ.get('DEEPSEEK_API_KEY','')
if not API_KEY: print('No API key'); sys.exit(1)

PHILO = os.path.join(BASE, '..', 'app', 'public', 'philosophers.json')
p = json.load(open(PHILO, 'r', encoding='utf-8'))
short = [(n, i.get('era',''), i.get('school','')) for n, i in p.items() if len(i.get('bio','')) < 1000]
print(f'Fixing {len(short)} short bios...')

BATCH = 4
fixed = 0
for bi in range(0, len(short), BATCH):
    batch = short[bi:bi+BATCH]
    lines = '\n'.join(f'- {n}（{e} - {s}）' for n, e, s in batch)
    payload = {
        'model': 'deepseek-chat',
        'messages': [{'role':'user','content': f'为以下哲学家各写1000字以上中文简介。返回JSON: {{"名字":"简介...", ...}}。只返回JSON，不要markdown。\n\n{lines}'}],
        'temperature': 0.7, 'max_tokens': 16384,
        'response_format': {'type': 'json_object'},
    }
    req = urllib.request.Request(
        'https://api.deepseek.com/v1/chat/completions',
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {API_KEY}'},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            r = json.loads(resp.read().decode('utf-8'))
            content = r['choices'][0]['message']['content'].strip()
            if content.startswith('```'): content = content.split('\n',1)[1].rsplit('```',1)[0]
            data = json.loads(content)
            for name, bio in data.items():
                if name in p and len(bio) > 200:
                    p[name]['bio'] = bio; fixed += 1
        print(f'  {bi//BATCH+1}: {len(data)} bios ({bi+len(batch)}/{len(short)})')
    except Exception as e:
        print(f'  {bi//BATCH+1} FAIL: {e}')
    time.sleep(1)

json.dump(p, open(PHILO, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
import shutil
shutil.copy(PHILO, os.path.join(BASE, 'data', 'philosophers.json'))
print(f'\nFixed: {fixed} bios')
