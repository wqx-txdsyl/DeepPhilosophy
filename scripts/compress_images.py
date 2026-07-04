#!/usr/bin/env python3
"""
图片批量压缩 — 流派背景图 + 哲人头像 + gene 素材
目标: 493MB → ~150MB (70% 削减)
- 学校背景图: 2560px → 1200px WebP
- 哲人头像: 原尺寸 → 800px WebP（保留原图当 thumb）
- gene 素材: 保持原尺寸，转 WebP
用法: python compress_images.py          # 预览模式 (dry run)
     python compress_images.py --apply  # 执行压缩
"""
import os, sys
from PIL import Image
from _lib import ROOT

PUBLIC = os.path.join(ROOT, "app", "public")

# ——— 配置 ———
CONFIG = {
    "schools": {
        "dir": os.path.join(PUBLIC, "schools"),
        "max_width": 1200,
        "quality": 82,
        "format": "webp",
        "skip_existing": True,   # 已有 WebP 则跳过
    },
    "philosopher": {
        "dir": os.path.join(PUBLIC, "philosopher"),
        "max_width": 800,
        "quality": 85,
        "format": "webp",
        "skip_existing": True,
    },
    "gene": {
        "dir": os.path.join(PUBLIC, "gene"),
        "max_width": 0,           # 0 = 不 resize
        "quality": 85,
        "format": "webp",
        "skip_existing": True,
    },
}

COMPRESSED_SUFFIX = ".compressed"

def compress_dir(cfg, apply=False):
    """压缩一个目录下的所有图片"""
    d = cfg["dir"]
    if not os.path.isdir(d):
        print(f"  SKIP: {d} (not found)")
        return {"count": 0, "before": 0, "after": 0}

    max_w = cfg["max_width"]
    quality = cfg["quality"]
    fmt = cfg["format"]
    skip = cfg["skip_existing"]
    ext_out = f".{fmt}"

    stats = {"count": 0, "before": 0, "after": 0}

    for root, dirs, files in os.walk(d):
        # 跳过 thumb 子目录
        dirs[:] = [d for d in dirs if d != "thumb"]

        for f in sorted(files):
            if not f.lower().endswith(('.jpg', '.jpeg', '.png')):
                continue

            in_path = os.path.join(root, f)
            stem = os.path.splitext(f)[0]
            out_path = os.path.join(root, f"{stem}{ext_out}")

            # 跳过已压缩的
            if skip and os.path.exists(out_path):
                continue

            # 跳过已经标记的文件
            if COMPRESSED_SUFFIX in f:
                continue

            in_size = os.path.getsize(in_path)
            stats["before"] += in_size

            if not apply:
                print(f"  [DRY] {os.path.relpath(in_path, PUBLIC)} ({in_size//1024}KB)")
                stats["count"] += 1
                continue

            try:
                img = Image.open(in_path)
                if img.mode in ("RGBA", "P", "LA"):
                    img = img.convert("RGBA")
                else:
                    img = img.convert("RGB")

                # Resize
                if max_w > 0 and img.size[0] > max_w:
                    ratio = max_w / img.size[0]
                    new_h = int(img.size[1] * ratio)
                    img = img.resize((max_w, new_h), Image.LANCZOS)

                # Save
                save_kwargs = {"quality": quality, "optimize": True}
                if fmt == "webp":
                    save_kwargs["method"] = 6  # slowest = best compression
                img.save(out_path, fmt.upper(), **save_kwargs)

                out_size = os.path.getsize(out_path)
                stats["after"] += out_size
                stats["count"] += 1
                pct = (1 - out_size / in_size) * 100
                print(f"  {os.path.relpath(in_path, PUBLIC)}: {in_size//1024}KB → {out_size//1024}KB (-{pct:.0f}%)")

                # 可选：删除原文件
                # os.remove(in_path)

            except Exception as e:
                print(f"  ERROR {f}: {e}")

    return stats


def main():
    apply = "--apply" in sys.argv

    if not apply:
        print("=" * 60)
        print("DRY RUN MODE — 仅预览，不修改文件")
        print("添加 --apply 参数执行实际压缩")
        print("=" * 60)
    else:
        print("=" * 60)
        print("COMPRESS MODE — 正在压缩图片...")
        print("=" * 60)

    grand_total = {"count": 0, "before": 0, "after": 0}

    for name, cfg in CONFIG.items():
        print(f"\n--- {name} ---")
        stats = compress_dir(cfg, apply=apply)
        for k in stats:
            grand_total[k] += stats[k]
        if stats["count"] > 0 and not apply:
            print(f"  Total files: {stats['count']}")

    print(f"\n{'=' * 60}")
    if apply:
        print(f"Done: {grand_total['count']} files")
        print(f"Before: {grand_total['before']//(1024*1024)}MB")
        print(f"After:  {grand_total['after']//(1024*1024)}MB")
        if grand_total["before"] > 0:
            pct = (1 - grand_total["after"] / grand_total["before"]) * 100
            print(f"Saved:  {(grand_total['before'] - grand_total['after'])//(1024*1024)}MB ({pct:.0f}%)")
    else:
        print(f"Preview: {grand_total['count']} files would be compressed")
        print("Run with --apply to compress")


if __name__ == "__main__":
    main()
