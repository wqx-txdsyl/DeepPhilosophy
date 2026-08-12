# -*- coding: utf-8 -*-
"""
dp_grab_cf_assets.py — 从 CF Pages 部署 URL 全量抓取构建产物（含懒加载 chunk）到 dist/assets

背景 2026-08-12: 部署流程只抓 index.html 引用的入口文件, 懒加载 chunk(AuthorDetailPage-*.js 等)
                从未同步 OSS → 用户点击作者详情页 404 "Failed to fetch dynamically imported module"。
                本地构建 hash ≠ CF git 构建 hash, 必须从部署 URL 抓线上产物。

用法:
  python dp_grab_cf_assets.py <部署URL>          # 抓取全部产物到 app/dist/assets/
  python dp_grab_cf_assets.py <部署URL> --upload # 抓取后调 dp_sync_oss_static.py 上传 OSS

抓取策略:
  1. 抓 index.html → 提取入口 js/css
  2. 从 JS 文本提取懒加载引用 import("./Xxx-xxx.js") / import("/assets/Xxx.js"), 递归 BFS
  3. 全部下载到 app/dist/assets/（hash 同名, 幂等）
"""
import io, os, re, sys, urllib.request

if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))            # DeepPhilosophy/backend
ROOT = os.path.dirname(BASE)                                                   # DeepPhilosophy
DIST_ASSETS = os.path.join(ROOT, "app", "dist", "assets")

RE_ENTRY = re.compile(r'(?:src|href)="(?:/assets|https://deepphilosophy\.oss-cn-shanghai\.aliyuncs\.com/app/assets)/([A-Za-z0-9_-]+\.(?:js|css))"')
# vite/rolldown 懒加载两种形式: import(`./Xxx.js`) 反引号模板串, __vite__mapDeps 数组 "assets/Xxx.js"
RE_LAZY = re.compile(r'import\(\s*[`\'"]\./([A-Za-z0-9_-]+\.js)[`\'"]\s*\)')
RE_LAZY_ABS = re.compile(r'import\(\s*[`\'"]/assets/([A-Za-z0-9_-]+\.js)[`\'"]\s*\)')
RE_MAPDEPS = re.compile(r'"assets/([A-Za-z0-9_-]+\.js)"')


def grab(url, name, seen, allow_html=False):
    """下载 url 指向的部署文件到本地; 返回文件内容(用于解析懒加载)"""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "dp-grab"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read()
    except Exception as e:
        print(f"  ⚠ 抓取失败 {url}: {e}")
        return b""
    # 2026-08-12 教训: CF Pages 部署中间态, /assets/{新hash}.js 未就绪 → SPA fallback 返回 index.html。
    # 若把 HTML 当 JS 存盘并上传 OSS → 线上 JS 变 HTML → 白屏。检测到即丢弃（不覆盖已有真文件）。
    # 仅 assets 启用检测——index.html 本身是 HTML（65cee451f 曾误伤, 导致抓取永远失败）。
    if not allow_html:
        head = data[:200].lstrip().lower()
        if head.startswith(b"<!doctype") or b"<html" in head:
            print(f"  ⚠ {name} 响应为 HTML（部署中间态/SPA fallback）, 已丢弃")
            return b""
    os.makedirs(DIST_ASSETS, exist_ok=True)
    with open(os.path.join(DIST_ASSETS, name), "wb") as f:
        f.write(data)
    print(f"  ✓ {name} ({len(data)} bytes)")
    return data


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    deploy_url = args[0].rstrip("/")
    do_upload = "--upload" in args

    os.makedirs(DIST_ASSETS, exist_ok=True)
    seen, queue = set(), []
    html = grab(f"{deploy_url}/", "index.html", seen, allow_html=True)
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
        data = grab(f"{deploy_url}/assets/{name}", name, seen)
        if not data:
            continue
        text = data.decode("utf-8", "replace")
        for m in RE_LAZY.findall(text) + RE_LAZY_ABS.findall(text) + RE_MAPDEPS.findall(text):
            if m not in seen:
                seen.add(m)
                queue.append(m)

    print(f"\n共抓取 {len(seen)} 个文件 → {DIST_ASSETS}")
    if do_upload:
        sync = os.path.join(ROOT, "..", "PhiAgent", "backend", "tools", "dp_sync_oss_static.py")
        os.system(f'"{sys.executable}" "{sync}"')


if __name__ == "__main__":
    main()
