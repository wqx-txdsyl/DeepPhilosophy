#!/usr/bin/env python3
"""
批量爬取哲学家头像
用法: python fetch_philosopher_batch.py [--skip-existing]
"""
import sys, os, json, time, subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FETCH_SCRIPT = os.path.join(SCRIPT_DIR, "fetch_philosopher_img.py")
PHILOSOPHERS_FILE = os.path.join(SCRIPT_DIR, "..", "backend", "data", "philosophers.json")
FULL_LIST_FILE = os.path.join(SCRIPT_DIR, "_batch_philosophers_full.txt")
OUT_DIR = os.path.join(SCRIPT_DIR, "..", "app", "public", "philosopher")

def load_names():
    # 优先使用全量列表（381），否则回退到 philosophers.json（353）
    if os.path.exists(FULL_LIST_FILE):
        with open(FULL_LIST_FILE, "r", encoding="utf-8") as f:
            names = [l.strip() for l in f if l.strip()]
        if names:
            print(f"使用全量列表: {len(names)} 位哲人 ({FULL_LIST_FILE})")
            return names
    with open(PHILOSOPHERS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"使用内置库: {len(data)} 位哲人")
    return sorted(data.keys())

def already_has_image(name):
    safe = name.replace("/", "-").replace("\\", "-").replace(":", "：")
    return os.path.exists(os.path.join(OUT_DIR, f"{safe}.jpg"))

def main():
    skip_existing = "--skip-existing" in sys.argv
    names = load_names()
    total = len(names)

    existing = sum(1 for n in names if already_has_image(n))
    print(f"哲学家总数: {total}")
    print(f"已有图片: {existing}")
    print(f"待爬取: {total - existing}")
    print(f"{'='*50}")

    success, fail, skipped = 0, 0, 0
    for i, name in enumerate(names, 1):
        if skip_existing and already_has_image(name):
            skipped += 1
            continue

        print(f"\n[{i}/{total}] {name}")
        result = subprocess.run(
            [sys.executable, FETCH_SCRIPT, name],
            cwd=SCRIPT_DIR, timeout=180,
            capture_output=True, text=True
        )
        out = (result.stdout or '') + (result.stderr or '')
        if result.returncode == 0:
            success += 1
        elif "SKIP" in out:
            skipped += 1
        else:
            fail += 1
            lines = out.strip().split("\n")
            print(f"  [FAIL] {lines[-1] if lines else 'unknown error'}")

        # Rate limit: 1 request per 2 seconds (Wikipedia API is lenient but be polite)
        if i < total:
            time.sleep(2)

    print(f"\n{'='*50}")
    print(f"完成！成功: {success}, 失败: {fail}, 跳过: {skipped}")
    print(f"总计处理: {success + fail + skipped}/{total}")

if __name__ == "__main__":
    main()
