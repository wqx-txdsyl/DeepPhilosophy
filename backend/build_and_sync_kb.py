# -*- coding: utf-8 -*-
"""Build vector DB locally, upload to Render (bypasses Render memory limits)"""
import sys, os, shutil, tarfile, tempfile, requests

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

API = "https://deepphilosophy.onrender.com"
BOOKS_DIR = os.getenv("PHILOSOPHY_BOOKS_DIR", "F:/philosophy")
VECTOR_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "vectordb")
EXTRACTED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "extracted")

print("=" * 60)
print("Build Knowledge Base Locally + Upload to Render")
print("=" * 60)

# Clean old data
for d in [VECTOR_DIR, EXTRACTED_DIR]:
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d, exist_ok=True)

# Override config paths to local dirs (matching Render's path structure)
import config
config.KNOWLEDGE_DIR = "/app/data/books"
config.CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "vectordb")
config.CHROMA_COLLECTION_NAME = "deephilosophy_knowledge"  # Match Render's config

from modules.document_loader import DocumentLoader
from modules.text_processor import TextProcessor
from modules.embedding import EmbeddingManager
from modules.vector_store import VectorStoreManager

print("\n[1/3] Initializing embedding engine...")
mgr = EmbeddingManager()
store = VectorStoreManager(embedding_function=mgr.get_embedding_function())
tp = TextProcessor()
loader = DocumentLoader()

print("\n[2/3] Processing books (this will take several minutes)...")
import pdfplumber

count = skipped = 0
total_files = 0
for root, dirs, files in os.walk(BOOKS_DIR):
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        if ext in ('.epub', '.pdf'):
            total_files += 1

processed = 0
for root, dirs, files in os.walk(BOOKS_DIR):
    for f in files:
        ext = os.path.splitext(f)[1].lower()
        if ext not in ('.epub', '.pdf'):
            continue

        file_path = os.path.join(root, f)
        processed += 1

        # All files go through loader (OCR handles scanned PDFs automatically)

        try:
            pages = loader.load_file(file_path)
            if pages:
                full_text = loader.merge_pages_to_text(pages)
                cleaned = tp.clean_text(full_text)
                chunks = tp.split_text(cleaned)
                # Use Render-like path for metadata
                rel = os.path.relpath(file_path, BOOKS_DIR).replace("\\", "/")
                category = loader.extract_category(rel)
                metadata = [{'source': f, 'category': category} for _ in chunks]
                store.add_documents(chunks, metadata, doc_id_prefix=f.replace('.', '_')[:50])
                count += 1
                print(f"  [{processed}/{total_files}] OK: {f} ({len(chunks)} chunks)")
        except Exception as e:
            print(f"  [{processed}/{total_files}] ERROR: {f} - {e}")

stats = store.get_collection_stats()
print(f"\nLocal build done: {count} docs, {skipped} skipped, {stats['chunk_count']} chunks")

# Find chroma data directory
chroma_dir = None
for root, dirs, files in os.walk(VECTOR_DIR):
    for d in dirs:
        if d != "__pycache__":
            chroma_dir = os.path.join(root, d)
            break
    if chroma_dir:
        break

if not chroma_dir:
    print("ERROR: No ChromaDB data found!")
    sys.exit(1)

print(f"\n[3/3] Uploading vector database ({len(os.listdir(chroma_dir))} files)...")

# Upload each file
for root, dirs, files in os.walk(chroma_dir):
    for f in files:
        fpath = os.path.join(root, f)
        fsize = os.path.getsize(fpath) / 1024
        rel = os.path.relpath(fpath, VECTOR_DIR)
        print(f"  [{fsize:.0f}KB] {rel} ...", end=" ", flush=True)
        try:
            with open(fpath, "rb") as fh:
                r = requests.post(
                    f"{API}/api/sync/upload",
                    files={"file": (f"vectordb/{rel}", fh)},
                    timeout=120,
                )
            print("OK" if r.status_code == 200 else f"FAIL {r.status_code}")
        except Exception as e:
            print(f"FAIL: {e}")

print("\nDone! Knowledge base synced to Render.")
