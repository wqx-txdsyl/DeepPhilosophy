# -*- coding: utf-8 -*-
"""SSE 流式路由——agent 拆分模块 6/6（R2-2/S21, 2026-08-18 复审）

职责: /api/agent/stream_lg（LangGraph 引擎, SSE——实时思考过程 + 工具调用 + 最终回答逐 token）。
代码从 routes/agent.py 原样搬移（不改逻辑）; 本模块自带 router,
由 agent.py 聚合 include_router（main.py 的 router 引用不变）。
"""
import json
import asyncio
import os
from typing import Optional, List, Literal

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, ConfigDict

import guard
from auth_deps import auth_required
from routes.agent_llm import API_KEY

router = APIRouter()


@router.get('/api/agent/version')
def agent_version(language: Literal['zh','en']='zh'):
    from agent_release import release_descriptor
    return release_descriptor(language)

def _sse(event):
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


async def _heartbeat_stream(events, interval=15):
    """Keep an idle research request alive; disconnect cancels its upstream task."""
    pending = None
    try:
        while True:
            pending = asyncio.create_task(anext(events))
            while not pending.done():
                done, _ = await asyncio.wait({pending}, timeout=interval)
                if not done:
                    yield ": keep-alive\n\n"
            try:
                event = pending.result()
            except StopAsyncIteration:
                return
            pending = None
            yield _sse(event)
    finally:
        if pending is not None:
            if not pending.done():
                pending.cancel()
            await asyncio.gather(pending, return_exceptions=True)
        await events.aclose()

class AgentChatRequest(BaseModel):
    message: str
    history: Optional[List[dict]] = []
    book_id: Optional[str] = None  # 阅读语境（来自阅读器的提问）
    agent: str = "general"         # 智能体广场: general=深哲; nietzsche 等=哲学家智能体
    language: Optional[str] = None # zh/en——前端语言偏好（匿名用户也能生效; 登录用户以 profile 为准）
    conversation_id: Optional[str] = None  # Phase A (A1): tool loop 观测上下文（可选）
    message_id: Optional[str] = None       # Phase A (A1): 单条消息 id（可选, 缺省自动生成）


def agent_access(req: AgentChatRequest, request: Request, authorization: str = Header(None)):
    from soul_agents import is_soul_agent
    if is_soul_agent(req.agent) or (req.agent or 'general') == 'nietzsche' or ((req.agent or 'general') == 'general' and os.getenv('DEEP_AGENT_RUNTIME', 'bare') == 'bare'):
        # Keep identity resolution and per-user memory isolation, but no
        # experiment request rate or daily usage quota.
        return guard.resolve_user(authorization)
    return guard.agent_guard(request, authorization)


class ExplorationRequest(AgentChatRequest):
    answer: str
    previous_questions: List[str] = []


@router.post('/api/agent/exploration')
async def regenerate_exploration(req: ExplorationRequest, _g: dict = Depends(agent_access)):
    from deep_exploration import generate_exploration
    return await asyncio.to_thread(generate_exploration, req.message, req.answer,
                                   req.language or 'zh', req.previous_questions)


class HomeQuestionsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    language: Literal["zh", "en"] = "zh"
    refresh: bool = False


@router.post('/api/agent/home-questions')
async def home_questions(req: HomeQuestionsRequest, user: dict = Depends(auth_required)):
    from home_questions import generate_home_questions
    result = await asyncio.to_thread(generate_home_questions, user["id"], req.language, req.refresh)
    return JSONResponse(result, headers={"Cache-Control":"private, no-store"})

# ═══════════════════════════════════════════════════════
# LangGraph 引擎路由（v2）: /api/agent/stream_lg
# Claude Code 风格: 思考 → 工具（并行）→ 最终回答; 前端协议不变
# ═══════════════════════════════════════════════════════
@router.post("/api/agent/stream_lg")
async def agent_stream_lg(req: AgentChatRequest, request: Request, authorization: str = Header(None),
                          _g: dict = Depends(agent_access)):
    async def stream_events():
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
        events = elg.stream_agent(req.message, req.history or [], req.agent or "general", custom, language,
                                 conversation_id=req.conversation_id, message_id=req.message_id)
        from soul_agents import is_soul_agent
        if (req.agent or "general") in {"general", "nietzsche"} or is_soul_agent(req.agent):
            frames = _heartbeat_stream(events)
            try:
                async for frame in frames:
                    yield frame
            finally:
                await frames.aclose()
        else:
            async for ev in events:
                yield _sse(ev)

    async def gen():
        from soul_agents import is_soul_agent
        if (req.agent or "general") not in {"general", "nietzsche"} and not is_soul_agent(req.agent):
            async for frame in stream_events():
                yield frame
            return
        from deep_context import current_memory_key, general_memory_key, current_account_id, reset_owned_context
        # Sync FastAPI dependencies execute in a worker context. Their
        # ContextVar writes do not propagate back into this SSE task.
        ip = guard.client_ip(request)
        identity_token = guard.current_user.set({"id": (_g or {}).get("id"), "ip": ip})
        scope_token = current_memory_key.set(general_memory_key(_g, ip, req.conversation_id))
        account_token = current_account_id.set((_g or {}).get("id"))
        stream = stream_events()
        try:
            async for frame in stream:
                yield frame
        finally:
            try:
                await stream.aclose()
            finally:
                reset_owned_context(current_memory_key, scope_token)
                reset_owned_context(current_account_id, account_token)
                reset_owned_context(guard.current_user, identity_token)
    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
