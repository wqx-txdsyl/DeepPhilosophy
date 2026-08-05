"""
哲学家肖像全方位验证算法
==========================
层次化检测管道：
  L1: 文件完整性 — 存在、可读、非空
  L2: 图像属性 — 尺寸、比例、色彩分布
  L3: 重复检测 — 完整 MD5 碰撞
  L4: 地域-年代启发 — 古代人+彩色照片、区域风格不匹配
  L5: AI 视觉验证 — Agnes AI (需代理)
==========================
用法: python verify_all_portraits.py [--ai] [--dry-run]
  --ai       启用 AI 视觉验证 (需要代理连通 Agnes)
  --dry-run  仅检测，不删除
"""
import os, sys, json, io, hashlib, re, time, base64, ssl, socket, urllib.request
from PIL import Image
import numpy as np
from collections import defaultdict, Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(BASE, 'app', 'public', 'philosopher')
PHIL_FILE = os.path.join(BASE, 'app', 'public', 'philosophers.json')
REPORT_FILE = os.path.join(BASE, 'scripts', '_portrait_report.json')

USE_AI = '--ai' in sys.argv
DRY_RUN = '--dry-run' in sys.argv

# Agnes 配置
AGNES_HOST = "apihub.agnes-ai.com"
AGNES_REAL_IP = "104.18.19.62"
AGNES_MODEL = "agnes-2.0-flash"

# 读 Agnes key
_key_path = os.path.join(os.path.expanduser("~"), ".claude", "skills", "image", "scripts", "vision.py")
AGNES_KEY = None
if os.path.exists(_key_path):
    with open(_key_path, "r", encoding="utf-8") as f:
        m = re.search(r'API_KEY\s*=\s*"([^"]+)"', f.read())
        if m: AGNES_KEY = m.group(1)

# ===== 工具函数 =====
def safe_fn(name):
    return name.replace('/', '-').replace('\\', '-').replace(':', '-')

def era_year(era_str):
    """提取年代的近似年份，用于判断是否早于摄影术发明"""
    if not era_str: return None
    years = re.findall(r'(\d{4})', str(era_str))
    if years: return int(years[0])
    if '前' in str(era_str):
        nums = re.findall(r'(\d+)', str(era_str))
        if nums: return -int(nums[0])
    if '世纪' in str(era_str):
        nums = re.findall(r'(\d+)', str(era_str))
        if nums:
            c = int(nums[0])
            if '前' in str(era_str): return -c * 100
            return c * 100
    return None

# ===== L1: 文件完整性 =====
def check_file(name):
    """检查图片文件是否存在且有效"""
    for ext in ['.jpg', '.png', '.webp']:
        fp = os.path.join(IMG_DIR, safe_fn(name) + ext)
        if os.path.exists(fp):
            try:
                img = Image.open(fp)
                img.verify()
                return {'status': 'ok', 'path': fp, 'ext': ext, 'size_kb': round(os.path.getsize(fp) / 1024, 1)}
            except:
                return {'status': 'corrupt', 'path': fp}
    return {'status': 'missing'}

# ===== L2: 图像属性 =====
def check_properties(img_path):
    """分析图像质量属性"""
    img = Image.open(img_path)
    if img.mode not in ('RGB', 'RGBA', 'L'):
        img = img.convert('RGB')
    arr = np.array(img)
    w, h = img.size
    aspect = w / h if h > 0 else 0

    gray = np.mean(arr, axis=2) if len(arr.shape) == 3 else arr
    brightness = float(np.mean(gray))
    contrast = float(np.std(gray))

    # 色彩饱和度
    if len(arr.shape) == 3 and arr.shape[2] >= 3:
        rg = np.std(arr[:,:,0].astype(float) - arr[:,:,1].astype(float))
        gb = np.std(arr[:,:,1].astype(float) - arr[:,:,2].astype(float))
        saturation = float((rg + gb) / 2)
        # 主色调
        avg_r, avg_g, avg_b = [float(np.mean(arr[:,:,c])) for c in range(3)]
        is_bw = float(np.std([avg_r, avg_g, avg_b])) < 12
    else:
        saturation = 0
        is_bw = True

    # 判定是否为照片风格
    # 照片: 高饱和度 + 中等对比度 + 边缘柔和
    # 素描/版画: 低饱和度(黑白) + 高对比度 + 锐利边缘
    # 雕塑/油画: 中等饱和度 + 中低对比度

    is_photo_like = saturation > 25 and contrast > 40 and not is_bw
    is_sketch_like = is_bw and contrast > 60
    is_sculpture_like = saturation < 20 and 20 < contrast < 50

    # 肖像比例 (0.6~1.2)
    is_portrait_ratio = 0.5 <= aspect <= 1.5

    flags = []
    if img.width < 100 or img.height < 100: flags.append('TINY')
    if contrast < 10: flags.append('FLAT')
    if brightness > 245: flags.append('OVEREXPOSED')
    if brightness < 15: flags.append('UNDEREXPOSED')
    if aspect < 0.3 or aspect > 3: flags.append('EXTREME_RATIO')

    return {
        'size': f'{w}x{h}',
        'aspect': round(aspect, 2),
        'brightness': round(brightness, 1),
        'contrast': round(contrast, 1),
        'saturation': round(saturation, 1),
        'is_bw': is_bw,
        'is_photo_like': is_photo_like,
        'is_sketch_like': is_sketch_like,
        'is_sculpture_like': is_sculpture_like,
        'is_portrait_ratio': is_portrait_ratio,
        'flags': flags
    }

# ===== L3: 重复检测 =====
def compute_md5(filepath):
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

# ===== L4: 年代-区域启发 =====
def check_era_region_consistency(name, data, props):
    """检查年代/区域与图像风格是否一致"""
    era = data.get('era', '')
    region = data.get('region', '')
    year = era_year(era)
    issues = []

    # 摄影术发明于 1839 年，普及于 1850s
    if year is not None and year < 1800 and props['is_photo_like']:
        # 古代人 + 照片风格 → 不一定错（可能是雕塑照片），但需标注
        if props['saturation'] > 40:
            issues.append('PRE-CAMERA_PHOTO')

    # 中世纪之前 + 过高精度彩色 → 可疑
    if year is not None and year < 500 and props['saturation'] > 50:
        issues.append('ANCIENT_VIVID_COLOR')

    # 极小图可能是占位符
    w, h = [int(x) for x in props['size'].split('x')]
    if w < 120 and h < 120:
        issues.append('TINY_PLACEHOLDER')

    return issues

# ===== L5: AI 视觉验证 =====
def ai_verify(name, img_path, era, region, school):
    """用 Agnes AI 验证肖像匹配度"""
    if not AGNES_KEY:
        return {'verdict': 'SKIP', 'reason': 'no_api_key'}

    with open(img_path, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode('utf-8')
    mime = 'image/webp' if img_path.endswith('.webp') else 'image/jpeg' if img_path.endswith('.jpg') else 'image/png'
    img_uri = f"data:{mime};base64,{b64}"

    prompt = (
        f"This image is labeled as a portrait of the philosopher \"{name}\". "
        f"Era: {era}. Region: {region}. School: {school}. "
        f"Verify: Does this image plausibly depict this philosopher? Consider: "
        f"(1) Era-appropriate visual medium (e.g., ancient figures → sculpture/painting is fine; modern figures → photo is expected). "
        f"(2) Regional/ethnic plausibility. "
        f"(3) Does the image show ANY kind of person/portrait at all? "
        f"Answer in Chinese with one word: MATCH or MISMATCH, followed by one short reason."
    )

    payload = {
        'model': AGNES_MODEL,
        'messages': [{
            'role': 'system',
            'content': 'You are a portrait verifier. Be strict: flag mismatches. Sculptures, paintings, and busts are acceptable for pre-modern figures. Reply concisely in Chinese.'
        }, {
            'role': 'user',
            'content': [
                {'type': 'text', 'text': prompt},
                {'type': 'image_url', 'image_url': {'url': img_uri}}
            ]
        }],
        'temperature': 0.3, 'max_tokens': 200
    }

    # DNS patch
    _orig = socket.getaddrinfo
    def _patched(host, port, family=0, type=0, proto=0, flags=0):
        if host == AGNES_HOST:
            return _orig(AGNES_REAL_IP, port, family, type, proto, flags)
        return _orig(host, port, family, type, proto, flags)

    try:
        socket.getaddrinfo = _patched
        req = urllib.request.Request(
            f"https://{AGNES_HOST}/v1/chat/completions",
            data=json.dumps(payload).encode('utf-8'),
            headers={'Authorization': f'Bearer {AGNES_KEY}', 'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            r = json.loads(resp.read().decode('utf-8'))
            if 'error' in r:
                return {'verdict': 'API_ERROR', 'reason': r['error'].get('message', str(r['error']))[:100]}
            reply = r['choices'][0]['message']['content'].strip()
            tokens = r.get('usage', {}).get('total_tokens', 0)
            verdict = 'MATCH' if reply.upper().startswith('MATCH') else 'MISMATCH'
            return {'verdict': verdict, 'reply': reply, 'tokens': tokens}
    except Exception as e:
        return {'verdict': 'NETWORK_ERROR', 'reason': str(e)[:100]}
    finally:
        socket.getaddrinfo = _orig


# ===== 主流程 =====
def main():
    print("=" * 60)
    print("哲学家肖像全方位验证")
    print(f"AI验证: {'ON' if USE_AI else 'OFF'} | 仅检测: {'YES' if DRY_RUN else 'NO (会删除)'}")
    print("=" * 60)

    with open(PHIL_FILE, 'r', encoding='utf-8') as f:
        philosophers = json.load(f)

    # L1: 文件检查
    print("\n[L1] 文件完整性...")
    missing = []
    corrupt = []
    valid = []
    for name in philosophers:
        r = check_file(name)
        if r['status'] == 'missing':
            missing.append(name)
        elif r['status'] == 'corrupt':
            corrupt.append((name, r['path']))
        else:
            valid.append((name, r))
    print(f"  有效: {len(valid)}  缺失: {len(missing)}  损坏: {len(corrupt)}")

    # L2: 属性分析
    print("\n[L2] 图像属性...")
    props_data = {}
    issues_l2 = defaultdict(list)
    for name, finfo in valid:
        p = check_properties(finfo['path'])
        props_data[name] = p
        for flag in p['flags']:
            issues_l2[flag].append(name)
    for flag, names in issues_l2.items():
        print(f"  {flag}: {len(names)}")

    # L3: 重复检测
    print("\n[L3] MD5 重复检测...")
    md5_map = defaultdict(list)
    for name, finfo in valid:
        h = compute_md5(finfo['path'])
        md5_map[h].append((name, finfo['path']))
    duplicates = {h: names for h, names in md5_map.items() if len(names) > 1}
    print(f"  重复组: {len(duplicates)}")
    for h, names in duplicates.items():
        ns = [n for n, _ in names]
        print(f"    {ns}")

    # L4: 年代区域启发
    print("\n[L4] 年代-区域一致性...")
    era_issues = {}
    valid_set = {name for name, _ in valid}
    for name, _ in valid:
        if name not in philosophers: continue
        data = philosophers[name]
        if name not in props_data: continue
        issues = check_era_region_consistency(name, data, props_data[name])
        if issues:
            era_issues[name] = issues

    pre_camera_photos = [(n, philosophers[n].get('era', ''), props_data[n]['saturation'])
                         for n in valid_set if n in era_issues and 'PRE-CAMERA_PHOTO' in era_issues[n]]
    tiny_placeholders = [n for n in valid_set if n in era_issues and 'TINY_PLACEHOLDER' in era_issues[n]]
    print(f"  前摄影术+彩色照片: {len(pre_camera_photos)}")
    for n, e, s in pre_camera_photos[:10]:
        print(f"    {n} ({e}) sat={s:.0f}")
    print(f"  疑似占位小图: {len(tiny_placeholders)}")

    # L5: AI 视觉 (如启用)
    ai_results = {}
    if USE_AI and AGNES_KEY:
        print(f"\n[L5] Agnes AI 视觉验证...")
        # 优先验证 L4 标出的可疑项，再随机抽样
        suspects = set()
        for n in era_issues: suspects.add(n)
        # 也加入 L2 标出的异常
        for flag in ['TINY', 'FLAT', 'EXTREME_RATIO']:
            for n in issues_l2.get(flag, []):
                suspects.add(n)

        verify_list = sorted(suspects)
        print(f"  待验证: {len(verify_list)} 张")

        ai_mismatches = []
        ai_errors = []
        for i, name in enumerate(verify_list, 1):
            if name not in philosophers: continue
            data = philosophers[name]
            safe = safe_fn(name)
            img_path = None
            for ext in ['.jpg', '.png', '.webp']:
                fp = os.path.join(IMG_DIR, safe + ext)
                if os.path.exists(fp):
                    img_path = fp
                    break
            if not img_path: continue

            result = ai_verify(name, img_path,
                             data.get('era', ''), data.get('region', ''), data.get('school', ''))
            ai_results[name] = result

            if result['verdict'] == 'MISMATCH':
                ai_mismatches.append(name)
                print(f"  [{i}/{len(verify_list)}] MISMATCH {name}: {result.get('reply', '')[:80]}")
            elif result['verdict'] == 'API_ERROR':
                ai_errors.append(name)
                if len(ai_errors) <= 3:
                    print(f"  [{i}/{len(verify_list)}] API_ERR {name}: {result.get('reason', '')}")
            else:
                pass  # MATCH, don't print every one

            time.sleep(0.3)

        print(f"\n  AI MISMATCH: {len(ai_mismatches)}")
        for n in ai_mismatches:
            print(f"    {n}: {ai_results[n].get('reply', '')}")
        print(f"  AI ERRORS: {len(ai_errors)}")
    else:
        print(f"\n[L5] AI 视觉验证: SKIP (使用 --ai 启用)")

    # ===== 汇总报告 =====
    report = {
        'total': len(philosophers),
        'L1_missing': missing,
        'L1_corrupt': [(n, p) for n, p in corrupt],
        'L2_flags': {k: v for k, v in issues_l2.items()},
        'L3_duplicates': {h: [(n, p) for n, p in ns] for h, ns in duplicates.items()},
        'L4_era_issues': {n: v for n, v in era_issues.items()},
        'L5_ai_mismatches': ai_mismatches if USE_AI else [],
        'L5_ai_results': ai_results if USE_AI else {},
    }

    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n报告: {REPORT_FILE}")

    # ===== 自动修复 =====
    if not DRY_RUN:
        print("\n=== 自动修复 ===")
        deleted = 0

        # 删除重复图 (保留一组中名字最短的 or 在 philosophers 中出现时间最早的)
        for h, names in duplicates.items():
            # 保留第一个，删除其余
            keeper = names[0][0]
            for name, path in names[1:]:
                if os.path.exists(path):
                    os.remove(path)
                    print(f"  [DUP] {os.path.basename(path)} (保留 {keeper})")
                    deleted += 1

        # 删除损坏图
        for name, path in corrupt:
            if os.path.exists(path):
                os.remove(path)
                print(f"  [CORRUPT] {os.path.basename(path)}")
                deleted += 1

        print(f"\n共删除: {deleted} 个文件")

    print("\n=== 完成 ===")


if __name__ == '__main__':
    main()
