#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepPhilosophy Data Sync Tool
Usage:
  python sync_to_cloud.py --full
  python sync_to_cloud.py --dry-run
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import os
import sys
import json
import hashlib
import time
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional

# ============================================================
# 配置（可通过命令行参数覆盖）
# ============================================================
CLOUD_API_URL = os.getenv("DP_API_URL", "https://deepphilosophy.onrender.com")
LOCAL_PHILOSOPHY_DIR = os.getenv("DP_LOCAL_DIR", "F:/philosophy")
SYNC_STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".sync_state.json")

# 支持的扩展名
SUPPORTED_EXTS = {".pdf", ".epub", ".txt", ".md"}


def get_file_hash(file_path: str) -> str:
    """计算文件 MD5"""
    h = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_sync_state() -> dict:
    """加载上次同步状态"""
    if os.path.exists(SYNC_STATE_FILE):
        with open(SYNC_STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_sync_state(state: dict):
    """保存同步状态"""
    with open(SYNC_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def scan_local_files(base_dir: str) -> dict:
    """扫描本地所有支持的文件及其哈希"""
    files = {}
    if not os.path.exists(base_dir):
        print(f"[ERROR] 目录不存在: {base_dir}")
        return files

    for root, dirs, filenames in os.walk(base_dir):
        for f in filenames:
            ext = Path(f).suffix.lower()
            if ext not in SUPPORTED_EXTS:
                continue
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, base_dir).replace("\\", "/")
            files[rel_path] = {
                "size": os.path.getsize(full_path),
                "hash": get_file_hash(full_path),
                "mtime": os.path.getmtime(full_path),
            }
    return files


def sync_to_cloud(
    api_url: str,
    local_dir: str,
    dry_run: bool = False,
    full: bool = False,
):
    """同步本地文件 → 云端服务器"""
    print("=" * 60)
    print("  DeepPhilosophy 数据同步工具")
    print("=" * 60)
    print(f"  本地目录: {local_dir}")
    print(f"  云端地址: {api_url}")
    print()

    # 检查云端健康状态
    try:
        resp = requests.get(f"{api_url}/api/health", timeout=60)
        if resp.status_code == 200:
            print("  ✅ 云端服务连接正常")
        else:
            print(f"  ⚠️ 云端服务状态异常: {resp.status_code}")
    except Exception as e:
        print(f"  ❌ 无法连接云端服务: {e}")
        print("  请确认 API 地址正确且服务正在运行")
        return

    prev_state = {} if full else load_sync_state()
    current_files = scan_local_files(local_dir)

    # 计算差异
    new_files = []
    changed_files = []
    deleted_files = []

    for path, info in current_files.items():
        if path not in prev_state:
            new_files.append(path)
        elif prev_state[path]["hash"] != info["hash"]:
            changed_files.append(path)

    for path in prev_state:
        if path not in current_files:
            deleted_files.append(path)

    print(f"  📄 新增: {len(new_files)} 个文件")
    for f in new_files:
        file_size = current_files[f]["size"] / (1024 * 1024)
        print(f"     + {f} ({file_size:.1f} MB)")
    print(f"  ✏️ 修改: {len(changed_files)} 个文件")
    for f in changed_files:
        print(f"     ~ {f}")
    print(f"  🗑 删除: {len(deleted_files)} 个文件")
    for f in deleted_files:
        print(f"     - {f}")

    if dry_run:
        print("\n  [DRY RUN] 仅预览，未实际同步")
        return

    if not new_files and not changed_files and not deleted_files:
        print("\n  ✅ 无变更，无需同步")
        return

    # ---- 执行同步 ----
    print(f"\n{'─' * 60}")
    print("  开始同步...")
    print(f"{'─' * 60}")

    uploaded = 0
    failed = 0

    # 上传新文件和修改的文件
    for path in new_files + changed_files:
        full_path = os.path.join(local_dir, path)
        file_size_mb = os.path.getsize(full_path) / (1024 * 1024)

        print(f"\n  ⬆️ [{file_size_mb:.1f}MB] {path} ...", end=" ", flush=True)

        try:
            with open(full_path, "rb") as f:
                resp = requests.post(
                    f"{api_url}/api/sync/upload",
                    files={"file": (path, f, "application/octet-stream")},
                    timeout=600,  # 大文件需要更长时间
                )
            if resp.status_code == 200:
                print("✅")
                uploaded += 1
            else:
                print(f"❌ HTTP {resp.status_code}: {resp.text[:100]}")
                failed += 1
        except requests.exceptions.Timeout:
            print("❌ 超时")
            failed += 1
        except Exception as e:
            print(f"❌ {e}")
            failed += 1

    # 删除云端文件
    for path in deleted_files:
        print(f"\n  🗑 {path} ...", end=" ", flush=True)
        try:
            resp = requests.post(
                f"{api_url}/api/sync/delete",
                json={"path": path},
                timeout=30,
            )
            if resp.status_code == 200:
                print("✅")
            else:
                print(f"⚠️ HTTP {resp.status_code}")
        except Exception as e:
            print(f"⚠️ {e}")

    # 保存同步状态
    save_sync_state(current_files)

    # 触发知识库重建
    print(f"\n  🔄 触发云端知识库重建...", end=" ", flush=True)
    try:
        resp = requests.post(f"{api_url}/api/knowledge/init", timeout=1800)
        if resp.status_code == 200:
            data = resp.json()
            print(
                f"✅ "
                f"({data.get('documents_indexed', 0)} 文档, "
                f"{data.get('chunks', 0)} 文本块)"
            )
            if data.get("skipped", 0) > 0:
                print(f"     ⏭ 跳过 {data['skipped']} 个扫描件/空文档")
        else:
            print(f"⚠️ HTTP {resp.status_code}")
    except requests.exceptions.Timeout:
        print("⚠️ 超时（可能仍在后台处理中）")
    except Exception as e:
        print(f"⚠️ {e}")

    print(f"\n{'=' * 60}")
    print(f"  同步完成: {uploaded} 上传成功, {failed} 失败")
    if failed == 0:
        print(f"  ✅ 数据已同步至云端！")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="DeepPhilosophy 数据同步工具 - 将本地哲学书籍同步到云端"
    )
    parser.add_argument(
        "--api-url",
        help=f"云端 API 地址 (默认: {CLOUD_API_URL})",
        default=None,
    )
    parser.add_argument(
        "--local-dir",
        help=f"本地哲学目录 (默认: {LOCAL_PHILOSOPHY_DIR})",
        default=None,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="预览模式，只显示变更不实际上传",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="全量同步（忽略历史状态，重新上传所有文件）",
    )

    args = parser.parse_args()

    api_url = args.api_url or CLOUD_API_URL
    local_dir = args.local_dir or LOCAL_PHILOSOPHY_DIR

    sync_to_cloud(
        api_url=api_url,
        local_dir=local_dir,
        dry_run=args.dry_run,
        full=args.full,
    )
