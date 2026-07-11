from fastapi import APIRouter, HTTPException, Query
import admin as admin_module

router = APIRouter()

@router.get("/api/admin/stats")
async def admin_stats(password: str = Query("")):
    if not admin_module.ADMIN_PASSWORD:
        raise HTTPException(status_code=503, detail="管理后台未配置（请设置 ADMIN_PASSWORD 环境变量）")
    if password != admin_module.ADMIN_PASSWORD:
        raise HTTPException(status_code=403, detail="密码错误")
    stats = admin_module.load_stats()
    users = admin_module.get_users()
    return {"stats": stats, "users": users, "user_count": len(users)}
