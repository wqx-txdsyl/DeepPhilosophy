"""Model boundary: deterministic offline model or an explicitly enabled HTTP API."""
import asyncio
import json
import os
from urllib.parse import urlparse
import httpx

def current_turn(messages):
    index = max(i for i, message in enumerate(messages) if message["role"] == "user")
    return messages[index:]

class MockModel:
    """Scripted plumbing test. It does NOT measure intelligence or answer quality."""
    async def decide(self, messages, tools):
        turn = current_turn(messages)
        results = [json.loads(m["content"]) for m in turn if m["role"] == "tool"]
        if not results:
            name, args = "search_library", {"query": turn[0]["content"]}
        elif isinstance(results[-1], list) and results[-1]:
            name, args = "read_passage", {"passage_id": results[-1][0]["id"]}
        else:
            return {"role": "assistant", "content": "可以整理已有材料。"}
        return {"role": "assistant", "content": "", "tool_calls": [{
            "id": f"call-{len(results)}", "type": "function", "function": {
                "name": name, "arguments": json.dumps(args, ensure_ascii=False),
            },
        }]}

    async def stream(self, messages):
        results = [json.loads(m["content"]) for m in current_turn(messages) if m["role"] == "tool"]
        passages = [r for r in results if isinstance(r, dict) and "text" in r and "id" in r]
        if passages:
            p = passages[-1]
            answer = f"离线演示：以下是教学材料摘要，不是哲学家原文。\n{p['text']} [{p['id']}]"
        else:
            answer = "离线演示：当前教学材料不足以回答这个问题。请尝试提问：自由与责任有什么关系？"
        # Replay is explicit in mock mode; real mode consumes upstream deltas.
        for start in range(0, len(answer), 8):
            await asyncio.sleep(0)
            yield answer[start:start + 8]

class HttpModel:
    """Subset of a Chat Completions-compatible protocol; provider differences matter."""
    def __init__(self):
        self.key = os.environ.get("PHI_API_KEY", "")
        self.base = os.environ.get("PHI_API_BASE", "https://api.deepseek.com").rstrip("/")
        self.name = os.environ.get("PHI_MODEL", "")
        if not self.key or not self.name:
            raise ValueError("真实模式需要 PHI_API_KEY 和 PHI_MODEL")
        if not self.base.startswith("https://"):
            raise ValueError("真实模式的远程 API 地址必须使用 HTTPS")

    def client(self):
        return httpx.AsyncClient(
            base_url=self.base + "/", timeout=httpx.Timeout(60, connect=10),
            headers={"Authorization": f"Bearer {self.key}"},
        )

    def provider_options(self):
        # DeepSeek currently defaults to thinking mode; this teaching adapter
        # explicitly uses non-thinking mode to avoid a different history protocol.
        if urlparse(self.base).hostname == "api.deepseek.com":
            return {"thinking": {"type": "disabled"}}
        return {}

    async def decide(self, messages, tools):
        async with self.client() as client:
            response = await client.post("chat/completions", json={
                "model": self.name, "messages": messages, "tools": tools,
                "stream": False, "max_tokens": 1000,
                **self.provider_options(),
            })
            response.raise_for_status()
            msg = response.json()["choices"][0]["message"]
            # Deliberately supports ordinary non-thinking chat models only.
            return {key: value for key, value in msg.items()
                    if key in {"role", "content", "tool_calls"} and value is not None}

    async def stream(self, messages):
        async with self.client() as client:
            async with client.stream("POST", "chat/completions", json={
                "model": self.name, "messages": messages,
                "stream": True, "max_tokens": 1500,
                **self.provider_options(),
            }) as response:
                response.raise_for_status()
                completed = False
                async for line in response.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    payload = line[5:].strip()
                    if payload == "[DONE]":
                        completed = True
                        break
                    event = json.loads(payload)
                    if "error" in event:
                        raise RuntimeError("上游返回流式错误")
                    for choice in event.get("choices", []):
                        reason = choice.get("finish_reason")
                        if reason and reason != "stop":
                            raise RuntimeError("上游回答未正常完成")
                        delta = choice.get("delta", {}).get("content")
                        if delta:
                            yield delta
                if not completed:
                    raise RuntimeError("上游连接提前结束")

def build_model():
    mode = os.environ.get("PHI_MODE", "mock")
    if mode == "mock":
        return MockModel()
    if mode == "real":
        return HttpModel()
    raise ValueError("PHI_MODE 只能是 mock 或 real")
