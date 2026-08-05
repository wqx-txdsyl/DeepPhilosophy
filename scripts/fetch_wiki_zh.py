"""中文维基百科图片爬取 —— 走代理"""
import os, sys, json, io, re, time, urllib.request, urllib.error
from PIL import Image

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(BASE, 'app', 'public', 'philosopher')
PHIL_FILE = os.path.join(BASE, 'app', 'public', 'philosophers.json')

PROXY = 'http://127.0.0.1:12450'
os.environ['HTTPS_PROXY'] = PROXY
os.environ['HTTP_PROXY'] = PROXY

UA = 'DeepPhilosophy/1.0 (philosophy database project)'

def safe_fn(name):
    return name.replace('/', '-').replace('\\', '-').replace(':', '-')

def wiki_api_call(url, use_proxy=True, retries=3):
    """带重试的 API 调用"""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=10) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = (attempt + 1) * 10
                print(f'(429等{wait}s)', end=' ', flush=True)
                time.sleep(wait)
            else:
                return None
        except Exception:
            if attempt == retries - 1:
                return None
            time.sleep(3)
    return None


def wiki_search(name, use_proxy=True):
    """搜索维基百科（中/英），返回 pageids"""
    query = urllib.parse.quote(name)
    lang = 'zh' if use_proxy else 'en'
    url = f'https://{lang}.wikipedia.org/w/api.php?action=query&list=search&srsearch={query}&format=json&srlimit=2'

    # 英文不需要代理
    if not use_proxy:
        orig_http = os.environ.pop('HTTP_PROXY', None)
        orig_https = os.environ.pop('HTTPS_PROXY', None)

    data = wiki_api_call(url)

    if not use_proxy:
        if orig_http: os.environ['HTTP_PROXY'] = orig_http
        if orig_https: os.environ['HTTPS_PROXY'] = orig_https

    if not data:
        return []
    return [r['pageid'] for r in data.get('query', {}).get('search', [])]


def wiki_page_image(pageid, use_proxy=True):
    """获取页面主图"""
    lang = 'zh' if use_proxy else 'en'
    url = f'https://{lang}.wikipedia.org/w/api.php?action=query&prop=pageimages&pageids={pageid}&piprop=original&format=json'

    if not use_proxy:
        orig_http = os.environ.pop('HTTP_PROXY', None)
        orig_https = os.environ.pop('HTTPS_PROXY', None)

    data = wiki_api_call(url)

    if not use_proxy:
        if orig_http: os.environ['HTTP_PROXY'] = orig_http
        if orig_https: os.environ['HTTPS_PROXY'] = orig_https

    if not data:
        return None, None
    pages = data.get('query', {}).get('pages', {})
    page = pages.get(str(pageid), {})
    original = page.get('original', {}).get('source', '')
    title = page.get('title', '')
    return original or None, title
    """中文维基搜索 → 返回 pageid 列表"""
    query = urllib.parse.quote(name)
    url = f'https://zh.wikipedia.org/w/api.php?action=query&list=search&srsearch={query}&format=json&srlimit=3'
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode('utf-8'))
            return [r['pageid'] for r in data.get('query', {}).get('search', [])]
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = (attempt + 1) * 5
                print(f'(429等{wait}s)', end=' ', flush=True)
                time.sleep(wait)
            else:
                return []
        except Exception:
            return []
    return []


def download_save(img_url, filepath):
    """下载图片 → 转 WebP → 保存"""
    try:
        req = urllib.request.Request(img_url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
        if len(data) < 2000:
            return False, 'too_small'

        img = Image.open(io.BytesIO(data))
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        w, h = img.size
        if w > 800 or h > 800:
            ratio = 800 / max(w, h)
            img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)

        webp_path = filepath.rsplit('.', 1)[0] + '.webp'
        img.save(webp_path, 'WebP', quality=80)
        return True, round(os.path.getsize(webp_path) / 1024, 1)
    except Exception as e:
        return False, str(e)[:50]


# ===== 主流程 =====
with open(PHIL_FILE, 'r', encoding='utf-8') as f:
    philosophers = json.load(f)

missing = []
for name, data in philosophers.items():
    if not isinstance(data, dict):
        continue
    fn = safe_fn(name)
    if not any(os.path.exists(os.path.join(IMG_DIR, fn + e)) for e in ['.jpg', '.png', '.webp']):
        missing.append((name, data))

missing.sort(key=lambda x: x[1].get('rank', 0), reverse=True)
print(f'缺图: {len(missing)}/{len(philosophers)}')
print(f'代理: {PROXY}')
print()

success = 0
for i, (name, data) in enumerate(missing, 1):
    rank = data.get('rank', 0)
    print(f'[{i}/{len(missing)}] {name} (rank={rank})', end=' ', flush=True)

    # 1. 先试英文维基（不需要代理，不限流）
    img_url, page_title = None, None
    en_ids = wiki_search(name, use_proxy=False)
    if en_ids:
        img_url, page_title = wiki_page_image(en_ids[0], use_proxy=False)

    # 2. 英文没图，试中文维基（走代理）
    if not img_url:
        zh_ids = wiki_search(name, use_proxy=True)
        if zh_ids:
            img_url, page_title = wiki_page_image(zh_ids[0], use_proxy=True)

    if not img_url:
        print('→ 无图')
        continue

    print(f'→ {page_title}', end=' ', flush=True)

    # 3. 下载
    fn = safe_fn(name)
    filepath = os.path.join(IMG_DIR, fn + '.tmp')
    ok, info = download_save(img_url, filepath)
    if ok:
        print(f'OK ({info}KB)')
        success += 1
    else:
        print(f'FAIL: {info}')

    time.sleep(3)

remaining = sum(1 for n in philosophers if not any(
    os.path.exists(os.path.join(IMG_DIR, safe_fn(n) + e)) for e in ['.jpg', '.png', '.webp']
))
print(f'\n成功: {success}  剩余缺图: {remaining}/{len(philosophers)}')
