# -*- coding: utf-8 -*-
"""
dp_grab_cf_assets.py — 从 CF Pages 部署 URL 全量抓取构建产物（含懒加载 chunk）到 dist/assets

背景 2026-08-12/14: 部署流程只抓 index.html 引用的入口文件, 懒加载 chunk 从未同步 OSS
                  → 用户点击详情页 404 "Failed to fetch dynamically imported module"。
                  本地构建 hash ≠ CF git 构建 hash, 必须从部署 URL 抓线上产物。

用法:
  python dp_grab_cf_assets.py <部署URL>               # 抓取全部产物到 app/dist/assets/
  python dp_grab_cf_assets.py <部署URL> --upload      # 抓取 + dp_sync_oss_static.py 上传 + OSS 完整性校验
  python dp_grab_cf_assets.py <部署URL> --verify-only # 只校验当前 OSS 资产完整性（不抓不传）

抓取策略:
  1. 抓 index.html → 提取入口 js/css
  2. 从 JS 文本提取懒加载引用 import("./Xxx-xxx.js") / import("/assets/Xxx.js"), 递归 BFS
  3. 全部下载到 app/dist/assets/（hash 同名, 幂等）

2026-08-14 加固（白屏事故教训, 见 git log d55034ef5 前后）:
  1. 抓取失败自动重试 3 次（指数退避）——部署中间态/网络抖动不再静默漏文件
  2. 抓取后本地完整性校验: index.html 全部引用 + BFS 懒加载图, 缺任一即报错退出（不静默）
  3. --upload 上传后对 OSS 逐引用 HEAD 校验, 缺失即失败退出（防"传了但漏了"）
"""
import io, os, re, sys, time, urllib.request

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))            # DeepPhilosophy/backend
ROOT = os.path.dirname(BASE)                                                   # DeepPhilosophy
DIST_ASSETS = os.path.join(ROOT, "app", "dist", "assets")

OSS_BASE = "https://deepphilosophy.oss-cn-shanghai.aliyuncs.com"
OSS_PREFIX = "app/assets/"

RE_ENTRY = re.compile(r'(?:src|href)="(?:/assets|https://deepphilosophy\.oss-cn-shanghai\.aliyuncs\.com/app/assets)/([A-Za-z0-9_-]+\.(?:js|css))"')
# vite/rolldown 懒加载两种形式: import(`./Xxx.js`) 反引号模板串, __vite__mapDeps 数组 "assets/Xxx.js"
RE_LAZY = re.compile(r'import\(\s*[`\'"]\./([A-Za-z0-9_-]+\.js)[`\'"]\s*\)')
RE_LAZY_ABS = re.compile(r'import\(\s*[`\'"]/assets/([A-Za-z0-9_-]+\.js)[`\'"]\s*\)')
RE_MAPDEPS = re.compile(r'"assets/([A-Za-z0-9_-]+\.js)"')


def grab(url, name, allow_html=False, retries=3):
    """下载 url 指向的部署文件到本地; 返回文件内容(用于解析懒加载)或 b""（失败/HTML 中间态）"""
    last_err = ""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "dp-grab"})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
            # 2026-08-12 教训: CF Pages 部署中间态, /assets/{新hash}.js 未就绪 → SPA fallback 返回 index.html。
            # 若把 HTML 当 JS 存盘并上传 OSS → 线上 JS 变 HTML → 白屏。检测到即丢弃（不覆盖已有真文件）。
            # 仅 assets 启用检测——index.html 本身是 HTML（65cee451f 曾误伤, 导致抓取永远失败）。
            if not allow_html:
                head = data[:200].lstrip().lower()
                if head.startswith(b"<!doctype") or b"<html" in head:
                    print(f"  ⚠ {name} 响应为 HTML（部署中间态/SPA fallback）, 重试中")
                    last_err = "HTML fallback"
                    time.sleep(1 + attempt)
                    continue
            os.makedirs(DIST_ASSETS, exist_ok=True)
            with open(os.path.join(DIST_ASSETS, name), "wb") as f:
                f.write(data)
            print(f"  ✓ {name} ({len(data)} bytes)")
            return data
        except Exception as e:
            last_err = str(e)[:100]
            if attempt < retries - 1:
                time.sleep(1 + 2 ** attempt)
    print(f"  ⚠ 抓取失败 {name}: {last_err}")
    return b""


def verify_oss(names, prefix=OSS_PREFIX):
    """对 OSS 逐引用 HEAD 校验, 返回 (缺失/错误) 列表"""
    bad = []
    for name in sorted(names):
        url = f"{OSS_BASE}/{prefix}{name}"
        try:
            req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "dp-verify"})
            with urllib.request.urlopen(req, timeout=20) as r:
                ct = (r.headers.get("Content-Type") or "").lower()
                if "javascript" not in ct and "css" not in ct and "json" not in ct:
                    bad.append((name, f"Content-Type={ct}"))
        except Exception as e:
            bad.append((name, str(e)[:70]))
    return bad


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    deploy_url = args[0].rstrip("/")
    do_upload = "--upload" in args
    verify_only = "--verify-only" in args

    if verify_only:
        # 只校验: 需要先有 dist/assets 产物作引用图（用线上 index.html + 主 chunk 也可）
        html_path = os.path.join(DIST_ASSETS, "index.html")
        if not os.path.isfile(html_path):
            print("❌ --verify-only 需要先运行一次抓取（本地无 dist/assets/index.html）")
            sys.exit(1)
        html = open(html_path, encoding="utf-8").read()
        names = set(RE_ENTRY.findall(html))
        main_js = [n for n in names if n.endswith(".js") and n.startswith("index-")]
        if main_js:
            mp = os.path.join(DIST_ASSETS, main_js[0])
            if os.path.isfile(mp):
                text = open(mp, encoding="utf-8", errors="replace").read()
                names |= set(RE_LAZY.findall(text) + RE_LAZY_ABS.findall(text) + RE_MAPDEPS.findall(text))
        bad = verify_oss(names)
        if bad:
            print(f"❌ OSS 缺失 {len(bad)} 个资产:")
            for n, e in bad:
                print(f"   {n}: {e}")
            sys.exit(1)
        print(f"✅ OSS 完整性校验通过: {len(names)} 个引用全部 200")
        return

    os.makedirs(DIST_ASSETS, exist_ok=True)
    seen, queue = set(), []
    html = grab(f"{deploy_url}/", "index.html", allow_html=True)
    if not html:
        print("❌ index.html 抓取失败")
        sys.exit(1)
    for m in RE_ENTRY.findall(html.decode("utf-8", "replace")):
        if m not in seen:
            seen.add(m)
            queue.append(m)

    # BFS: 解析 JS 里的懒加载引用
    while queue:
        name = queue.pop(0)
        if name.endswith(".css"):
            continue
        data = grab(f"{deploy_url}/assets/{name}", name)
        if not data:
            continue
        text = data.decode("utf-8", "replace")
        for m in RE_LAZY.findall(text) + RE_LAZY_ABS.findall(text) + RE_MAPDEPS.findall(text):
            if m not in seen:
                seen.add(m)
                queue.append(m)

    # 本地完整性校验: seen 中的每个名字必须有真实产物
    missing_local = [n for n in seen if not os.path.isfile(os.path.join(DIST_ASSETS, n))]
    if missing_local:
        print(f"❌ 本地抓取不完整, 缺失 {len(missing_local)} 个文件（部署中间态或网络失败）:")
        for n in sorted(missing_local):
            print(f"   {n}")
        print("   请稍候重试（等 CF 边缘稳定后）或检查部署 URL")
        sys.exit(1)
    print(f"\n共抓取 {len(seen)} 个文件 → {DIST_ASSETS}")

    if do_upload:
        sync = os.path.join(BASE, "tools", "dp_sync_oss_static.py")
        rc = os.system(f'"{sys.executable}" "{sync}"')
        if rc != 0:
            print("❌ dp_sync_oss_static.py 上传失败")
            sys.exit(1)
        bad = verify_oss(seen)
        if bad:
            print(f"❌ OSS 上传后校验失败, 缺失 {len(bad)} 个资产:")
            for n, e in bad:
                print(f"   {n}: {e}")
            sys.exit(1)
        print(f"✅ OSS 完整性校验通过: {len(seen)} 个引用全部 200")
    else:
        print("（未上传 OSS；需要上传时加 --upload）")


if __name__ == "__main__":
    main()
