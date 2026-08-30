# -*- coding: utf-8 -*-
"""PhiAgent MCP server — 将 DeepPhilosophy 的智能体能力暴露为 MCP 工具。

供 Hermes Agent（或其他 MCP 客户端）调用，实现三 agent 共存：
  - ask_zhe(question)       深哲本体（LangGraph 引擎，30 工具全量）
  - ask_nietzsche(question) 尼采数字人格（AIAuthor 六库）
  - search_classics(query)  409 部哲学原典向量检索（RAG）

运行（stdio 协议）: cd backend && python mcp_servers/phiagent.py
Hermes 配置（config.yaml mcp_servers）:
  phiagent:
    command: "python"
    args: ["F:/program/Python/DeepPhilosophy/backend/mcp_servers/phiagent.py"]
"""
import asyncio
import json
import os
import sys

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
os.chdir(BACKEND_DIR)  # engine 内部路径解析依赖 cwd=backend

# 加载 backend/.env（DEEPSEEK_API_KEY 等）
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(BACKEND_DIR, ".env"))
except Exception:
    pass

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("phiagent")


def _collect_answer(events) -> str:
    """从 stream_agent 事件流提取最终回答（type=token 的拼接）。"""
    parts = []
    err = None
    for ev in events:
        t = ev.get("type", "")
        if t == "error":
            err = ev.get("content") or ev.get("error") or str(ev)
        elif t == "token":
            c = ev.get("content", "")
            if isinstance(c, str) and c.strip():
                parts.append(c)
    if not parts and err:
        return f"[深哲引擎错误] {err}"
    return "".join(parts).strip()


async def _ask(question: str, agent: str) -> str:
    from engine_langgraph import stream_agent
    events = []
    async for ev in stream_agent(question, [], agent=agent):
        events.append(ev)
    return _collect_answer(events) or json.dumps(events[-3:], ensure_ascii=False)


@mcp.tool()
def ask_zhe(question: str) -> str:
    """向「深哲」智能体提问（LangGraph 引擎，30 工具全量：原典检索/苏格拉底追问/辩论/写作/疏导/生图/概念脑图）。以中文回答。"""
    return asyncio.run(_ask(question, "general"))


@mcp.tool()
def ask_nietzsche(question: str) -> str:
    """以「尼采」数字人格作答（AIAuthor 六库：23 本著作 6488 chunks 语料、1296 实体知识图谱、564 条记忆、早中晚期人格快照）。引文全部出自真实原典。以中文回答。"""
    return asyncio.run(_ask(question, "nietzsche"))


@mcp.tool()
def search_classics(query: str, limit: int = 5) -> str:
    """检索 409 部哲学经典原典（向量相似度，余弦 > 0.35 阈值），返回命中的书名/章节/原文片段。limit 1-10。"""
    from routes.agent_tools_retrieval import _exec_search_books
    res = _exec_search_books({"query": query, "limit": max(1, min(int(limit), 10))})
    if isinstance(res, dict) and res.get("error"):
        return json.dumps(res, ensure_ascii=False)
    return json.dumps(res, ensure_ascii=False)[:8000]


if __name__ == "__main__":
    mcp.run()
