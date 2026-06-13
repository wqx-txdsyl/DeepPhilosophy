"""
上传哲学书库到 GitHub Release（无需信用卡）
使用 GitHub API 逐本上传
"""
import os, sys, json, time, io
import urllib.request, urllib.error

GITHUB_TOKEN = "PLACEHOLDER"  # 脚本接受命令行参数
REPO = "wqx-txdsyl/DeepPhilosophy"
BOOKS_DIR = "F:/philosophy"
TAG = "books-v1"

def api(path, method="GET", data=None, headers_extra=None):
    url = f"https://api.github.com/repos/{REPO}{path}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    if headers_extra:
        for k, v in headers_extra.items():
            req.add_header(k, v)
    if data:
        req.add_header("Content-Type", "application/json")
        req.data = json.dumps(data).encode()
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"API Error {e.code}: {body[:200]}")
        return None

def get_release(tag):
    releases = api("/releases")
    if releases:
        for r in releases:
            if r["tag_name"] == tag:
                return r
    return None

def create_release():
    return api("/releases", method="POST", data={
        "tag_name": TAG,
        "name": "DeepPhilosophy 书库 v1",
        "body": f"哲学书籍库，共 200+ 本。上传时间：{time.strftime('%Y-%m-%d')}",
        "prerelease": False,
    })

def upload_asset(release_id, file_path, asset_name):
    """上传单个文件作为 release asset（自动重试）"""
    import urllib.parse
    url = f"https://uploads.github.com/repos/{REPO}/releases/{release_id}/assets?name={urllib.parse.quote(asset_name, safe='')}"
    with open(file_path, "rb") as f:
        data = f.read()
    for attempt in range(3):
        req = urllib.request.Request(url, method="POST", data=data)
        req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("Content-Type", "application/octet-stream")
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read())
                return result.get("browser_download_url", "")
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            if attempt < 2:
                time.sleep(3)
                continue
            print(f"  Upload failed {e.code}: {body[:100]}")
            return None
        except Exception as e:
            if attempt < 2:
                time.sleep(3)
                continue
            print(f"  Network error: {e}")
            return None

def main():
    global GITHUB_TOKEN
    if len(sys.argv) < 2:
        print("Usage: python upload_to_github.py <GITHUB_TOKEN>")
        return
    GITHUB_TOKEN = sys.argv[1]

    print("=" * 60)
    print("  上传哲学书库到 GitHub Release")
    print("=" * 60)

    # Create or get release
    release = get_release(TAG)
    if not release:
        print("Creating new release...")
        release = create_release()
        if not release:
            print("FAILED to create release")
            return
        print(f"Release created: {release['html_url']}")
    else:
        print(f"Using existing release: {release['html_url']}")

    release_id = release["id"]
    # Get existing assets to skip
    existing = set()
    for a in release.get("assets", []):
        existing.add(a["name"])

    # Scan all books
    files_to_upload = []
    for root, dirs, files in os.walk(BOOKS_DIR):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext not in ('.pdf', '.epub'):
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, BOOKS_DIR).replace("\\", "/")
            # asset name: use original rel path with / → _, replace #→＃
            asset_name = rel.replace("/", "_").replace("#", "＃")
            # URL-encode for upload
            import urllib.parse
            encoded_name = urllib.parse.quote(asset_name, safe='')
            if asset_name not in existing:
                files_to_upload.append((full, asset_name, encoded_name, rel))
            else:
                print(f"  SKIP: {asset_name}")

    print(f"\nTo upload: {len(files_to_upload)} files")
    total = len(files_to_upload)
    for i, (full, asset_name, encoded_name, rel) in enumerate(files_to_upload):
        size_mb = os.path.getsize(full) / 1024 / 1024
        print(f"  [{i+1}/{total}] {asset_name} ({size_mb:.1f}MB)...", end=" ", flush=True)
        url = upload_asset(release_id, full, asset_name)
        if url:
            print("OK")
        else:
            print("FAILED")
            if size_mb > 100:
                print(f"    WARNING: file > 100MB, may hit limits")
        time.sleep(0.3)  # rate limit

    # Generate manifest
    manifest = {}
    release_final = get_release(TAG)
    if release_final:
        for a in release_final.get("assets", []):
            # asset name back to relative path: replace _ back to / (only first 2 underscores)
            parts = a["name"].split("_", 2)
            if len(parts) >= 3:
                rel_path = f"{parts[0]}/{parts[1]}/{parts[2]}"
            else:
                rel_path = a["name"]
            # fix fullwidth hash back
            rel_path = rel_path.replace("＃", "#")
            manifest[rel_path] = a["browser_download_url"]

    manifest_path = os.path.join(os.path.dirname(__file__), "data", "github_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print(f"\nManifest saved: {manifest_path} ({len(manifest)} files)")

if __name__ == "__main__":
    main()
