# -*- coding: utf-8 -*-
"""
dp_sync_oss_chapters.py — 章节数据增量同步到阿里云 OSS（国内直连提速，jsDelivr 兜底配合）

源:   DeepPhilosophy/backend/data/book_chapters/（git 跟踪源, 与 jsDelivr 读的是同一份）
目标: OSS bucket deepphilosophy, 前缀 book_chapters/
      前端生产读取: https://deepphilosophy.oss-cn-shanghai.aliyuncs.com/book_chapters/{bid}/{idx}.json

同步策略（幂等, 可断点续跑）:
  1. ListObjects 取远端全部 key→ETag（ETag = 普通上传文件的 MD5）
  2. 本地遍历 {bid}/*.json 计算 md5, 与远端对比 → 仅传缺失/变更
  3. ThreadPool 并发上传, 失败重试 2 次

用法:
  python dp_sync_oss_chapters.py              # 增量同步
  python dp_sync_oss_chapters.py --dry-run    # 只统计不动
  python dp_sync_oss_chapters.py --prune      # 删除远端有而本地无的（重建书残留, 慎用）
  python dp_sync_oss_chapters.py --workers 16 # 并发数（默认 16）

凭证: 从本仓库根 .env 读 OSS_ACCESS_KEY/OSS_SECRET_KEY/OSS_BUCKET/OSS_ENDPOINT
"""
import io, json, os, sys, hashlib, threading

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

import oss2

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))            # PhiAgent/backend
ROOT = os.path.dirname(BASE)                                                   # PhiAgent
DP_CH = os.path.join(ROOT, "..", "DeepPhilosophy", "backend", "data", "book_chapters")  # 源（生产真身）


def load_env(path):
    """极简 .env 解析: KEY=VALUE 行, 忽略空行/注释; os.environ 优先"""
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

    if not os.path.isdir(DP_CH):
        sys.exit(f"章节源目录不存在: {DP_CH}")

    auth = oss2.Auth(ak, sk)
    bucket = oss2.Bucket(auth, f"https://{endpoint}", bucket_name)
    PREFIX = "book_chapters/"

    # 1. 远端清单
    remote = {}
    marker = ""
    while True:
        r = bucket.list_objects(PREFIX, marker=marker, max_keys=1000)
        for obj in r.object_list:
            remote[obj.key] = (obj.etag or "").strip('"').lower()  # OSS ETag 大写, 本地 md5 小写, 统一小写比较
        if r.is_truncated:
            marker = r.next_marker
        else:
            break
    print(f"OSS 远端: {len(remote)} 个对象（前缀 {PREFIX}）")

    # 2. 本地清单 + 对比
    local = {}
    for bid in sorted(os.listdir(DP_CH)):
        bd = os.path.join(DP_CH, bid)
        if not os.path.isdir(bd):
            continue
        for fn in sorted(os.listdir(bd)):
            if fn.endswith(".json"):
                local[f"{PREFIX}{bid}/{fn}"] = os.path.join(bd, fn)

    to_up, same = [], 0
    for key, fp in sorted(local.items()):
        md5 = md5_file(fp)
        if remote.get(key) == md5:
            same += 1
        else:
            to_up.append((key, fp, md5))

    print(f"本地: {len(local)} 个 / 无需上传 {same} / 需上传 {len(to_up)}")
    if prune:
        stale = [k for k in remote if k not in local]
        print(f"远端残留待删: {len(stale)}")
        if not dry:
            for k in stale:
                bucket.delete_object(k)
            print(f"已删 {len(stale)}")

    if dry:
        for key, _, _ in to_up[:10]:
            print("  [dry] +", key)
        if len(to_up) > 10:
            print(f"  ... 共 {len(to_up)} 个")
        print("DRY-RUN — 未做任何上传")
        return

    if not to_up:
        print("无需上传, 全部一致")
        return

    # 3. 并发上传（小文件, 直接读内存; 失败重试 2 次）
    lock = threading.Lock()
    ok, fail = 0, []
    state = {"n": 0, "total": len(to_up)}

    def up(key, fp, _md5):
        last_err = None
        for attempt in range(3):
            try:
                with open(fp, "rb") as f:
                    bucket.put_object(key, f, headers={"Content-Type": "application/json"})
                with lock:
                    state["n"] += 1
                    if state["n"] % 500 == 0 or state["n"] == state["total"]:
                        print(f"  进度 {state['n']}/{state['total']}")
                return
            except Exception as e:
                last_err = e
        with lock:
            fail.append((key, str(last_err)))

    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(lambda t: up(*t), to_up))

    print(f"上传完成: 成功 {state['n']} / 失败 {len(fail)}")
    for k, e in fail[:10]:
        print(f"  ✗ {k}: {e}")
    if fail:
        sys.exit(1)


if __name__ == "__main__":
    main()
