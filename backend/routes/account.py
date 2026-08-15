"""用户账户 API 路由 — 个性化资料更新 / 删除账户
从 main.py 拆分（2026-08-15）
"""
from fastapi import APIRouter, Depends, Header
from models import UpdateProfileRequest

router = APIRouter()


def auth_required(authorization: str = Header(None)) -> dict:
    from fastapi import HTTPException
    from auth import get_user_by_token
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    token = authorization[7:]
    user = get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    return user


@router.put("/api/auth/profile")
async def api_update_profile(req: UpdateProfileRequest, user: dict = Depends(auth_required)):
    """更新个性化资料（昵称/职业/关于我/自定义指令）"""
    from auth import update_profile, get_profile, update_username
    fields = {"nickname": req.nickname, "occupation": req.occupation,
              "about": req.about, "custom_instructions": req.custom_instructions,
              "language": req.language}
    fields = {k: v for k, v in fields.items() if v is not None}
    if req.username:
        update_username(user["id"], req.username)
    update_profile(user["id"], fields)
    return {"success": True, "profile": get_profile(user["id"])}


@router.delete("/api/auth/account")
async def api_delete_account(user: dict = Depends(auth_required)):
    """删除账户及全部数据"""
    from auth import delete_account
    delete_account(user["id"])
    return {"success": True, "message": "账户已删除"}
