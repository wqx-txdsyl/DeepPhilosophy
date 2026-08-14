# -*- coding: utf-8 -*-
"""演示 MCP server（stdio）——验证深哲的外部工具接入链路
运行: python mcp_servers/demo_server.py
能力: 服务器时间 / 回声 / 简单计算
"""
import time
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("phiagent-demo")


@mcp.tool()
def get_server_time() -> str:
    """返回当前服务器时间（本地时区）"""
    return time.strftime("%Y-%m-%d %H:%M:%S")


@mcp.tool()
def echo(text: str) -> str:
    """原样返回输入文本"""
    return text


@mcp.tool()
def add(a: float, b: float) -> float:
    """两个数相加"""
    return a + b


if __name__ == "__main__":
    mcp.run()
