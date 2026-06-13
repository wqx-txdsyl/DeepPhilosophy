#!/usr/bin/env python3
"""
生成书籍目录 JSON（离线数据兜底用）
从本地 F:/philosophy 扫描生成 app/src/assets/books.json
也可用于检查知识库完整性
"""
import os
import json
import hashlib
from pathlib import Path

PHILOSOPHY_DIR = "F:/philosophy"
OUTPUT_PATHS = [
    "app/src/assets/books.json",            # Android 内置数据
    "backend/data/books_catalog.json",       # 后端参考
]

SUPPORTED_EXTS = {".pdf", ".epub", ".txt", ".md"}


def generate_catalog(philosophy_dir: str) -> dict:
    """扫描目录生成书籍目录"""
    if not os.path.exists(philosophy_dir):
        print(f"[ERROR] 目录不存在: {philosophy_dir}")
        return {"books": [], "total": 0, "generated_at": "", "error": "目录不存在"}

    books = []
    stats = {"pdf": 0, "epub": 0, "txt": 0, "md": 0, "total_size": 0}

    for root, dirs, files in os.walk(philosophy_dir):
        for f in files:
            ext = Path(f).suffix.lower()
            if ext not in SUPPORTED_EXTS:
                continue

            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, philosophy_dir)
            parts = rel_path.replace("\\", "/").split("/")

            region = parts[0] if len(parts) > 0 else "未知"
            author = parts[1] if len(parts) > 1 else "未知"
            author_clean = author.replace("###合集&概述###", "合集&概述")
            title = Path(f).stem
            file_size = os.path.getsize(full_path)

            file_id = hashlib.md5(rel_path.encode()).hexdigest()[:12]
            file_type = ext.replace(".", "")

            books.append({
                "id": file_id,
                "title": title,
                "author": author_clean,
                "region": region,
                "file_type": file_type,
                "file_size": file_size,
                "status": "pending" if file_type == "txt" else "available",
                "path": rel_path.replace("\\", "/"),
            })

            stats[file_type] = stats.get(file_type, 0) + 1
            stats["total_size"] += file_size

    books.sort(key=lambda b: (b["region"], b["author"], b["title"]))

    from datetime import datetime
    catalog = {
        "books": books,
        "total": len(books),
        "generated_at": datetime.now().isoformat(),
        "stats": {
            **stats,
            "total_size_mb": round(stats["total_size"] / (1024 * 1024), 1),
        },
    }

    return catalog


def main():
    print("=" * 60)
    print("  DeepPhilosophy 书籍目录生成器")
    print("=" * 60)
    print(f"  扫描目录: {PHILOSOPHY_DIR}")
    print()

    catalog = generate_catalog(PHILOSOPHY_DIR)

    if catalog.get("error"):
        print(f"  ❌ {catalog['error']}")
        return

    print(f"  📚 书籍总数: {catalog['total']}")
    s = catalog["stats"]
    print(f"  📄 PDF: {s['pdf']}  |  📖 EPUB: {s['epub']}  |  📝 TXT(待收录): {s['txt']}")
    print(f"  💾 总大小: {s['total_size_mb']} MB")
    print()

    # 按区域统计
    regions = {}
    authors_set = set()
    for b in catalog["books"]:
        r = b["region"]
        if r not in regions:
            regions[r] = {"count": 0, "authors": set()}
        regions[r]["count"] += 1
        regions[r]["authors"].add(b["author"])
        authors_set.add(b["author"])

    for region, info in sorted(regions.items()):
        print(f"  {region}: {info['count']} 本书, {len(info['authors'])} 位作者")
    print(f"  总计: {len(authors_set)} 位作者")

    # 写入输出文件
    for output_path in OUTPUT_PATHS:
        abs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            json.dump(catalog, f, ensure_ascii=False, indent=2)
        print(f"\n  ✅ 已写入: {output_path}")


if __name__ == "__main__":
    # 强制 UTF-8 输出，兼容 Windows GBK 终端
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    main()
