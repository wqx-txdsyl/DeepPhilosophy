from fastapi import APIRouter, HTTPException, Depends, Header
from models import RegisterRequest, LoginRequest
from auth import register, login, get_user_by_token

router = APIRouter()

def auth_required(authorization: str = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    token = authorization[7:]
    user = get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    return user

@router.post("/api/auth/register")
async def api_register(req: RegisterRequest):
    result = register(req.username, req.password)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.post("/api/auth/login")
async def api_login(req: LoginRequest):
    result = login(req.username, req.password)
    if not result["success"]:
        raise HTTPException(status_code=401, detail=result["error"])
    return result

@router.get("/api/auth/profile")
async def api_profile(user: dict = Depends(auth_required)):
    return {"username": user["username"], "id": user["id"]}
