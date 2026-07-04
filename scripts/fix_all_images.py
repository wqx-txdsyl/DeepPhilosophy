#!/usr/bin/env python3
"""
全量图片修复：重爬 → 失败则AI生成 → 本地验证
"""
import os, sys, json, subprocess, time

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPT_DIR)
PHILO_DIR = os.path.join(ROOT, "app", "public", "philosopher")
FETCH_SCRIPT = os.path.join(SCRIPT_DIR, "fetch_philosopher_img.py")
GEN_SCRIPT = os.path.join(SCRIPT_DIR, "gen_portrait.py")

# ============================================================
# Step 1: 找出所有缺图/差图的哲人
# ============================================================
with open(os.path.join(ROOT, "backend", "data", "philosophers.json"), "r", encoding="utf-8") as f:
    philosophers = json.load(f)

# 需要修复的名单
TO_FIX = []

for name in philosophers:
    safe = name.replace("/", "-").replace(":", "：")
    path = os.path.join(PHILO_DIR, f"{safe}.jpg")

    if not os.path.exists(path):
        TO_FIX.append((name, "missing"))
        continue

    sz = os.path.getsize(path)
    if sz < 20000:  # < 20KB, 几乎肯定是低质量/损坏的图
        TO_FIX.append((name, f"tiny_{sz}"))
        continue

    try:
        from PIL import Image
        img = Image.open(path)
        w, h = img.size
        if w < 200 or h < 200:  # 太小了
            TO_FIX.append((name, f"small_{w}x{h}"))
    except:
        TO_FIX.append((name, "corrupt"))

print(f"Need to fix: {len(TO_FIX)} philosophers\n")

# ============================================================
# Step 2: 逐个修复：先 Wikipedia 重爬，失败则 AI 生成
# ============================================================
fixed = 0
failed = []

for i, (name, reason) in enumerate(TO_FIX, 1):
    print(f"[{i}/{len(TO_FIX)}] {name} ({reason})")

    # 先删除旧文件
    safe = name.replace("/", "-").replace(":", "：")
    old_path = os.path.join(PHILO_DIR, f"{safe}.jpg")
    thumb_path = os.path.join(PHILO_DIR, "thumb", f"{safe}.jpg")
    if os.path.exists(old_path):
        os.remove(old_path)
    if os.path.exists(thumb_path):
        os.remove(thumb_path)

    # Strategy 1: Wikipedia fetch
    success = False
    try:
        r = subprocess.run(
            [sys.executable, FETCH_SCRIPT, name],
            capture_output=True, text=True, timeout=45,
            cwd=SCRIPT_DIR,
        )
        if os.path.exists(old_path):
            sz = os.path.getsize(old_path)
            if sz > 30000:  # 爬到了正常大小的图
                print(f"  OK: fetched from Wiki ({sz//1024}KB)")
                fixed += 1
                success = True
    except Exception as e:
        pass

    # Strategy 2: AI generation
    if not success:
        print(f"  Fetch failed, generating AI portrait...")
        try:
            r = subprocess.run(
                [sys.executable, GEN_SCRIPT, name],
                capture_output=True, text=True, timeout=60,
                cwd=SCRIPT_DIR,
            )
            if os.path.exists(old_path):
                print(f"  OK: AI portrait generated")
                fixed += 1
                success = True
            else:
                print(f"  FAIL: AI generation produced no file")
                failed.append(name)
        except Exception as e:
            print(f"  ERROR: {e}")
            failed.append(name)

    time.sleep(0.5)  # Rate limit

# ============================================================
# Step 3: 报告
# ============================================================
print(f"\n{'='*60}")
print(f"Fixed: {fixed}/{len(TO_FIX)}")
if failed:
    print(f"Still missing: {len(failed)}")
    for n in failed:
        print(f"  - {n}")

# Count final state
missing_final = 0
for name in philosophers:
    safe = name.replace("/", "-").replace(":", "：")
    if not os.path.exists(os.path.join(PHILO_DIR, f"{safe}.jpg")):
        missing_final += 1
print(f"Total philosophers without images: {missing_final}")
