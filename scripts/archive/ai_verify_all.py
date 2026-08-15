"""Agnes AI 全量肖像验证（需代理）"""
import os, sys, json, io, base64, urllib.request, re, time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(BASE, 'app', 'public', 'philosopher')
PHIL_FILE = os.path.join(BASE, 'app', 'public', 'philosophers.json')

# API key
key_path = os.path.join(os.path.expanduser('~'), '.claude', 'skills', 'image', 'scripts', 'vision.py')
with open(key_path, 'r', encoding='utf-8') as f:
    m = re.search(r'API_KEY\s*=\s*"([^"]+)"', f.read())
    API_KEY = m.group(1)

MODEL = 'agnes-2.0-flash'

with open(PHIL_FILE, 'r', encoding='utf-8') as f:
    philosophers = json.load(f)

# 构建待检列表
to_check = []
for name, data in philosophers.items():
    if not isinstance(data, dict):
        continue
    safe = name.replace('/', '-').replace('\\', '-').replace(':', '-')
    for ext in ['.jpg', '.png', '.webp']:
        fp = os.path.join(IMG_DIR, safe + ext)
        if os.path.exists(fp):
            to_check.append((name, fp, data))
            break

print(f'=== Agnes AI 全量肖像验证 ===')
print(f'待检: {len(to_check)} 张')
print(f'模型: {MODEL}')
print()

mismatches = []
errors = []
total_tokens = 0

for i, (name, img_path, data) in enumerate(to_check, 1):
    try:
        with open(img_path, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode('utf-8')
        ext = os.path.splitext(img_path)[1].lower()
        mime_map = {'.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp'}
        mime = mime_map.get(ext, 'image/webp')
        img_uri = f'data:{mime};base64,{b64}'

        prompt = (
            f'Verify: Is this image a plausible portrait of philosopher "{name}"? '
            f'Era: {data.get("era","?")}. Region: {data.get("region","?")}. '
            f'Rules: sculptures/paintings/busts OK for pre-modern. Modern photos OK for 1900+. '
            f'Flag MISMATCH if: wrong era style, wrong ethnicity, not a person, obviously wrong person. '
            f'Reply: MATCH or MISMATCH + one short reason in Chinese.'
        )

        payload = {
            'model': MODEL,
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

        with urllib.request.urlopen(req, timeout=30) as resp:
            r = json.loads(resp.read().decode('utf-8'))

        if 'error' in r:
            err = r['error'].get('message', str(r['error']))[:80]
            errors.append((name, err))
            if len(errors) <= 5:
                print(f'[{i}/{len(to_check)}] ERR {name}: {err}')
        else:
            reply = r['choices'][0]['message']['content'].strip()
            tokens = r.get('usage', {}).get('total_tokens', 0)
            total_tokens += tokens

            if reply.upper().startswith('MISMATCH'):
                mismatches.append((name, reply, img_path))
                print(f'[{i}/{len(to_check)}] MISMATCH {name}: {reply[9:].strip()}')
            elif i % 50 == 0:
                print(f'[{i}/{len(to_check)}] OK ({len(mismatches)} mismatches so far)')

    except Exception as e:
        errors.append((name, str(e)[:80]))
        if len(errors) <= 5:
            print(f'[{i}/{len(to_check)}] NET {name}: {e}')

    # 保存进度每 50 张
    if i % 50 == 0:
        with open(os.path.join(BASE, 'scripts', '_ai_progress.json'), 'w', encoding='utf-8') as f:
            json.dump({
                'checked': i, 'total': len(to_check),
                'mismatches': [(n, r) for n, r, _ in mismatches],
                'errors': errors,
                'tokens': total_tokens
            }, f, ensure_ascii=False, indent=2)

    time.sleep(0.2)  # 速率控制

# 最终报告
print(f'\n=== 验证完成 ===')
print(f'检查: {len(to_check)}')
print(f'MISMATCH: {len(mismatches)}')
print(f'错误: {len(errors)}')
print(f'Tokens: {total_tokens}')

if mismatches:
    print(f'\n--- 全部 MISMATCH ---')
    for name, reason, path in mismatches:
        print(f'  {name}: {reason[:100]}')

# 保存
report = {
    'total': len(to_check),
    'mismatches': [(n, r, os.path.basename(p)) for n, r, p in mismatches],
    'errors': errors,
    'tokens': total_tokens,
}
with open(os.path.join(BASE, 'scripts', '_ai_verify_report.json'), 'w', encoding='utf-8') as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print(f'\n报告: scripts/_ai_verify_report.json')
