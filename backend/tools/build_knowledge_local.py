# -*- coding: utf-8 -*-
"""Build knowledge base locally, then upload vector files to Render."""
import sys, os, time, shutil, tempfile, requests

sys.stdout.reconfigure(encoding='utf-8')

# Add parent project path for config/modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import KNOWLEDGE_DIR as LOCAL_BOOKS_DIR

API = "https://deepphilosophy.onrender.com"
VECTOR_SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "vectordb")
VECTOR_DST = "/tmp/deephilosophy_vectordb"  # temp dir for zipping

print("=" * 60)
print("Build Knowledge Base Locally")
print(f"Books dir: {LOCAL_BOOKS_DIR}")
print("=" * 60)

# Step 1: Build locally
print("\n[1/3] Building vector database locally...")
from modules.document_loader import DocumentLoader
from modules.text_processor import TextProcessor
from modules.embedding import EmbeddingManager
from modules.vector_store import VectorStoreManager

# Clean old
shutil.rmtree(VECTOR_SRC, ignore_errors=True)
os.makedirs(VECTOR_SRC, exist_ok=True)

mgr = EmbeddingManager()
store = VectorStoreManager(embedding_function=mgr.get_embedding_function())
tp = TextProcessor()
loader = DocumentLoader()

import pdfplumber

count = skipped = 0
for root, dirs, filenames in os.walk(LOCAL_BOOKS_DIR):
    for f in filenames:
        ext = os.path.splitext(f)[1].lower()
        if ext not in ('.epub', '.pdf'):
            continue

        file_path = os.path.join(root, f)

        # Quick check for scanned PDFs
        if ext == '.pdf':
            try:
                with pdfplumber.open(file_path) as pdf:
                    chars = sum(len((p.extract_text() or '')) for p in pdf.pages[:3])
                if chars < 200:
                    skipped += 1
                    continue
            except:
                skipped += 1
                continue

        try:
            pages = loader.load_file(file_path)
            if pages:
                full_text = loader.merge_pages_to_text(pages)
                cleaned = tp.clean_text(full_text)
                chunks = tp.split_text(cleaned)
                rel_path = os.path.relpath(file_path, LOCAL_BOOKS_DIR)
                category = loader.extract_category(rel_path)
                store.add_documents(
                    chunks,
                    [{'source': f, 'category': category} for _ in chunks],
                    doc_id_prefix=f.replace('.', '_')[:50],
                )
                count += 1
                print(f"  [{count}] {f}")
        except Exception as e:
            print(f"  SKIP: {f} ({e})")

stats = store.get_collection_stats()
print(f"\nDone: {count} docs, {skipped} skipped, {stats['chunk_count']} chunks")

# Step 2: Find vector files
print("\n[2/3] Preparing vector files for upload...")
vector_dir = None
for root, dirs, files in os.walk(VECTOR_SRC):
    for d in dirs:
        if d != "__pycache__":
            vector_dir = os.path.join(root, d)
            break
    if vector_dir:
        break

if not vector_dir:
    print("ERROR: Could not find ChromaDB data directory")
    sys.exit(1)

# Collect chroma files
chroma_files = []
for root, dirs, files in os.walk(vector_dir):
    for f in files:
        chroma_files.append(os.path.join(root, f))

print(f"  {len(chroma_files)} vector files in {vector_dir}")

# Step 3: Upload vector files
print("\n[3/3] Uploading vector files to Render...")
# First upload books, then vectors

import json

headers = {}
for i, file_path in enumerate(chroma_files, 1):
    fname = os.path.basename(file_path)
    rel = os.path.relpath(file_path, VECTOR_SRC)
    fsize = os.path.getsize(file_path) / 1024
    print(f"  [{i}/{len(chroma_files)}] {rel} ({fsize:.1f}KB) ...", end=" ", flush=True)
    try:
        with open(file_path, "rb") as fh:
            r = requests.post(
                f"{API}/api/sync/upload",
                files={"file": (f"vectordb/{rel}", fh)},
                timeout=120,
            )
        if r.status_code == 200:
            print("OK")
        else:
            print(f"FAIL {r.status_code}")
    except Exception as e:
        print(f"FAIL: {e}")

# Also upload the vectors to a special endpoint or just rely on file sync
# For now, we need to also update the chroma persist dir
print("\nKnowledge base built locally!")
print(f"Vector files: {vector_dir}")
print(f"\nNow running init on server to use uploaded files...")
try:
    r = requests.post(f"{API}/api/knowledge/init", timeout=1800)
    print(f"  Result: {r.json()}")
except Exception as e:
    print(f"  (init may be running in background): {e}")

print("\nDone!")
