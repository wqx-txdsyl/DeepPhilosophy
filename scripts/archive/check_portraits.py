"""哲学家肖像校验：图像属性检测 + 异常标记"""
import os, sys, json, io, re, hashlib
from PIL import Image, ImageStat
import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(BASE, 'app', 'public', 'philosopher')
PHIL_FILE = os.path.join(BASE, 'app', 'public', 'philosophers.json')

def analyze_image(img_path):
    """综合分析一张肖像图"""
    try:
        img = Image.open(img_path)
    except Exception as e:
        return {'valid': False, 'reason': f'cant_open: {e}'}

    w, h = img.size
    if w < 30 or h < 30:
        return {'valid': False, 'reason': f'too_small', 'size': (w, h)}

    # 文件大小
    file_size = os.path.getsize(img_path)

    # 宽高比（肖像照通常 0.6~1.0）
    aspect = w / h if h > 0 else 0
    is_portrait = 0.5 <= aspect <= 1.5

    # 转为 RGB
    if img.mode not in ('RGB', 'RGBA', 'L'):
        img = img.convert('RGB')
    arr = np.array(img)

    # 灰度统计
    if len(arr.shape) == 3:
        gray = np.mean(arr, axis=2)
    else:
        gray = arr

    brightness = float(np.mean(gray))
    contrast = float(np.std(gray))

    # 颜色饱和度 (RGB 通道间差异)
    if len(arr.shape) == 3 and arr.shape[2] >= 3:
        channel_std = float(np.mean([np.std(arr[:,:,c]) for c in range(min(3, arr.shape[2]))]))
    else:
        channel_std = 0

    # 是否极可能是纯色/空白
    if contrast < 8:
        return {'valid': False, 'reason': 'blank_or_solid', 'size': (w, h)}

    # 边缘检测（简化：用像素差）
    if len(arr.shape) == 3:
        edges_h = np.mean(np.abs(np.diff(arr[:, :, 0], axis=1)))
        edges_v = np.mean(np.abs(np.diff(arr[:, :, 0], axis=0)))
    else:
        edges_h = np.mean(np.abs(np.diff(arr, axis=1)))
        edges_v = np.mean(np.abs(np.diff(arr, axis=0)))
    edge_intensity = float((edges_h + edges_v) / 2)

    # 判断类型
    is_bw = channel_std < 12  # 低色彩变化 → 黑白/素描
    is_low_quality = file_size < 3000  # < 3KB 可能是低质量缩略图
    is_square = 0.9 <= aspect <= 1.1
    is_landscape = aspect > 1.5

    # 综合评分：置信度是否是人像
    confidence = 1.0
    flags = []
    if contrast < 15:
        confidence -= 0.3; flags.append('低对比度')
    if is_landscape:
        confidence -= 0.2; flags.append('横版非肖像')
    if file_size < 3000:
        confidence -= 0.3; flags.append('低质量缩略图')
    if brightness > 240:
        confidence -= 0.2; flags.append('过曝/纯白')
    if brightness < 20:
        confidence -= 0.2; flags.append('过暗/纯黑')
    if channel_std < 5 and w * h > 10000:
        confidence -= 0.1; flags.append('极低色彩')

    return {
        'valid': True,
        'size': (w, h),
        'file_kb': round(file_size / 1024, 1),
        'aspect': round(aspect, 2),
        'brightness': round(brightness, 1),
        'contrast': round(contrast, 1),
        'channel_std': round(channel_std, 1),
        'edge_intensity': round(edge_intensity, 2),
        'is_bw': is_bw,
        'is_portrait': is_portrait,
        'is_square': is_square,
        'is_landscape': is_landscape,
        'is_low_quality': is_low_quality,
        'confidence': round(max(0, confidence), 2),
        'flags': flags,
        'hash': hashlib.md5(arr.tobytes()[:4096]).hexdigest()[:8]  # 快速指纹
    }

# ===== 主流程 =====
print('=== 肖像图像质量检测 ===\n')

with open(PHIL_FILE, 'r', encoding='utf-8') as f:
    philosophers = json.load(f)

# 也扫描 IMG_DIR 中不在列表里的孤立图片
existing_imgs = set()
for name in philosophers:
    safe = name.replace('/', '-').replace('\\', '-').replace(':', '-')
    for ext in ['.jpg', '.png', '.webp']:
        p = os.path.join(IMG_DIR, safe + ext)
        if os.path.exists(p):
            existing_imgs.add(os.path.basename(p))

all_imgs = set()
for f in os.listdir(IMG_DIR):
    if f.endswith(('.jpg', '.png', '.webp', '.jpeg')):
        all_imgs.add(f)

orphan_imgs = all_imgs - existing_imgs

results = {
    'suspect': [],      # 可疑（置信度低）
    'not_portrait': [], # 非肖像比例
    'bad_quality': [],  # 质量差
    'missing': [],      # 缺图片
    'orphan_imgs': sorted(orphan_imgs),  # 孤图
    'identical_hashes': [],  # 相同指纹（可能重复图片）
}

# 检测 hash 重复
hash_map = {}

total = len(philosophers)
for i, (name, data) in enumerate(philosophers.items()):
    if (i + 1) % 100 == 0:
        print(f'  [{i+1}/{total}]...')

    if not isinstance(data, dict):
        continue

    safe = name.replace('/', '-').replace('\\', '-').replace(':', '-')
    img_path = None
    for ext in ['.jpg', '.png', '.webp']:
        candidate = os.path.join(IMG_DIR, safe + ext)
        if os.path.exists(candidate):
            img_path = candidate
            break

    if not img_path:
        results['missing'].append(name)
        continue

    analysis = analyze_image(img_path)
    era = data.get('era', '')
    region = data.get('region', '')

    if not analysis['valid']:
        results['bad_quality'].append((name, os.path.basename(img_path), analysis['reason']))
        continue

    # 检查 hash 碰撞
    h = analysis['hash']
    if h in hash_map:
        results['identical_hashes'].append((
            name, os.path.basename(img_path),
            hash_map[h][0], hash_map[h][1]
        ))
    else:
        hash_map[h] = (name, os.path.basename(img_path))

    # 标记可疑
    if analysis['confidence'] < 0.7:
        results['suspect'].append((name, os.path.basename(img_path), era, analysis))
    elif not analysis['is_portrait']:
        results['not_portrait'].append((name, os.path.basename(img_path), era, analysis))

# 输出
print(f'\n=== 检测结果 ===')
print(f'总哲学家: {len(philosophers)}')
print(f'缺图片: {len(results["missing"])}')
print(f'相同图片(Hash碰撞): {len(results["identical_hashes"])}')
print(f'损毁图片: {len(results["bad_quality"])}')
print(f'可疑图片(置信度<0.7): {len(results["suspect"])}')
print(f'非肖像比例: {len(results["not_portrait"])}')
print(f'孤立图片(无对应哲学家): {len(results["orphan_imgs"])}')

print(f'\n--- 损毁图片 ({len(results["bad_quality"])}) ---')
for name, fname, reason in results['bad_quality']:
    print(f'  {name:30s} | {fname} | {reason}')

print(f'\n--- 可疑图片 ({len(results["suspect"])}) ---')
for name, fname, era, a in results['suspect']:
    print(f'  {name:35s} | era={era:20s} | conf={a["confidence"]:.2f} | {a["flags"]} | {fname}')

print(f'\n--- 相同Hash ({len(results["identical_hashes"])}) ---')
for name, fname, other_name, other_fname in results['identical_hashes']:
    print(f'  {name} ({fname}) = {other_name} ({other_fname})')

print(f'\n--- 非肖像比例 ({len(results["not_portrait"])}) ---')
for name, fname, era, a in results['not_portrait'][:20]:
    print(f'  {name:35s} | era={era:20s} | aspect={a["aspect"]} | {fname}')

if len(results["orphan_imgs"]) > 0:
    print(f'\n--- 孤立图片 ({len(results["orphan_imgs"])}) ---')
    for f in results['orphan_imgs'][:30]:
        print(f'  {f}')

# 保存
with open(os.path.join(BASE, 'scripts', '_portrait_check.json'), 'w', encoding='utf-8') as f:
    # 简化输出（移除 numpy 等不可序列化的）
    clean = {
        'suspect': [(n, fn, e, a['confidence'], a['flags']) for n, fn, e, a in results['suspect']],
        'identical_hashes': results['identical_hashes'],
        'bad_quality': results['bad_quality'],
        'not_portrait': [(n, fn, e, a['aspect'], a['confidence']) for n, fn, e, a in results['not_portrait']],
        'missing': results['missing'],
        'orphan_imgs': results['orphan_imgs'],
    }
    json.dump(clean, f, ensure_ascii=False, indent=2)

print(f'\n结果: scripts/_portrait_check.json')
