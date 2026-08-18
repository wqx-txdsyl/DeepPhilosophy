import os
from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from models import SyncDeleteRequest
import config
import guard

router = APIRouter()

# 鉴权说明（审计 S3 加固）: upload/delete 原无鉴权, 匿名可写/删知识库文件。
# 现复用 ADMIN_PASSWORD 管理口令（X-Admin-Password 请求头, 与 admin 端点同源）:
#   - 未配置 ADMIN_PASSWORD → 503 拒绝（生产默认关, 端点不可用）
#   - 本地开发: 在 backend/.env 设置 ADMIN_PASSWORD=你的口令 后, 请求带该头即可启用

@router.post("/api/sync/upload")
async def sync_upload(file: UploadFile = File(...), _g: dict = Depends(guard.require_admin)):
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
    # N6（audit 2026-08-18）: 书库变更 → 失效 agent 进程内缓存（books.json/章节/embedding）
    from routes.agent import invalidate_agent_cache
    invalidate_agent_cache()
    return {"status": "ok", "path": safe_name, "size": len(content)}

@router.post("/api/sync/delete")
async def sync_delete(req: SyncDeleteRequest, _g: dict = Depends(guard.require_admin)):
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
        # N6（audit 2026-08-18）: 书库变更 → 失效 agent 进程内缓存
        from routes.agent import invalidate_agent_cache
        invalidate_agent_cache()
        return {"status": "ok", "deleted": safe_path}
    return {"status": "not_found", "path": safe_path}
