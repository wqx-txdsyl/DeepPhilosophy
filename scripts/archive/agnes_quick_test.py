"""快速测试 Agnes AI + 代理"""
import os, sys, json, io, base64, urllib.request, re

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

key_path = os.path.join(os.path.expanduser('~'), '.claude', 'skills', 'image', 'scripts', 'vision.py')
with open(key_path, 'r', encoding='utf-8') as f:
    m = re.search(r'API_KEY\s*=\s*"([^"]+)"', f.read())
    API_KEY = m.group(1)

IMG_DIR = 'app/public/philosopher'

with open('app/public/philosophers.json', 'r', encoding='utf-8') as f:
    p = json.load(f)

# 测试几张 L4 标出的可疑图
suspects = ['摩西', '仁钦·乔玛', '卡蒂尼', '维雷杜·维雷杜', '瓦曼·波马·德·阿亚拉']

for name in suspects:
    if name not in p:
        print(f'{name}: not found')
        continue
    data = p[name]
    safe = name.replace('/', '-').replace('\\', '-').replace(':', '-')
    fp = None
    for ext in ['.jpg', '.png', '.webp']:
        candidate = os.path.join(IMG_DIR, safe + ext)
        if os.path.exists(candidate):
            fp = candidate
            break
    if not fp:
        print(f'{name}: no image')
        continue

    with open(fp, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode('utf-8')
    img_uri = f'data:image/webp;base64,{b64}'

    prompt = (
        f'This image is labeled as a portrait of philosopher "{name}" '
        f'(era: {data.get("era","")}, region: {data.get("region","")}). '
        f'Verify: plausible? Consider era-appropriate medium and regional plausibility. '
        f'Reply: MATCH or MISMATCH + one short reason in Chinese.'
    )

    payload = {
        'model': 'agnes-2.0-flash',
        'messages': [{'role': 'user', 'content': [
            {'type': 'text', 'text': prompt},
            {'type': 'image_url', 'image_url': {'url': img_uri}}
        ]}],
        'temperature': 0.3, 'max_tokens': 200
    }

    req = urllib.request.Request(
        'https://apihub.agnes-ai.com/v1/chat/completions',
        data=json.dumps(payload).encode('utf-8'),
        headers={'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'}
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            r = json.loads(resp.read().decode('utf-8'))
            if 'error' in r:
                print(f'{name}: API_ERROR {r["error"].get("message", r["error"])[:80]}')
            else:
                reply = r['choices'][0]['message']['content']
                tokens = r.get('usage', {}).get('total_tokens', 0)
                print(f'{name}: {reply} ({tokens}t)')
    except Exception as e:
        print(f'{name}: NET_ERR {e}')
