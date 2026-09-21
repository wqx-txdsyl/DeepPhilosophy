# -*- coding: utf-8 -*-
"""OpenAI 兼容端点 — 将深哲/尼采原生引擎（LangGraph）暴露为 /v1/chat/completions。

让 Hermes 等 OpenAI 兼容客户端把深哲/尼采当作「模型」直连：
  切换后，用户的每条消息直接进入 stream_agent 引擎——LangGraph 编排、
  工具调用（原典检索/思辨/脑图…）、DeepSeek 推理全程引擎原生。

事件映射（对齐 Hermes 渲染; O5: thought_stream/thought 死映射分支已删——
引擎不再发出该类型, public thinking 走 thinking_summary 通道由客户端按需处理）:
  - token                    → delta.content
  - 【《书名》·章节】引用      → 真实目录匹配后直接链接 deepphilosophy.top。
    历史 /cite 链接仍提供跳转；未匹配时不猜章节或跳到其他书。
"""
import json
import re
import time
import uuid
from primary_links import primary_link

from fastapi import APIRouter
from fastapi.responses import RedirectResponse, StreamingResponse
from pydantic import BaseModel

router = APIRouter()

# 【《书名》·章节】或【《书名》】引用（AI 输出可能夹行内符号，逐字匹配闭合）
CITE_RE = re.compile(r"【《([^》]+)》·?([^】]*)】")

AGENT_ALIASES = {"zhe": "general", "nietzsche": "nietzsche"}

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
    label = f"【《{book}》{suffix}】"
    url = primary_link(book, chapter)
    return f"[{label}]({url})" if url else label


def convert_cites(text: str) -> str:
    """非流式聚合回答：整段转换引用为 markdown 链接。"""
    out, pending = _convert_buffered(text)
    return out + pending


def _convert_buffered(buf: str) -> tuple[str, str]:
    """流式缓冲转换：buf 尾部若含未闭合【则保留等待后续分片。

    返回 (可安全输出, 剩余待定缓冲)。"""
    out = ""
    while buf:
        start = buf.find("【")
        if start < 0:
            # '[' can be the start of a Markdown-wrapped citation next chunk.
            keep = 1 if buf.endswith("[") else 0
            out += buf[:-1] if keep else buf
            buf = buf[-1:] if keep else ""
            break
        wrapped = start > 0 and buf[start - 1] == "["
        if wrapped:
            start -= 1
        out += buf[:start]
        buf = buf[start:]
        m = CITE_RE.match(buf, 1 if wrapped else 0)
        if not m:
            end = buf.find("】")
            if end < 0:
                break
            out += buf[:end + 1]
            buf = buf[end + 1:]
            continue
        end = m.end()
        if wrapped:
            tail = buf[end:]
            if tail in ("", "]"):
                break
            if tail.startswith("]("):
                close = buf.find(")", end + 2)
                if close < 0:
                    break
                end = close + 1
            else:
                out += "["
        out += _cite_markdown(m)
        buf = buf[end:]
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


@router.get("/cite/{book}")
@router.get("/cite/{book}/{chapter:path}")
async def cite_redirect(book: str, chapter: str = ""):
    """Historical citation URL, resolved strictly against real catalogue entries."""
    import asyncio
    url = await asyncio.to_thread(primary_link, book, chapter)
    if not url:
        return {"error": "未能唯一定位原典，请核对书名和章节", "book": book, "chapter": chapter}
    return RedirectResponse(url, status_code=302)


@router.get("/api/primary-link")
async def resolve_primary_link(book: str, chapter: str = ""):
    """Resolve old saved citation links without exposing a loopback URL."""
    import asyncio
    url = await asyncio.to_thread(primary_link, book, chapter)
    return {"url": url, "matched": bool(url)}


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

    # ── 流式：回答 → content（引用转链接） ──
    async def gen():
        buf = ""
        async for ev in events():
            t = ev.get("type")
            c = ev.get("content") or ""
            if t == "token" and c:
                out, buf = _convert_buffered(buf + c)
                for ch in out:
                    yield _chunk(cid, {"content": ch})
        if buf:
            for ch in buf:
                yield _chunk(cid, {"content": ch})
        yield _chunk(cid, {}, "stop")
        yield "data: [DONE]\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")
