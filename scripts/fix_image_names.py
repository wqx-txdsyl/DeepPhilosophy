#!/usr/bin/env python3
"""
修复哲学家图片损坏文件名（85 个文件含 U+FFFD 替换字符）
从 philosophers.json 匹配标准名并重命名
"""
import os, json, shutil
from _lib import PHILOSOPHERS_FILE, ROOT

IMG_DIR = os.path.join(ROOT, "app", "public", "philosopher")
THUMB_DIR = os.path.join(IMG_DIR, "thumb")

with open(PHILOSOPHERS_FILE, "r", encoding="utf-8") as f:
    philosophers = json.load(f)

canonical_names = set(philosophers.keys())
# 也加入别名映射
from _lib import load_aliases
aliases = load_aliases()
for alias, canonical in aliases.items():
    canonical_names.add(canonical)

# 收集损坏文件
damaged = []
for f in os.listdir(IMG_DIR):
    if f.endswith(('.jpg', '.png', '.webp', '.jpeg')):
        if '�' in f:
            damaged.append(f)

print(f"Found {len(damaged)} damaged files")

repaired = 0
skipped = 0
log_lines = []

for filename in damaged:
    name_no_ext = os.path.splitext(filename)[0]
    ext = os.path.splitext(filename)[1]

    # 策略1: 从文件名中提取可读部分，在哲学家名中搜索
    readable = ''.join(c for c in name_no_ext if c.isalpha() or c in '. -')
    readable = readable.strip(' .-')

    match = None
    # 精确匹配可读部分
    for cname in canonical_names:
        if readable and readable.lower() == cname.lower():
            match = cname
            break

    # 策略2: 模糊匹配（保留可读的 CJK 字符）
    if not match:
        cjk_chars = [c for c in name_no_ext if '一' <= c <= '鿿' or '぀' <= c <= 'ヿ']
        if cjk_chars:
            partial = ''.join(cjk_chars)
            for cname in canonical_names:
                if partial in cname:
                    match = cname
                    break

    # 策略3: 基于哲学家列表的密近匹配
    if not match:
        # 提取所有字母数字字符
        stripped = ''.join(c for c in name_no_ext if c.isalnum() or c in '. -')
        for cname in canonical_names:
            c_stripped = ''.join(c for c in cname if c.isalnum() or c in '. -')
            if stripped and c_stripped and (
                stripped.lower() in c_stripped.lower() or
                c_stripped.lower() in stripped.lower()
            ):
                match = cname
                break

    if match:
        old_path = os.path.join(IMG_DIR, filename)
        new_name = f"{match}{ext}"
        new_path = os.path.join(IMG_DIR, new_name)

        if os.path.exists(new_path) and old_path != new_path:
            print(f"  SKIP: {ascii(filename)[:60]} → {new_name} (target exists)")
            log_lines.append(f"CONFLICT: {filename} → {new_name}")
            skipped += 1
            continue

        print(f"  RENAME: {ascii(filename)[:60]} → {new_name}")
        os.rename(old_path, new_path)
        log_lines.append(f"RENAMED: {filename} → {new_name}")

        # 也重命名缩略图
        thumb_old = os.path.join(THUMB_DIR, filename)
        thumb_new = os.path.join(THUMB_DIR, new_name)
        if os.path.exists(thumb_old) and not os.path.exists(thumb_new):
            os.rename(thumb_old, thumb_new)
        repaired += 1
    else:
        print(f"  NO MATCH: {ascii(filename)[:80]}")
        log_lines.append(f"UNMATCHED: {filename}")
        skipped += 1

print(f"\nRepaired: {repaired}, Skipped: {skipped}")

# 写入日志
log_path = os.path.join(os.path.dirname(__file__), "_fix_image_names.log")
with open(log_path, "w", encoding="utf-8") as f:
    f.write(f"Repaired: {repaired}\nSkipped: {skipped}\n\n")
    f.write('\n'.join(log_lines))
print(f"Log written to {log_path}")
