import os, threading
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
import config
import guard

router = APIRouter()

# 重建互斥锁（审计 S4 加固: 防并发重复触发全量重建 = DoS; 配合 require_admin 鉴权）
_building = False
_building_lock = threading.Lock()

# 鉴权说明（审计 S4 加固）: /api/knowledge/init 原无鉴权, POST 即删库重建。
# 现复用 ADMIN_PASSWORD 管理口令（X-Admin-Password 请求头, 与 admin 端点同源）:
#   - 未配置 ADMIN_PASSWORD → 503 拒绝（生产默认关, 端点不可用）
#   - 本地开发: 在 backend/.env 设置 ADMIN_PASSWORD=你的口令 后, 请求带该头即可启用

@router.post("/api/knowledge/init")
async def init_knowledge_base(_g: dict = Depends(guard.require_admin)):
    global _building
    with _building_lock:
        if _building:
            raise HTTPException(status_code=409, detail="知识库正在重建中，请稍后再试")
        _building = True
    def _build():
        global _building
        try:
            _do_build()
        finally:
            with _building_lock:
                _building = False
            # N6（audit 2026-08-18）: 重建完成后失效 agent 进程内缓存
            # （重建是后台线程, 故在完成点而非端点内调用）
            from routes.agent import invalidate_agent_cache
            invalidate_agent_cache()

    def _do_build():
        from modules.document_loader import DocumentLoader
        from modules.text_processor import TextProcessor
        from modules.embedding import EmbeddingManager
        from modules.vector_store import VectorStoreManager
        import chromadb, pdfplumber
        try:
            old_client = chromadb.PersistentClient(path=config.CHROMA_PERSIST_DIR)
            old_client.delete_collection(config.CHROMA_COLLECTION_NAME)
        except Exception:
            pass
        mgr = EmbeddingManager()
        store = VectorStoreManager(embedding_function=mgr.get_embedding_function())
        tp = TextProcessor()
        loader = DocumentLoader()
        count = skipped = 0
        for root, dirs, files in os.walk(config.KNOWLEDGE_DIR):
            for f in files:
                ext = Path(f).suffix.lower()
                if ext not in ('.epub', '.pdf'):
                    continue
                file_path = os.path.join(root, f)
                if ext == '.pdf':
                    try:
                        with pdfplumber.open(file_path) as pdf:
                            chars = sum(len((p.extract_text() or '')) for p in pdf.pages[:3])
                        if chars < 200:
                            skipped += 1
                            continue
                    except Exception:
                        skipped += 1
                        continue
                try:
                    pages = loader.load_file(file_path)
                    if pages:
                        full_text = loader.merge_pages_to_text(pages)
                        cleaned = tp.clean_text(full_text)
                        chunks = tp.split_text(cleaned)
                        rel_path = os.path.relpath(file_path, config.KNOWLEDGE_DIR)
                        category = loader.extract_category(rel_path)
                        store.add_documents(chunks,
                            [{'source': f, 'category': category} for _ in chunks],
                            doc_id_prefix=f.replace('.', '_')[:50])
                        count += 1
                except Exception:
                    pass
    threading.Thread(target=_build, daemon=True).start()
    return {"status": "started", "message": "Building in background. Check /api/knowledge/stats for progress."}

@router.get("/api/knowledge/stats")
async def knowledge_stats():
    try:
        from modules.vector_store import VectorStoreManager
        from modules.embedding import EmbeddingManager
        mgr = EmbeddingManager()
        store = VectorStoreManager(embedding_function=mgr.get_embedding_function())
        return store.get_collection_stats()
    except Exception:
        return {"document_count": 0, "chunk_count": 0}
