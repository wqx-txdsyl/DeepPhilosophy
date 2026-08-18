# -*- coding: utf-8 -*-
"""SSE 流式路由——agent 拆分模块 6/6（R2-2/S21, 2026-08-18 复审）

职责: /api/agent/stream_lg（LangGraph 引擎, SSE——实时思考过程 + 工具调用 + 最终回答逐 token）。
代码从 routes/agent.py 原样搬移（不改逻辑）; 本模块自带 router,
由 agent.py 聚合 include_router（main.py 的 router 引用不变）。
"""
import json
from typing import Optional, List

from fastapi import APIRouter, Depends, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

import guard
from routes.agent_llm import API_KEY

router = APIRouter()

def _sse(event):
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

class AgentChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = []
    book_id: Optional[str] = None  # 阅读语境（来自阅读器的提问）
    agent: str = "general"         # 智能体广场: general=深哲; nietzsche 等=哲学家智能体
    language: Optional[str] = None # zh/en——前端语言偏好（匿名用户也能生效; 登录用户以 profile 为准）

# ═══════════════════════════════════════════════════════
# LangGraph 引擎路由（v2）: /api/agent/stream_lg
# Claude Code 风格: 思考 → 工具（并行）→ 最终回答; 前端协议不变
# ═══════════════════════════════════════════════════════
@router.post("/api/agent/stream_lg")
async def agent_stream_lg(req: AgentChatRequest, authorization: str = Header(None),
                          _g: dict = Depends(guard.agent_guard)):
    async def gen():
        import engine_langgraph as elg
        if not API_KEY:
            yield _sse({"type": "error", "content": "未配置 API Key"})
            return
        # 语言偏好: 请求体（前端 localStorage）优先, 登录用户以 profile.language 为准
        custom = None
        language = req.language if req.language in ("zh", "en") else "zh"
        if authorization and authorization.startswith("Bearer "):
            try:
                from auth import get_user_by_token, get_profile
                user = get_user_by_token(authorization[7:])
                if user:
                    prof = get_profile(user["id"])
                    custom = prof.get("custom_instructions")
                    if prof.get("language") in ("zh", "en"):
                        language = prof["language"]
            except Exception:
                pass
        async for ev in elg.stream_agent(req.message, req.history or [], req.agent or "general", custom, language):
            yield _sse(ev)
    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
