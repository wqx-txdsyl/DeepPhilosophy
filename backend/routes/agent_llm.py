# -*- coding: utf-8 -*-
"""LLM 客户端（DeepSeek, 云端）——agent 拆分模块 1/6（R2-2/S21, 2026-08-18 复审）

职责: .env 加载 + DeepSeek chat 调用（function calling + 思考模式）。
从 routes/agent.py 原样搬移（不改逻辑）; agent.py 聚合 import 并 re-export
API_KEY / API_URL / MODEL / llm_chat（engine_langgraph 依赖 AG.llm_chat 等）。
"""
import json, os, time, urllib.request
from pathlib import Path
from loguru import logger

# ── 路径 ─────────────────────────────────────────────
BASE = Path(__file__).resolve().parent.parent          # backend/

# ── LLM 客户端（DeepSeek, 云端）───────────────────────
def _load_env():
    env_path = BASE.parent / ".env"
    if env_path.exists():
        for line in open(env_path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
_load_env()
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
API_URL = os.environ.get("DP_API_URL", "https://api.deepseek.com").rstrip("/")
MODEL = os.environ.get("AGENT_MODEL", "deepseek-chat")

def llm_chat(messages, tools=None, temperature=0.7, max_tokens=2000, thinking=False):
    """DeepSeek chat 调用（支持 function calling + 思考模式）
    思考模式: reasoning_content 思维链 + 工具调用必须完整回传 reasoning_content（否则 400）
    """
    body = {"model": MODEL, "messages": messages, "max_tokens": max_tokens}
    if thinking:
        body["thinking"] = {"type": "enabled"}
        body["reasoning_effort"] = "medium"   # 思考模式不支持 temperature（high 思考期过长: 30-90s 无输出）
    else:
        body["temperature"] = temperature
    if tools:
        body["tools"] = tools
    data = json.dumps(body).encode()
    req = urllib.request.Request(f"{API_URL}/v1/chat/completions", data=data,
                                 headers={"Content-Type": "application/json",
                                          "Authorization": f"Bearer {API_KEY}"})
    for attempt, wait in enumerate([5, 10, 15]):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", "ignore")[:500]
            logger.warning(f"[llm] HTTP {e.code}: {err_body[:200]}")   # 细节只进日志
            if attempt == 2:
                # 2026-08-14 脱敏: 客户端不携带上游响应体（可能含请求/密钥细节）
                raise Exception(f"DeepSeek API HTTP {e.code}")
            time.sleep(wait)
        except Exception:
            if attempt == 2:
                raise
            time.sleep(wait)
