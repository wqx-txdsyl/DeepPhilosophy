from fastapi import APIRouter, HTTPException, Header
from models import UpdateProfileRequest, ChangePasswordRequest, AvatarRequest
from auth import get_user_by_token, update_username, change_password
import sqlite3, os

router = APIRouter()

def _get_conn():
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "users.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def _sync_db():
    try:
        from auth import _sync_db as _s
        _s()
    except Exception:
        pass

@router.put("/api/user/profile")
async def api_update_profile(req: UpdateProfileRequest, authorization: str = Header(None)):
    token = (authorization or "").replace("Bearer ", "")
    user = get_user_by_token(token)
    if not user: raise HTTPException(status_code=401, detail="未登录")
    new_name = req.username.strip()
    if not new_name: raise HTTPException(status_code=400, detail="用户名不能为空")
    if not update_username(user["id"], new_name):
        raise HTTPException(status_code=500, detail="更新失败")
    return {"status": "ok", "username": new_name}

@router.put("/api/user/password")
async def api_change_password(req: ChangePasswordRequest, authorization: str = Header(None)):
    token = (authorization or "").replace("Bearer ", "")
    user = get_user_by_token(token)
    if not user: raise HTTPException(status_code=401, detail="未登录")
    ok, err = change_password(user["id"], req.old_password, req.new_password)
    if not ok:
        raise HTTPException(status_code=403 if "原密码" in err else 400, detail=err)
    return {"status": "ok"}

@router.get("/api/user/avatar")
async def api_get_avatar(authorization: str = Header(None)):
    token = (authorization or "").replace("Bearer ", "")
    user = get_user_by_token(token)
    if not user: raise HTTPException(status_code=401, detail="未登录")
    conn = _get_conn()
    row = conn.execute("SELECT avatar FROM users WHERE id = ?", (user["id"],)).fetchone()
    conn.close()
    return {"avatar": row[0] if row and row[0] else ""}

@router.post("/api/user/avatar")
async def api_save_avatar(req: AvatarRequest, authorization: str = Header(None)):
    token = (authorization or "").replace("Bearer ", "")
    user = get_user_by_token(token)
    if not user: raise HTTPException(status_code=401, detail="未登录")
    conn = _get_conn()
    conn.execute("UPDATE users SET avatar = ? WHERE id = ?", (req.avatar, user["id"]))
    conn.commit()
    conn.close()
    _sync_db()
    return {"status": "ok"}
