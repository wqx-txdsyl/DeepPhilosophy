# -*- coding: utf-8 -*-
"""
dp_sync_oss_images.py — 书内图片同步到阿里云 OSS（章内图直连 OSS 的数据底座）

源:   DeepPhilosophy/backend/data/book_images/（生产真身, 11498 张）
目标: OSS bucket deepphilosophy, 前缀 book_images/
      章内图加载: https://deepphilosophy.oss-cn-shanghai.aliyuncs.com/book_images/{name}

同步策略（幂等, 可断点续跑, 与 dp_sync_oss_chapters 同构）:
  1. ListObjects 取远端全部 key→ETag（ETag 大写, 与本地 md5 统一小写比较）
  2. 本地遍历计算 md5, 与远端对比 → 仅传缺失/变更
  3. ThreadPool 并发上传, 失败重试 2 次

用法:
  python dp_sync_oss_images.py              # 增量同步
  python dp_sync_oss_images.py --dry-run    # 只统计不动
  python dp_sync_oss_images.py --prune      # 删除远端有而本地无的（慎用）
  python dp_sync_oss_images.py --workers 16 # 并发数（默认 16）

凭证: 从本仓库根 .env 读 OSS_ACCESS_KEY/OSS_SECRET_KEY/OSS_BUCKET/OSS_ENDPOINT
"""
import io, os, sys, hashlib, threading

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

import oss2

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))            # PhiAgent/backend
ROOT = os.path.dirname(BASE)                                                   # PhiAgent
DP_IMG = os.path.join(ROOT, "..", "DeepPhilosophy", "backend", "data", "book_images")  # 源（生产真身）


def load_env(path):
    env = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def md5_file(fp):
    h = hashlib.md5()
    with open(fp, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    args = [a for a in sys.argv[1:]]
    dry = "--dry-run" in args
    prune = "--prune" in args
    workers = 16
    for a in args:
        if a.startswith("--workers="):
            workers = int(a.split("=", 1)[1])

    env = load_env(os.path.join(ROOT, ".env"))
    ak = os.environ.get("OSS_ACCESS_KEY") or env.get("OSS_ACCESS_KEY")
    sk = os.environ.get("OSS_SECRET_KEY") or env.get("OSS_SECRET_KEY")
    bucket_name = os.environ.get("OSS_BUCKET") or env.get("OSS_BUCKET")
    endpoint = os.environ.get("OSS_ENDPOINT") or env.get("OSS_ENDPOINT")
    if not (ak and sk and bucket_name and endpoint):
        sys.exit(f"缺少 OSS 凭证: 请检查 {os.path.join(ROOT, '.env')} 的 OSS_ACCESS_KEY/OSS_SECRET_KEY/OSS_BUCKET/OSS_ENDPOINT")

    if not os.path.isdir(DP_IMG):
        sys.exit(f"图片源目录不存在: {DP_IMG}")

    auth = oss2.Auth(ak, sk)
    bucket = oss2.Bucket(auth, f"https://{endpoint}", bucket_name)

    # ── 1. 远端清单 ──
    print("列出远端 book_images/ ...")
    remote = {}
    for obj in oss2.ObjectIterator(bucket, prefix="book_images/"):
        remote[obj.key] = (obj.etag or "").strip('"').lower()  # ETag 大写, 统一小写
    print(f"远端: {len(remote)} 个对象")

    # ── 2. 本地清单 ──
    print("计算本地 md5 ...")
    local = {}
    for fn in os.listdir(DP_IMG):
        fp = os.path.join(DP_IMG, fn)
        if not os.path.isfile(fp):
            continue
        local["book_images/" + fn] = md5_file(fp)
    print(f"本地: {len(local)} 张")

    # ── 3. 差异 ──
    to_upload = {k: v for k, v in local.items() if k not in remote or remote[k] != v}
    orphan = [k for k in remote if k not in local]
    print(f"需上传: {len(to_upload)}  远端孤儿: {len(orphan)}")
    if dry:
        print("--dry-run 模式, 不执行")
        return

    # ── 4. 并发上传 ──
    lock = threading.Lock()
    ok, fail = [], []

    def work(items):
        for key in items:
            fp = os.path.join(DP_IMG, os.path.basename(key))
            for attempt in range(3):
                try:
                    bucket.put_object_from_file(key, fp)
                    with lock:
                        ok.append(key)
                    break
                except Exception as e:
                    if attempt == 2:
                        with lock:
                            fail.append((key, str(e)[:80]))
    import concurrent.futures
    items = list(to_upload.keys())
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        batch = [items[i::workers] for i in range(workers)]
        list(ex.map(work, batch))
    print(f"完成: 上传 {len(ok)} / 失败 {len(fail)}")
    for k, e in fail[:10]:
        print(f"  失败 {k}: {e}")
    if prune and orphan:
        for key in orphan:
            bucket.delete_object(key)
        print(f"prune: 删除远端孤儿 {len(orphan)}")


if __name__ == "__main__":
    main()
