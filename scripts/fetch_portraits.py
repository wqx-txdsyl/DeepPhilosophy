"""
哲学家肖像自动爬取 + AI 验证
============================
数据源优先级：
  1. Wikipedia REST API (thumbnail/original)
  2. Wikidata SPARQL (P18 image property)
  3. DBpedia (fallback)

流程：爬取 → AI验证 → 保留MATCH → 下载保存
============================
用法: python fetch_portraits.py [--replace] [--limit N]
  --replace  替换现有图片（默认只补缺失的）
  --limit N  只处理 N 张
"""
import os, sys, json, io, re, time, base64, urllib.request, urllib.parse
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(BASE, 'app', 'public', 'philosopher')
PHIL_FILE = os.path.join(BASE, 'app', 'public', 'philosophers.json')
LOG_FILE = os.path.join(BASE, 'scripts', '_fetch_portraits_log.json')

# Agnes AI
_key_path = os.path.join(os.path.expanduser("~"), ".claude", "skills", "image", "scripts", "vision.py")
AGNES_KEY = None
if os.path.exists(_key_path):
    with open(_key_path, "r", encoding="utf-8") as f:
        m = re.search(r'API_KEY\s*=\s*"([^"]+)"', f.read())
        if m: AGNES_KEY = m.group(1)

REPLACE = '--replace' in sys.argv
LIMIT = None
for i, arg in enumerate(sys.argv):
    if arg == '--limit' and i + 1 < len(sys.argv):
        LIMIT = int(sys.argv[i + 1])

os.makedirs(IMG_DIR, exist_ok=True)

def safe_fn(name):
    return name.replace('/', '-').replace('\\', '-').replace(':', '-')

# ===== 数据源 1: Wikipedia REST API =====
def wiki_search(name, lang='en'):
    """搜索 Wikipedia 获取页面摘要和图片"""
    query = urllib.parse.quote(name)
    # 先搜中文
    for l in [lang, 'zh']:
        url = f"https://{l}.wikipedia.org/api/rest_v1/page/summary/{query}"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'DeepPhilosophy/1.0'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            thumb = data.get('thumbnail', {}).get('source', '')
            original = data.get('originalimage', {}).get('source', '')
            title = data.get('title', '')
            desc = data.get('description', '')
            extract = data.get('extract', '')[:200]
            if thumb:
                return {
                    'source': 'wikipedia',
                    'title': title,
                    'description': desc,
                    'thumbnail': thumb,
                    'original': original,
                    'lang': l,
                    'extract': extract
                }
        except urllib.error.HTTPError as e:
            if e.code != 404:
                pass  # silent for 404
        except Exception:
            pass
    return None

# ===== 数据源 2: Wikidata SPARQL =====
def wikidata_image(name, lang='en'):
    """从 Wikidata 查询 P18 (image)"""
    # Wikidata 的搜索使用 wbsearchentities
    query = urllib.parse.quote(name)
    url = f"https://www.wikidata.org/w/api.php?action=wbsearchentities&search={query}&language={lang}&format=json&limit=3"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'DeepPhilosophy/1.0'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))

        for result in data.get('search', []):
            qid = result['id']
            # 获取实体详情
            detail_url = f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json"
            req2 = urllib.request.Request(detail_url, headers={'User-Agent': 'DeepPhilosophy/1.0'})
            with urllib.request.urlopen(req2, timeout=10) as resp2:
                entity = json.loads(resp2.read().decode('utf-8'))

            claims = entity.get('entities', {}).get(qid, {}).get('claims', {})
            if 'P18' in claims:
                # 提取图片文件名
                img_name = claims['P18'][0]['mainsnak']['datavalue']['value']
                # 转换 Commons URL
                img_name_enc = img_name.replace(' ', '_')
                img_hash = hashlib.md5(img_name_enc.encode()).hexdigest()
                commons_url = f"https://upload.wikimedia.org/wikipedia/commons/{img_hash[0]}/{img_hash[0:2]}/{urllib.parse.quote(img_name_enc)}"
                return {
                    'source': 'wikidata',
                    'qid': qid,
                    'label': result.get('label', ''),
                    'description': result.get('description', ''),
                    'image': commons_url
                }

    except Exception:
        pass
    return None


# ===== AI 验证 =====
def ai_verify_portrait(name, img_url, era='', region='', school=''):
    """用 Agnes AI 验证图片是否匹配哲学家"""
    if not AGNES_KEY:
        return {'verdict': 'SKIP', 'reason': 'no_api_key'}

    prompt = (
        f'Verify: Is this image a plausible portrait of philosopher "{name}"? '
        f'Era: {era}. Region: {region}. '
        f'Answer: MATCH or MISMATCH + one short reason in Chinese.'
    )

    payload = {
        'model': 'agnes-2.0-flash',
        'messages': [{'role': 'user', 'content': [
            {'type': 'text', 'text': prompt},
            {'type': 'image_url', 'image_url': {'url': img_url}}
        ]}],
        'temperature': 0.3, 'max_tokens': 150
    }

    try:
        req = urllib.request.Request(
            'https://apihub.agnes-ai.com/v1/chat/completions',
            data=json.dumps(payload).encode('utf-8'),
            headers={'Authorization': f'Bearer {AGNES_KEY}', 'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            r = json.loads(resp.read().decode('utf-8'))
        if 'error' in r:
            return {'verdict': 'API_ERROR', 'reason': r['error'].get('message', '')[:80]}
        reply = r['choices'][0]['message']['content'].strip()
        return {'verdict': 'MATCH' if reply.upper().startswith('MATCH') else 'MISMATCH', 'reply': reply}
    except Exception as e:
        return {'verdict': 'NET_ERROR', 'reason': str(e)[:80]}


# ===== 下载图片 =====
def download_image(url, filepath):
    """下载并保存图片"""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'DeepPhilosophy/1.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        if len(data) < 1000:
            return False
        with open(filepath, 'wb') as f:
            f.write(data)
        return os.path.getsize(filepath) > 1000
    except Exception:
        return False


# ===== 主流程 =====
def main():
    import hashlib  # 用于 wikidata 图片 URL 计算

    print("=" * 60)
    print("哲学家肖像爬取 + AI 验证")
    print(f"替换模式: {REPLACE} | 限制: {LIMIT or '全部'}")
    print("=" * 60)

    with open(PHIL_FILE, 'r', encoding='utf-8') as f:
        philosophers = json.load(f)

    # 确定待处理列表
    todo = []
    for name, data in philosophers.items():
        if not isinstance(data, dict):
            continue
        safe = safe_fn(name)
        has_img = any(os.path.exists(os.path.join(IMG_DIR, f'{safe}{ext}')) for ext in ['.jpg', '.png', '.webp'])
        if REPLACE or not has_img:
            todo.append((name, data))

    print(f"待处理: {len(todo)}/{len(philosophers)}")

    log = {'found': [], 'verified_ok': [], 'verified_bad': [], 'failed': [], 'skipped': []}

    count = 0
    for i, (name, data) in enumerate(todo, 1):
        if LIMIT and count >= LIMIT:
            break

        era = data.get('era', '')
        region = data.get('region', '')
        school = data.get('school', '')
        print(f"\n[{i}/{len(todo)}] {name} ({era})")

        # 1. 尝试 Wikipedia
        result = wiki_search(name)
        if not result:
            # 尝试 Wikidata
            print("  Wiki: 未找到, 试 Wikidata...")
            result = wikidata_image(name)

        if not result:
            print(f"  => 无结果")
            log['failed'].append({'name': name, 'reason': 'no_results'})
            continue

        img_url = result.get('original') or result.get('image') or result.get('thumbnail')
        if not img_url:
            print(f"  => 无图片")
            log['failed'].append({'name': name, 'reason': 'no_image'})
            continue

        print(f"  源: {result['source']} | {result.get('title', result.get('label', ''))} ")
        print(f"  图: {img_url[:100]}...")

        # 2. AI 验证
        print(f"  AI 验证中...", end=' ', flush=True)
        verify = ai_verify_portrait(name, img_url, era, region, school)
        print(verify['verdict'])

        if verify['verdict'] == 'MATCH':
            # 3. 下载
            safe = safe_fn(name)
            ext = os.path.splitext(img_url.split('?')[0])[1] or '.jpg'
            if ext not in ('.jpg', '.jpeg', '.png', '.webp'):
                ext = '.jpg'
            filepath = os.path.join(IMG_DIR, f'{safe}{ext}')
            print(f"  下载中...", end=' ', flush=True)
            if download_image(img_url, filepath):
                size_kb = round(os.path.getsize(filepath) / 1024, 1)
                print(f"OK ({size_kb}KB)")
                log['verified_ok'].append({'name': name, 'source': result['source'], 'url': img_url, 'file': f'{safe}{ext}', 'size_kb': size_kb})
                count += 1
            else:
                print("FAIL (下载失败)")
                log['failed'].append({'name': name, 'reason': 'download_failed', 'url': img_url})
        else:
            print(f"  => 验证不通过: {verify.get('reply', verify.get('reason', ''))[:80]}")
            log['verified_bad'].append({
                'name': name, 'verdict': verify['verdict'],
                'reason': verify.get('reply', verify.get('reason', '')),
                'url': img_url
            })

        # 保存日志
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(log, f, ensure_ascii=False, indent=2)

        time.sleep(0.3)

    print(f"\n=== 完成 ===")
    print(f"成功: {len(log['verified_ok'])}")
    print(f"AI 拒绝: {len(log['verified_bad'])}")
    print(f"失败: {len(log['failed'])}")
    print(f"日志: {LOG_FILE}")


if __name__ == '__main__':
    import hashlib
    main()
