# -*- coding: utf-8 -*-
"""Upload all books from F:/philosophy to Render server"""
import sys, os, time, requests

sys.stdout.reconfigure(encoding='utf-8')

API = "https://deepphilosophy.onrender.com"
LOCAL = "F:/philosophy"

def wait_for_health():
    """Wait for server to be ready"""
    for i in range(12):
        try:
            r = requests.get(f"{API}/api/health", timeout=30)
            if r.status_code == 200:
                print("Server ready")
                return True
        except:
            pass
        print(f"  Waiting... ({i+1}/12)")
        time.sleep(15)
    return False

def upload_file(rel_path, full_path):
    """Upload a single file"""
    file_size_mb = os.path.getsize(full_path) / (1024*1024)
    print(f"  [{file_size_mb:.1f}MB] {rel_path} ... ", end="", flush=True)
    try:
        with open(full_path, "rb") as f:
            r = requests.post(
                f"{API}/api/sync/upload",
                files={"file": (rel_path, f)},
                timeout=600,
            )
        if r.status_code == 200:
            print("OK")
            return True
        else:
            print(f"FAIL HTTP {r.status_code}")
            return False
    except Exception as e:
        print(f"FAIL: {e}")
        return False

def main():
    print("=" * 60)
    print("Upload books to DeepPhilosophy")
    print("=" * 60)

    if not wait_for_health():
        print("Server not reachable. Try again later.")
        return

    # Collect files
    files = []
    for root, dirs, filenames in os.walk(LOCAL):
        for f in filenames:
            ext = os.path.splitext(f)[1].lower()
            if ext in ('.pdf', '.epub', '.txt', '.md'):
                full = os.path.join(root, f)
                rel = os.path.relpath(full, LOCAL).replace("\\", "/")
                files.append((rel, full))

    print(f"\n{len(files)} files to upload\n")

    ok = 0
    fail = 0
    for i, (rel, full) in enumerate(files, 1):
        print(f"[{i}/{len(files)}]", end=" ")
        if upload_file(rel, full):
            ok += 1
        else:
            fail += 1

    print(f"\nDone: {ok} uploaded, {fail} failed")

    # Init knowledge base
    if ok > 0:
        print("\nRebuilding knowledge base (this may take 5-10 min)...")
        try:
            r = requests.post(f"{API}/api/knowledge/init", timeout=1800)
            data = r.json()
            print(f"  Books indexed: {data.get('documents_indexed', 0)}")
            print(f"  Chunks: {data.get('chunks', 0)}")
            print(f"  Skipped (scanned/empty): {data.get('skipped', 0)}")
        except Exception as e:
            print(f"  Warning: knowledge init may still be running: {e}")

if __name__ == "__main__":
    main()
