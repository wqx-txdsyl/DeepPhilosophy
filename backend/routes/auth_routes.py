from fastapi import APIRouter, HTTPException, Depends
from models import RegisterRequest, LoginRequest
from auth import register, login
from auth_deps import auth_required  # S15: 统一鉴权依赖（原 4 处复制实现收敛为单一来源）
import guard

router = APIRouter()

@router.post("/api/auth/register")
async def api_register(req: RegisterRequest, _ip: str = Depends(guard.auth_guard)):
    result = register(req.username, req.password)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.post("/api/auth/login")
async def api_login(req: LoginRequest, _ip: str = Depends(guard.auth_guard)):
    result = login(req.username, req.password)
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["error"])
    return result

@router.get("/api/auth/profile")
async def api_profile(user: dict = Depends(auth_required)):
    """获取用户信息 + 个性化资料"""
    from auth import get_profile
    return {"username": user["username"], "id": user["id"],
            "profile": get_profile(user["id"])}
