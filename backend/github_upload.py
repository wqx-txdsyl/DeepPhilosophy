"""
Upload philosophy books to GitHub Release using hash-based names.
GitHub API strips CJK from name param, so we use: {md5hash}.{ext}
Manifest maps original path → download URL.

Usage: GITHUB_TOKEN=xxx BOOKS_DIR=F:/philosophy python github_upload.py
"""
import os, sys, json, time, io, hashlib, requests

REPO = "wqx-txdsyl/DeepPhilosophy"
BOOKS_DIR = os.environ.get("BOOKS_DIR", "F:/philosophy")
TOKEN = os.environ.get("GITHUB_TOKEN", "")

def main():
    if not TOKEN:
        print("ERROR: set GITHUB_TOKEN env var"); return
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    sess = requests.Session()
    sess.headers.update({
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    })

    print("=" * 60)
    print("  DeepPhilosophy → GitHub Release (hash names)")
    print("=" * 60)

    # Clean slate
    r = sess.get(f"https://api.github.com/repos/{REPO}/releases")
    for rel in r.json() if r.ok else []:
        sess.delete(f"https://api.github.com/repos/{REPO}/releases/{rel['id']}")
        print(f"Deleted old release {rel['id']}")
        try:
            sess.delete(f"https://api.github.com/repos/{REPO}/git/refs/tags/{rel['tag_name']}")
        except: pass

    r = sess.post(f"https://api.github.com/repos/{REPO}/releases", json={
        "tag_name": "books-v2",
        "name": "DeepPhilosophy 书库 v2",
        "body": f"哲学书籍库 ({time.strftime('%Y-%m-%d')})\n\n文件名使用 MD5 hash（GitHub API 不支持 CJK 文件名）。",
    })
    if r.status_code not in (200, 201):
        print(f"Create release failed: {r.status_code} {r.text[:200]}")
        return
    release = r.json()
    upload_base = release["upload_url"].replace("{?name,label}", "")
    print(f"Release: {release['html_url']}")

    # Scan books
    todo = []
    for root, dirs, files in os.walk(BOOKS_DIR):
        for f in files:
            if not f.lower().endswith(('.pdf', '.epub', '.txt')):
                continue
            full = os.path.join(root, f)
            rel = os.path.relpath(full, BOOKS_DIR).replace("\\", "/")
            ext = os.path.splitext(f)[1].lower()
            # Hash-based asset name: md5(path).ext
            asset_name = hashlib.md5(rel.encode()).hexdigest()[:16] + ext
            todo.append((full, rel, asset_name, ext))
    print(f"Books: {len(todo)}")

    # Upload
    ok = fail = 0
    for i, (full, rel, asset_name, ext) in enumerate(todo):
        mb = os.path.getsize(full) / 1048576
        print(f"  [{i+1}/{len(todo)}] {rel} ({mb:.1f}MB) ...", end=" ", flush=True)

        try:
            with open(full, "rb") as fh:
                r = sess.post(
                    f"{upload_base}?name={asset_name}",
                    data=fh.read(),
                    headers={"Content-Type": "application/octet-stream"},
                    timeout=180,
                )
            if r.status_code in (200, 201):
                print("OK"); ok += 1
            elif r.status_code == 422 and "already_exists" in r.text:
                print("SKIP"); ok += 1
            else:
                print(f"FAIL({r.status_code})"); fail += 1
        except Exception as e:
            print(f"ERR {type(e).__name__}"); fail += 1

        time.sleep(0.2)

    # Build manifest
    r = sess.get(f"https://api.github.com/repos/{REPO}/releases/tags/books-v2")
    if r.ok:
        url_map = {}
        for a in r.json().get("assets", []):
            url_map[a["name"]] = a["browser_download_url"]

        manifest = {}
        for _, rel, asset_name, _ in todo:
            if asset_name in url_map:
                manifest[rel] = url_map[asset_name]

        mp = os.path.join(os.path.dirname(__file__), "data", "github_manifest.json")
        with open(mp, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

        print(f"\n{'='*60}")
        print(f"OK: {ok}, FAIL: {fail}")
        print(f"Manifest: {mp} ({len(manifest)} files)")

if __name__ == "__main__":
    main()
