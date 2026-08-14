# -*- coding: utf-8 -*-
"""MCP 客户端——深哲接入外部工具生态（插件市场雏形）

配置 MCP_SERVERS（默认空=不启用）:
  MCP_SERVERS = [
      {"name": "demo", "command": sys.executable, "args": ["mcp_servers/demo_server.py"]},
  ]
工具经 MCP 协议动态拉取, 注册为 StructuredTool 挂载进智能体工具集。
"""
import asyncio, json, sys, os
from pathlib import Path
from typing import Any, Optional

from langchain_core.tools import StructuredTool
from pydantic import create_model, Field

# ── 配置: 启用的 MCP 服务器（stdio）──
_BASE = Path(__file__).resolve().parent
MCP_SERVERS = [
    # {"name": "demo", "command": sys.executable, "args": [str(_BASE / "mcp_servers" / "demo_server.py")]},
]

_mcp_tools_cache = None
_mcp_tools_lock = asyncio.Lock()

def _schema_from_json(schema: dict) -> Optional[type]:
    """MCP inputSchema → pydantic model"""
    props = schema.get("properties") or {}
    req = set(schema.get("required") or [])
    fields = {}
    for pname, pmeta in props.items():
        ptype = pmeta.get("type", "string")
        ann = str
        if ptype == "integer":
            ann = int
        elif ptype == "number":
            ann = float
        elif ptype == "boolean":
            ann = bool
        fields[pname] = (ann, Field(description=pmeta.get("description", "")) if pname in req
                         else Field(default=None, description=pmeta.get("description", "")))
    return create_model("mcp_args", **fields) if fields else None


async def _list_tools(cfg):
    """连一次服务器, 拉取工具列表（用完即关）"""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    params = StdioServerParameters(command=cfg["command"], args=cfg.get("args", []))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            return await session.list_tools()


async def _call_tool(cfg, tname, kwargs):
    """调用 MCP 工具（每次调用建连/调用/关闭——绕开 anyio cancel scope 跨任务限制）"""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    params = StdioServerParameters(command=cfg["command"], args=cfg.get("args", []))
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tname, kwargs)
            parts = []
            for item in (result.content or []):
                if getattr(item, "type", "") == "text":
                    parts.append(item.text)
                elif isinstance(item, dict) and item.get("type") == "text":
                    parts.append(item.get("text", ""))
            return "\n".join(parts) if parts else str(result)


async def _load_mcp_tools():
    """拉取所有配置的 MCP server 的工具列表, 包装为 StructuredTool（调用时重连）"""
    if not MCP_SERVERS:
        return []
    tools = []
    for cfg in MCP_SERVERS:
        try:
            listed = await _list_tools(cfg)
            for t in listed.tools:
                tname = f"mcp_{cfg['name']}_{t.name}"
                schema = _schema_from_json(t.inputSchema)

                async def _call(cfg=cfg, tname=t.name, **kwargs):
                    return await _call_tool(cfg, tname, kwargs)

                tools.append(StructuredTool.from_function(
                    func=_call, name=tname,
                    description=f"[MCP·{cfg['name']}] {t.description or t.name}",
                    args_schema=schema))
        except Exception as e:
            print(f"[mcp] 服务器 {cfg['name']} 连接失败: {e}", flush=True)
    return tools


async def get_mcp_tools():
    """获取 MCP 工具（带缓存; async 工具由 tools_node 直接 await）"""
    global _mcp_tools_cache
    if _mcp_tools_cache is None:
        async with _mcp_tools_lock:
            if _mcp_tools_cache is None:
                _mcp_tools_cache = await _load_mcp_tools()
    return _mcp_tools_cache
