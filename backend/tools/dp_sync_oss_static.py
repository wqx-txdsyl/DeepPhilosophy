# -*- coding: utf-8 -*-
"""
dp_sync_oss_static.py — 书架静态数据同步到阿里云 OSS（书架提速 2026-08-11）

背景: 用户网络访问同源 CF 边缘 3-6s/请求, books.json 555KB 每次回源 → /book 首访卡"加载中"
      前端已改 OSS 双轨（books.json/covers.json/封面图 OSS 直链优先）→ 本脚本保证 OSS 有最新数据

源:   DeepPhilosophy/app/public/（生产真身）
目标: OSS bucket deepphilosophy
      books.json → 根 books.json（前端双轨: https://deepphilosophy.oss-cn-shanghai.aliyuncs.com/books.json）
      covers.json → 根 covers.json
      covers/*.webp → covers/（封面直链, 402 张 ~13MB）

同步策略（幂等, 与 dp_sync_oss_chapters/images 同构）:
  1. ListObjects 取远端 key→ETag（ETag 大写, 与本地 md5 统一小写比较）
  2. 本地 md5 对比 → 仅传缺失/变更
  3. ThreadPool 并发上传, 失败重试 2 次

用法:
  python dp_sync_oss_static.py              # 增量同步
  python dp_sync_oss_static.py --dry-run    # 只统计不动
  python dp_sync_oss_static.py --workers 16 # 并发数（默认 16）

凭证: 从本仓库根 .env 读 OSS_ACCESS_KEY/OSS_SECRET_KEY/OSS_BUCKET/OSS_ENDPOINT
"""
import io, os, sys, hashlib, threading

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

import oss2

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))            # backend/
ROOT = os.path.dirname(BASE)                                                   # 仓库根（2026-08-14 合并后即 DeepPhilosophy）
DP_PUBLIC = os.path.join(ROOT, "app", "public")                                # 源（生产真身）

# 同步清单: (本地相对路径, OSS key)
SOURCES = [
    ("books.json", "books.json"),
    ("covers.json", "covers.json"),
    # 2026-08-12: 哲学家目录（homepage/列表页双轨 OSS 优先）— 曾因漏同步,
    #   OSS 残留去重前 759 版, homepage 显示 759 vs 列表页 744, 用户反馈数字不符
    ("philosophers.json", "philosophers.json"),
]
# 目录整体同步: (本地子目录, OSS 前缀)
#   covers/   — 封面（书架/详情 双轨 OSS 直链）
#   schools/  — 流派图 + 首页/列表页背景（2026-08-11 新增, 120 张 44MB）
#   gene/     — 谱系素材（2026-08-11 新增, 时代/区域图 4.5MB）
DIRS = [
    ("covers", "covers"),
    ("schools", "schools"),
    ("gene", "gene"),
    # 构建产物（vite base 生产指向 OSS app/assets/, 构建后必须同步, 否则 JS 404）
    (os.path.join(ROOT, "app", "dist", "assets"), "app/assets"),
    # 书籍详情 JSON（2026-08-12 详情页提速: 前端双轨 OSS 优先 → 同源回退）
    ("book_detail", "book_detail"),
]


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

    if not os.path.isdir(DP_PUBLIC):
        sys.exit(f"源目录不存在: {DP_PUBLIC}")

    auth = oss2.Auth(ak, sk)
    bucket = oss2.Bucket(auth, f"https://{endpoint}", bucket_name)

    # ── 1. 本地清单 ──
    print("构建本地清单 ...")
    local = {}
    for rel, key in SOURCES:
        fp = os.path.join(DP_PUBLIC, rel)
        if not os.path.isfile(fp):
            print(f"  警告: 本地缺失 {rel}, 跳过")
            continue
        local[key] = md5_file(fp)
    for d, prefix in DIRS:
        d = d if os.path.isabs(d) else os.path.join(DP_PUBLIC, d)
        if not os.path.isdir(d):
            print(f"  警告: 目录缺失 {d}, 跳过")
            continue
        for fn in os.listdir(d):
            fp = os.path.join(d, fn)
            if not os.path.isfile(fp):
                continue
            local[f"{prefix}/{fn}"] = md5_file(fp)
    print(f"本地: {len(local)} 个对象")

    # ── 2. 远端清单 ──
    print("列出远端 ...")
    remote = {}
    prefixes = ("covers/", "app/assets/", "schools/", "gene/")
    for obj in oss2.ObjectIterator(bucket, prefix=""):
        # 只看本脚本管理的前缀: 根两个 json + covers/ + app/assets/ + schools/ + gene/
        if obj.key in ("books.json", "covers.json") or obj.key.startswith(prefixes):
            remote[obj.key] = (obj.etag or "").strip('"').lower()
    print(f"远端: {len(remote)} 个对象")

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
            if key.startswith("app/assets/"):
                fp = os.path.join(DIRS[3][0], os.path.basename(key))  # dist/assets/{file}
            else:
                fp = os.path.join(DP_PUBLIC, key)  # 根 json 或 covers/schools/gene 下文件
            for attempt in range(3):
                try:
                    # 2026-09-04: book_detail 不带 Cache-Control 时浏览器启发式缓存旧详情,
                    # 数据更新后用户侧长期不刷新 → 详情类短缓存, 其余维持原行为
                    _headers = {"Cache-Control": "max-age=300"} if key.startswith("book_detail/") else None
                    if _headers:
                        bucket.put_object_from_file(key, fp, headers=_headers)
                    else:
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


if __name__ == "__main__":
    main()
