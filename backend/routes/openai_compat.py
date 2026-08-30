# -*- coding: utf-8 -*-
"""OpenAI 兼容端点 — 将深哲/尼采原生引擎（LangGraph）暴露为 /v1/chat/completions。

让 Hermes 等 OpenAI 兼容客户端把深哲/尼采当作「模型」直连：
  切换后，用户的每条消息直接进入 stream_agent 引擎——LangGraph 编排、
  工具调用（原典检索/思辨/脑图…）、DeepSeek 推理全程引擎原生。

事件映射（对齐 Hermes 渲染）:
  - thought_stream / thought  → delta.reasoning_content（思考过程渲染）
  - token                    → delta.content
  - 【《书名》·章节】引用      → markdown 链接 [【《书》·章】](/cite/<书>/<章>)，
    点击经 302 跳转 DeepPhilosophy 阅读器（deepphilosophy.top/reader/<id>?ch=<idx>）
"""
import json
import re
import time
import uuid
from urllib.parse import quote

from fastapi import APIRouter
from fastapi.responses import RedirectResponse, StreamingResponse
from pydantic import BaseModel

router = APIRouter()

# 【《书名》·章节】或【《书名》】引用（AI 输出可能夹行内符号，逐字匹配闭合）
CITE_RE = re.compile(r"【《([^》]+)》·?([^】]*)】")

AGENT_ALIASES = {"zhe": "general", "nietzsche": "nietzsche"}

_CITE_BASE = "http://127.0.0.1:8011"


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str = "zhe"
    messages: list[ChatMessage] = []
    stream: bool = True


def _cite_markdown(m: re.Match) -> str:
    book, chapter = m.group(1), m.group(2)
    suffix = f"·{chapter}" if chapter else ""
    url = f"{_CITE_BASE}/cite/{quote(book)}/{quote(chapter)}"
    return f"[【《{book}》{suffix}】]({url})"


def convert_cites(text: str) -> str:
    """非流式聚合回答：整段转换引用为 markdown 链接。"""
    return CITE_RE.sub(_cite_markdown, text)


def _convert_buffered(buf: str) -> tuple[str, str]:
    """流式缓冲转换：buf 尾部若含未闭合【则保留等待后续分片。

    返回 (可安全输出, 剩余待定缓冲)。"""
    out = ""
    while True:
        m = CITE_RE.search(buf)
        if m and m.end() <= len(buf):
            out += buf[: m.start()] + _cite_markdown(m)
            buf = buf[m.end():]
        else:
            i = buf.rfind("【")
            if i >= 0:
                out += buf[:i]
                buf = buf[i:]
            else:
                out += buf
                buf = ""
            break
    return out, buf


def _chunk(cid: str, delta: dict, finish=None) -> str:
    body = {
        "id": cid,
        "object": "chat.completion.chunk",
        "model": "zhe",
        "created": int(time.time()),
        "choices": [{"index": 0, "delta": delta, "finish_reason": finish}],
    }
    return f"data: {json.dumps(body, ensure_ascii=False)}\n\n"


@router.get("/v1/models")
async def list_models():
    """OpenAI 兼容模型列表（供 Hermes /model 验证与模型发现）。"""
    return {
        "object": "list",
        "data": [
            {"id": "zhe", "object": "model", "owned_by": "phiagent"},
            {"id": "nietzsche", "object": "model", "owned_by": "phiagent"},
        ],
    }


@router.get("/cite/{book}/{chapter}")
async def cite_redirect(book: str, chapter: str = ""):
    """引用跳转：/api/cite 解析 → 302 到 DeepPhilosophy 阅读器。

    catalog（409 部精选）未命中时，fallback 到向量检索（引擎引用同一数据源），
    覆盖《查拉图斯特拉如是说》这类在向量库但不在 catalog 的原典。"""
    from routes.agent import api_cite

    res = await api_cite(book=book, chapter=chapter)
    if not res or res.get("error") or res.get("matched") is False:
        # fallback: 向量检索定位（异步线程化，避免阻塞事件循环）
        try:
            import asyncio

            from routes.agent_tools_retrieval import _exec_search_books

            r = await asyncio.to_thread(
                _exec_search_books, {"query": f"{book} {chapter}".strip(), "limit": 3}
            )
            results = (r or {}).get("results") or []
            if results:
                hit = results[0]
                url = f"https://deepphilosophy.top/reader/{hit['book_id']}?ch={hit['chapter_idx']}"
                return RedirectResponse(url, status_code=302)
        except Exception:
            pass
        return {"error": res.get("error") if res else "未匹配", "book": book, "chapter": chapter}
    url = f"https://deepphilosophy.top/reader/{res['book_id']}?ch={res.get('chapter_idx', 0)}"
    return RedirectResponse(url, status_code=302)


@router.post("/v1/chat/completions")
async def chat_completions(req: ChatRequest):
    cid = "chatcmpl-phi-" + uuid.uuid4().hex[:12]
    agent = AGENT_ALIASES.get(req.model, "general")
    history = [{"role": m.role, "content": m.content} for m in req.messages[:-1]]
    question = req.messages[-1].content if req.messages else ""

    async def events():
        from engine_langgraph import stream_agent

        async for ev in stream_agent(question, history, agent=agent):
            yield ev

    # ── 非流式：聚合 token，整段转换引用 ──
    if not req.stream:
        text = ""
        async for ev in events():
            if ev.get("type") == "token":
                text += ev.get("content") or ""
        return {
            "id": cid,
            "object": "chat.completion",
            "model": req.model,
            "created": int(time.time()),
            "choices": [
                {"index": 0, "message": {"role": "assistant", "content": convert_cites(text)}, "finish_reason": "stop"}
            ],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }

    # ── 流式：思考 → reasoning_content；回答 → content（引用转链接） ──
    async def gen():
        buf = ""
        async for ev in events():
            t = ev.get("type")
            c = ev.get("content") or ""
            if t in ("thought_stream", "thought") and c:
                yield _chunk(cid, {"reasoning_content": c})
            elif t == "token" and c:
                out, buf = _convert_buffered(buf + c)
                for ch in out:
                    yield _chunk(cid, {"content": ch})
        if buf:
            for ch in buf:
                yield _chunk(cid, {"content": ch})
        yield _chunk(cid, {}, "stop")
        yield "data: [DONE]\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")
