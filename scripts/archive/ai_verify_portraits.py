"""Agnes AI 视觉验证哲学家肖像 —— 批量抽查图片是否与人物匹配"""
import os, sys, json, io, base64, urllib.request, time, random

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(BASE, 'app', 'public', 'philosopher')
PHIL_FILE = os.path.join(BASE, 'app', 'public', 'philosophers.json')

# ── 从根 .env 读 API 凭证（勿硬编码）──
def _load_env():
    env_path = os.path.join(BASE, '.env')
    if os.path.exists(env_path):
        for line in open(env_path, encoding='utf-8'):
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())
_load_env()

API_KEY = os.environ.get("AGNES_API_KEY", "")
MODEL = "agnes-2.5-flash"
API_URL = "https://apihub.agnes-ai.com/v1/chat/completions"

def check_image(name, img_path, era, region, school):
    """用 Agnes AI 检查肖像是否匹配"""
    with open(img_path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode('utf-8')
    img_uri = f"data:image/webp;base64,{b64}"

    prompt = (
        f"This image is supposed to be a portrait/depiction of the philosopher \"{name}\". "
        f"Era: {era}. Region: {region}. School: {school}. "
        f"Does this image plausibly represent this philosopher? Consider: "
        f"era-appropriate visual style (ancient figures may have sculptures/paintings, modern figures should have photos), "
        f"regional/ethnic plausibility, and whether it looks like ANY kind of portrait at all. "
        f"Reply with exactly one line: MATCH or MISMATCH, followed by a brief reason in Chinese."
    )

    payload = {
        'model': MODEL,
        'messages': [
            {'role': 'system', 'content': 'You verify philosopher portraits. Sculptures, paintings, busts, sketches are all valid. Flag only obviously wrong matches: wrong era style, wrong ethnicity, not a person at all, etc. Reply in Chinese.'},
            {'role': 'user', 'content': [
                {'type': 'text', 'text': prompt},
                {'type': 'image_url', 'image_url': {'url': img_uri}}
            ]}
        ],
        'temperature': 0.3, 'max_tokens': 200
    }

    req = urllib.request.Request(API_URL,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Authorization': f'Bearer {API_KEY}', 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=60) as resp:
        r = json.loads(resp.read().decode('utf-8'))
    result = r['choices'][0]['message']['content'].strip()
    tokens = r.get('usage', {}).get('total_tokens', 0)
    return result, tokens


def main():
    if not API_KEY:
        print('⚠️  AGNES_API_KEY 未设置（请在根 .env 中配置）')
        sys.exit(1)
    with open(PHIL_FILE, 'r', encoding='utf-8') as f:
        philosophers = json.load(f)

    # 构建待查列表（有图片的哲学家）
    candidates = []
    for name, data in philosophers.items():
        if not isinstance(data, dict):
            continue
        safe = name.replace('/', '-').replace('\\', '-').replace(':', '-')
        for ext in ['.jpg', '.png', '.webp']:
            fp = os.path.join(IMG_DIR, safe + ext)
            if os.path.exists(fp):
                candidates.append((name, fp, data))
                break

    # 默认抽查 30 个随机样本
    sample_size = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    if sample_size > len(candidates):
        sample_size = len(candidates)

    samples = random.sample(candidates, sample_size)

    print(f'=== AI 视觉抽查 ({sample_size}/{len(candidates)}) ===\n')

    mismatches = []
    total_tokens = 0
    match_count = 0

    for i, (name, img_path, data) in enumerate(samples, 1):
        era = data.get('era', '?')
        region = data.get('region', '?')
        school = data.get('school', '?')

        try:
            result, tokens = check_image(name, img_path, era, region, school)
            total_tokens += tokens
            verdict = result.split('\n')[0]

            if verdict.startswith('MISMATCH'):
                mismatches.append((name, era, region, result))
                print(f'[{i}/{sample_size}] MISMATCH | {name} ({era}, {region}) | {result[9:]}')
            else:
                match_count += 1
                if i % 10 == 0:
                    print(f'[{i}/{sample_size}] {match_count} MATCH, {len(mismatches)} MISMATCH so far...')
        except Exception as e:
            print(f'[{i}/{sample_size}] ERROR {name}: {e}')

        time.sleep(0.3)

    print(f'\n=== 结果 ===')
    print(f'MATCH: {match_count}')
    print(f'MISMATCH: {len(mismatches)}')
    print(f'Tokens: {total_tokens} (~${total_tokens * 0.00015:.4f})')

    if mismatches:
        print(f'\n--- MISMATCH 详情 ---')
        for name, era, region, reason in mismatches:
            print(f'  {name} ({era}, {region}): {reason}')

    # 估算全量成本
    per_img_tokens = total_tokens / sample_size if sample_size > 0 else 0
    full_cost = per_img_tokens * len(candidates) * 0.00015
    print(f'\n全量 {len(candidates)} 张估费: ~${full_cost:.2f} (~¥{full_cost*7.2:.1f})')


if __name__ == '__main__':
    main()
