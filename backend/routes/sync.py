import os
from fastapi import APIRouter, HTTPException, UploadFile, File
from models import SyncDeleteRequest
import config

router = APIRouter()

@router.post("/api/sync/upload")
async def sync_upload(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")
    safe_name = file.filename.replace("\\", "/")
    if safe_name.startswith("/") or ".." in safe_name:
        raise HTTPException(status_code=400, detail="非法文件路径")
    if safe_name.startswith("vectordb/"):
        base = config.CHROMA_PERSIST_DIR
        safe_name = safe_name[len("vectordb/"):]
    else:
        base = config.KNOWLEDGE_DIR
    target_path = os.path.join(base, safe_name)
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    content = await file.read()
    with open(target_path, "wb") as f:
        f.write(content)
    return {"status": "ok", "path": safe_name, "size": len(content)}

@router.post("/api/sync/delete")
async def sync_delete(req: SyncDeleteRequest):
    safe_path = req.path.replace("\\", "/")
    if safe_path.startswith("/") or ".." in safe_path:
        raise HTTPException(status_code=400, detail="非法文件路径")
    target_path = os.path.join(config.KNOWLEDGE_DIR, safe_path)
    if os.path.exists(target_path):
        os.remove(target_path)
        try:
            parent = os.path.dirname(target_path)
            if not os.listdir(parent):
                os.rmdir(parent)
        except Exception:
            pass
        return {"status": "ok", "deleted": safe_path}
    return {"status": "not_found", "path": safe_path}
