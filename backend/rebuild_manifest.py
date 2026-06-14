"""Rebuild github_manifest.json from GitHub Release assets."""
import os, json, sys, io, hashlib, requests

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

TOKEN = os.environ.get("GITHUB_TOKEN", "")
BOOKS_DIR = "F:/philosophy"
MANIFEST_PATH = r"C:\Users\wqx_0\PyCharmProjects\Q&ASystem\DeepPhilosophy\backend\data\github_manifest.json"

if not TOKEN:
    print("ERROR: set GITHUB_TOKEN"); sys.exit(1)

s = requests.Session()
s.headers.update({"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json"})

# Fetch all release assets
r = s.get("https://api.github.com/repos/wqx-txdsyl/DeepPhilosophy/releases/tags/books-v2")
if not r.ok:
    print(f"Failed: {r.status_code} {r.text[:200]}"); sys.exit(1)
all_assets = r.json().get("assets", [])
print(f"Assets on release: {len(all_assets)}")

# Build local hash→path map
hash_to_path = {}
for root, dirs, files in os.walk(BOOKS_DIR):
    for f in files:
        if not f.lower().endswith(('.pdf', '.epub')):
            continue
        full = os.path.join(root, f)
        rel = os.path.relpath(full, BOOKS_DIR).replace("\\", "/")
        ext = os.path.splitext(f)[1].lower()
        asset_name = hashlib.md5(rel.encode()).hexdigest()[:16] + ext
        hash_to_path[asset_name] = rel

# Match
manifest = {}
unmatched = 0
for a in all_assets:
    name = a["name"]
    if name in hash_to_path:
        manifest[hash_to_path[name]] = a["browser_download_url"]
    else:
        unmatched += 1

print(f"Matched: {len(manifest)}")
print(f"Unmatched: {unmatched}")

with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=2)
print(f"Saved {len(manifest)} entries to manifest")
