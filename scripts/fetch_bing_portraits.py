"""Bing 图片搜索 → 下载 → 转 WebP"""
import os, sys, json, io, re, time, urllib.request, urllib.parse
from PIL import Image

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(BASE, 'app', 'public', 'philosopher')
PHIL_FILE = os.path.join(BASE, 'app', 'public', 'philosophers.json')

os.makedirs(IMG_DIR, exist_ok=True)

def safe_fn(name):
    return name.replace('/', '-').replace('\\', '-').replace(':', '-')

def bing_search(name, data, count=8):
    """搜索 Bing 图片，使用增强关键词 + 来源过滤"""
    era = data.get('era', '') if isinstance(data, dict) else ''
    region = data.get('region', '') if isinstance(data, dict) else ''

    # 增强搜索词：加上"哲学家 肖像 画像"约束
    # 提取年代数字辅助搜索
    import re as _re
    year_match = _re.search(r'(\d{4})', str(era))
    century_hint = f'{int(year_match.group(1)[:2])+1}世纪' if year_match else ''

    terms = [name, '哲学家']
    if '前' in str(era) or (year_match and int(year_match.group(1)) < 1800):
        terms.append('雕像 OR 画像 OR 肖像')  # 古代人偏好雕塑画像
    else:
        terms.append('肖像 OR 照片')  # 近现代人可以有照片
    if century_hint:
        terms.append(century_hint)

    query = urllib.parse.quote(' '.join(terms))
    url = f'https://cn.bing.com/images/async?q={query}&first=1&count={count}'
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8', errors='replace')
    except Exception:
        return []

    # 提取 murl
    murls = _re.findall(r'murl&quot;:&quot;(https?://[^&]+?\.(?:jpg|png|jpeg|webp)[^&\"]*)', html)

    # 来源黑名单：体育、娱乐、新闻等无关站点
    bad_domains = [
        'sports', 'sport', 'football', 'basketball', 'nba', 'fifa',
        'sinaimg.cn/sinakd', 'sinaimg.cn/sports', 'weibo', 'tieba',
        'sohucs.com/sports', 'qq.com/sports', 'hupu', 'zhibo8',
        'news', 'entertainment', 'movie', 'film', 'music', 'pop',
        'toutiao', 'kuaibao', 'ifengimg.com/pmop',  # 新闻类
        'sina.com.cn/ent', 'sina.com.cn/star',
        'img1.gtimg.com/sports', 'img1.gtimg.com/ent',
        '163.com/sports', '163.com/ent',
    ]
    # 来源白名单：学术、百科、文化类优先
    good_domains = [
        'wikimedia', 'wikipedia', 'zhimg.com', 'zhihu',
        'douban', 'baidu.com/hi', 'baike',
        'bcebos.com', 'bdimg.com',  # 百度系
        'lifeweek', 'ptext.nju.edu', 'cafamuseum',
        'philosophy', 'phil', 'academia', 'edu',
        'britannica', 'stanford', 'iep.utm',
    ]

    clean = []
    for u in murls:
        u = u.replace('\\/', '/')
        # 过滤缩略图
        if '80x80' in u or 'icon' in u.lower() or 'avatar' in u.lower():
            continue
        # 过滤来源
        u_lower = u.lower()
        if any(b in u_lower for b in bad_domains):
            continue
        if u not in clean:
            clean.append(u)

    if not clean:
        return []

    # 优先白名单来源
    good = [u for u in clean if any(g in u.lower() for g in good_domains)]
    bad = [u for u in clean if u not in good]
    return (good + bad)[:count]


def download_and_convert(url, filepath):
    """下载图片并转为 WebP"""
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Referer': 'https://cn.bing.com/'
        })
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
        if len(data) < 2000:
            return False, 'too_small'

        # 转 WebP
        img = Image.open(io.BytesIO(data))
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        # 限制最大尺寸
        w, h = img.size
        max_dim = 800
        if w > max_dim or h > max_dim:
            ratio = max_dim / max(w, h)
            img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)

        webp_path = filepath.rsplit('.', 1)[0] + '.webp'
        img.save(webp_path, 'WebP', quality=80)
        size_kb = round(os.path.getsize(webp_path) / 1024, 1)
        return True, size_kb
    except Exception as e:
        return False, str(e)[:50]


# ===== 主流程 =====
with open(PHIL_FILE, 'r', encoding='utf-8') as f:
    philosophers = json.load(f)

# 找缺图的
missing = []
for name, data in philosophers.items():
    if not isinstance(data, dict):
        continue
    fn = safe_fn(name)
    has = any(os.path.exists(os.path.join(IMG_DIR, fn + e)) for e in ['.jpg', '.png', '.webp'])
    if not has:
        missing.append((name, data))

# 清理上次残留的 .tmp 文件
for f in os.listdir(IMG_DIR):
    if f.endswith('.tmp'):
        os.remove(os.path.join(IMG_DIR, f))
        print(f'[清理] {f}')

missing.sort(key=lambda x: x[1].get('rank', 0) if isinstance(x[1], dict) else 0, reverse=True)
print(f'缺图: {len(missing)}/{len(philosophers)}')
print()

success = 0
for i, (name, data) in enumerate(missing, 1):
    rank = data.get('rank', 0) if isinstance(data, dict) else 0
    print(f'[{i}/{len(missing)}] {name} (rank={rank})', end=' ', flush=True)

    urls = bing_search(name, data)
    if not urls:
        print('→ 无结果')
        continue

    # 逐个尝试 URL
    fn = safe_fn(name)
    filepath = os.path.join(IMG_DIR, fn + '.tmp')
    ok = False
    for url in urls:
        ok, info = download_and_convert(url, filepath)
        if ok:
            print(f'→ OK ({info}KB)')
            success += 1
            break

    if not ok:
        print(f'→ FAIL: {info}')

    time.sleep(1)  # Bing 限速

# 统计
remaining = sum(1 for n in philosophers if not any(
    os.path.exists(os.path.join(IMG_DIR, safe_fn(n) + e)) for e in ['.jpg', '.png', '.webp']
))
print(f'\n成功: {success}  剩余缺图: {remaining}/{len(philosophers)}')
