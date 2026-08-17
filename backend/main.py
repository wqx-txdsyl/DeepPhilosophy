"""
DeepPhilosophy 云端 API 服务器 — 应用装配入口
业务端点全部拆分至 routes/ 模块（2026-08-15）:
  books     → routes/books.py    （列表/标签/详情/render/图片/下载）
  authors   → routes/authors.py  （filters/详情/列表）
  upload    → routes/upload.py   （附件→文本/识图）
  account   → routes/account.py  （个性化资料/删除账户）
  health/stats/auth/history/user/admin/sync/knowledge/ai/agent/text → 对应 routes/*.py
公共逻辑 → services/（book_scanner / summaries / tag_utils）+ modules/ + auth.py + db.py
"""
import os
import sys
import time
import threading
from datetime import datetime
from loguru import logger

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

import config
from auth import init_db
from services.book_scanner import scan_books
from services.summaries import load_summaries_cache

# ============================================================
# FastAPI 应用
# ============================================================
app = FastAPI(
    title="DeepPhilosophy API",
    description="哲学爱好者知识库云端服务",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://deepphilosophy.top",
        "https://deepphilosophy.pages.dev",
        "https://deepphilosophy.vercel.app",
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:8000",
    ],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_timer_middleware(request: Request, call_next):
    t0 = time.time()
    resp = await call_next(request)
    logger.debug(f"[timer] {request.url.path} {time.time() - t0:.2f}s")
    return resp


@app.middleware("http")
async def global_middleware(request: Request, call_next):
    """统一中间件：访问统计 + 静态资源缓存 + CSP（S9）"""
    import admin as admin_module
    response = await call_next(request)
    path = request.url.path
    # 访问统计（跳过管理员路径; S14 已改内存聚合, 直接调用不阻塞事件循环）
    if not path.startswith("/api/admin"):
        try:
            admin_module.record_visit(path)
        except Exception:
            pass
    # S9（audit 2026-08-17）: 全站 CSP——HTML 响应补安全头（覆盖同源 FastAPI 静态托管;
    # 若生产走 OSS/CF Pages 需在托管层配置同等 header）。/docs /redoc 排除, 避免破坏 Swagger UI
    if ((response.headers.get("content-type") or "").startswith("text/html")
            and not path.startswith(("/docs", "/redoc"))):
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://deepphilosophy.oss-cn-shanghai.aliyuncs.com; "
            "style-src 'self' 'unsafe-inline' https://deepphilosophy.oss-cn-shanghai.aliyuncs.com; "
            "img-src 'self' data: blob: https://deepphilosophy.oss-cn-shanghai.aliyuncs.com; "
            "connect-src 'self' https:; "
            "font-src 'self' data: https://deepphilosophy.oss-cn-shanghai.aliyuncs.com; "
            "object-src 'none'; base-uri 'self'; frame-src 'none'; form-action 'self'"
        )
    # 静态资源强缓存（1年）
    if path.startswith(("/gene/", "/assets/", "/icons/")) and not path.startswith("/api/"):
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    elif path.startswith("/schools/") and not path.startswith("/api/"):
        response.headers["Cache-Control"] = "public, max-age=3600"
    elif path.startswith("/philosopher/") and not path.startswith("/api/"):
        response.headers["Cache-Control"] = "public, max-age=3600"  # 1 hour, not 1 year (portraits get updated)
    return response


# 初始化用户数据库（本地表立即可用，云端恢复后台进行）
init_db()


# 后台预热（延迟到所有函数定义完毕后启动，避免 race condition）
def _warmup():
    try:
        scan_books(force=True)
        load_summaries_cache()
        logger.info("Books cache pre-loaded")
    except Exception as e:
        logger.warning(f"Books pre-load failed (non-fatal): {e}")
    try:
        from db import NAME_ALIASES, PHILOSOPHERS
        logger.info(f"Authors ready: {len(PHILOSOPHERS)} philosophers loaded")
    except Exception as e:
        logger.warning(f"Authors pre-load failed (non-fatal): {e}")


# ============================================================
# 路由注册（业务端点全部在 routes/ 模块）
# ============================================================
from routes.health import router as health_router
from routes.auth_routes import router as auth_router
from routes.user import router as user_router
from routes.admin_routes import router as admin_router
from routes.sync import router as sync_router
from routes.knowledge import router as knowledge_router
from routes.ai import router as ai_router
from routes.history import router as history_router
from routes.agent import router as agent_router
from routes.text import router as text_router
from routes.books import router as books_router
from routes.authors import router as authors_router
from routes.upload import router as upload_router
from routes.account import router as account_router

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(admin_router)
app.include_router(sync_router)
app.include_router(knowledge_router)
app.include_router(ai_router)
app.include_router(history_router)
app.include_router(text_router)
app.include_router(agent_router)
app.include_router(books_router)
app.include_router(authors_router)
app.include_router(upload_router)
app.include_router(account_router)

# ============================================================
# 静态前端（同源部署，须在 API 路由之后注册）
# ============================================================
_STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(_STATIC_DIR) and os.path.isfile(os.path.join(_STATIC_DIR, "index.html")):
    # 先挂 assets，再挂根路由
    app.mount("/assets", StaticFiles(directory=os.path.join(_STATIC_DIR, "assets")), name="spa_assets")
    if os.path.isdir(os.path.join(_STATIC_DIR, "gene")):
        app.mount("/gene", StaticFiles(directory=os.path.join(_STATIC_DIR, "gene")), name="gene_assets")
    if os.path.isdir(os.path.join(_STATIC_DIR, "schools")):
        app.mount("/schools", StaticFiles(directory=os.path.join(_STATIC_DIR, "schools")), name="school_assets")
    if os.path.isdir(os.path.join(_STATIC_DIR, "icons")):
        app.mount("/icons", StaticFiles(directory=os.path.join(_STATIC_DIR, "icons")), name="icon_assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """SPA fallback: 非 API 路径返回 index.html
        加固: 防路径遍历——resolve 后必须仍位于 _STATIC_DIR 内, 否则回退 index.html"""
        static_root = os.path.abspath(_STATIC_DIR)
        if full_path:
            fp = os.path.abspath(os.path.join(_STATIC_DIR, full_path))
            if not (fp == os.path.join(static_root, "index.html") or fp.startswith(static_root + os.sep)):
                fp = os.path.join(_STATIC_DIR, "index.html")
        else:
            fp = os.path.join(_STATIC_DIR, "index.html")
        if os.path.isfile(fp):
            return FileResponse(fp)
        return FileResponse(os.path.join(_STATIC_DIR, "index.html"))

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(_STATIC_DIR, "index.html"))


# ============================================================
# 启动
# ============================================================
threading.Thread(target=_warmup, daemon=True).start()


if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("  DeepPhilosophy × PhiAgent 统一后端（智能体 + 平台 API）")
    logger.info("=" * 50)
    books = scan_books()
    logger.info(f"  Books: {len(books)}")
    logger.info(f"  Data: {config.KNOWLEDGE_DIR}")
    logger.info(f"  API: http://0.0.0.0:{config.SERVER_PORT}")
    logger.info(f"  Docs: http://0.0.0.0:{config.SERVER_PORT}/docs")
    logger.info("=" * 50)
    uvicorn.run(app, host=config.SERVER_HOST, port=config.SERVER_PORT)
