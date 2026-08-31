# -*- coding: utf-8 -*-
"""LLM 客户端（OpenAI 兼容, 可切换供应商）——agent 拆分模块 1/6（R2-2/S21, 2026-08-18 复审）

职责: .env 加载 + chat 调用（function calling + 思考模式）。
从 routes/agent.py 原样搬移（不改逻辑）; agent.py 聚合 import 并 re-export
API_KEY / API_URL / MODEL / llm_chat（engine_langgraph 依赖 AG.llm_chat 等）。

2026-08-30: 供应商可切换（DeepSeek 默认 ↔ 智谱免费档, 改 .env 即切, 代码零改动）:
  DP_API_URL=https://open.bigmodel.cn/api/paas/v4 + AGENT_MODEL=glm-4-flash → 智谱
  （注: glm-4v-* 系列不支持 function calling, 只可用于识图, 不能驱动 agent 工具循环;
    glm-4-flash 可驱动但检索纪律差, 已实测放弃）
  删除上述两行（或缺省）→ DeepSeek deepseek-chat + 思考模式。
  密钥跟随 URL 供应商自动匹配（ZHIPU_API_KEY / DEEPSEEK_API_KEY）, 显式 LLM_API_KEY 永远优先。
  URL 拼接按供应商自适应: 智谱 v4 → /chat/completions; DeepSeek → /v1/chat/completions。
"""
import json, os, time, urllib.request
from pathlib import Path
from loguru import logger

# ── 路径 ─────────────────────────────────────────────
BASE = Path(__file__).resolve().parent.parent          # backend/

# ── LLM 客户端（OpenAI 兼容, 云端）─────────────────────
def _load_env():
    env_path = BASE.parent / ".env"
    if env_path.exists():
        for line in open(env_path, encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
_load_env()
API_URL = os.environ.get("DP_API_URL", "https://api.deepseek.com").rstrip("/")
MODEL = os.environ.get("AGENT_MODEL", "deepseek-chat")
_IS_ZHIPU = "bigmodel.cn" in API_URL or "zhipu" in API_URL
API_KEY = (os.environ.get("LLM_API_KEY")
           or (os.environ.get("ZHIPU_API_KEY") if _IS_ZHIPU else os.environ.get("DEEPSEEK_API_KEY"))
           or "")

def _chat_url():
    """OpenAI 兼容补全端点: 智谱 v4 基址不带 /v1; DeepSeek 风格基址带 /v1"""
    if API_URL.endswith("/v1") or "deepseek" in API_URL:
        return f"{API_URL}/chat/completions" if API_URL.endswith("/v1") else f"{API_URL}/v1/chat/completions"
    return f"{API_URL}/chat/completions"

def llm_chat(messages, tools=None, temperature=0.7, max_tokens=2000, thinking=False):
    """chat 调用（支持 function calling; 思考模式仅 DeepSeek 有效）
    思考模式: reasoning_content 思维链 + 工具调用必须完整回传 reasoning_content（否则 400）
    """
    body = {"model": MODEL, "messages": messages, "max_tokens": max_tokens}
    if thinking and not _IS_ZHIPU:
        body["thinking"] = {"type": "enabled"}
        body["reasoning_effort"] = "medium"   # 思考模式不支持 temperature（high 思考期过长: 30-90s 无输出）
    else:
        body["temperature"] = temperature
    if tools:
        body["tools"] = tools
    data = json.dumps(body).encode()
    req = urllib.request.Request(_chat_url(), data=data,
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
                raise Exception(f"LLM API HTTP {e.code}")
            time.sleep(wait)
        except Exception:
            if attempt == 2:
                raise
            time.sleep(wait)


def llm_stream(messages, tools=None, temperature=0.7, max_tokens=2000, thinking=False):
    """OpenAI 兼容流式 chat（stream=true, 逐 delta 产出; DeepSeek 原生支持）。
    仅用于安全摘要等短文本通道; 失败抛异常（调用方尽力而为跳过）。"""
    body = {"model": MODEL, "messages": messages, "max_tokens": max_tokens, "stream": True}
    if thinking and not _IS_ZHIPU:
        body["thinking"] = {"type": "enabled"}
        body["reasoning_effort"] = "medium"
    else:
        body["temperature"] = temperature
    if tools:
        body["tools"] = tools
    data = json.dumps(body).encode()
    req = urllib.request.Request(_chat_url(), data=data,
                                 headers={"Content-Type": "application/json",
                                          "Authorization": f"Bearer {API_KEY}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        for raw in r:
            line = raw.decode("utf-8", "ignore").strip()
            if not line.startswith("data:"):
                continue
            payload = line[5:].strip()
            if payload == "[DONE]":
                return
            try:
                chunk = json.loads(payload)
            except Exception:
                continue
            choices = chunk.get("choices") or []
            delta = (choices[0].get("delta") or {}) if choices else {}
            piece = delta.get("content") or ""
            if piece:
                yield piece
