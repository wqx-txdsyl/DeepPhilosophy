# -*- coding: utf-8 -*-
"""O6 Gate A — §22 RAM Regression（尽力而为, 进程内探针）。
序列: idle → general 首题 → nietzsche 首题 → 12 连轮 stream_agent。
真实工具（本地检索/章节读取）+ 脚本化 LLM（无网络）。每步 RSS/USS delta; 检查无单调泄漏。
产出 ram_probe.json"""
import asyncio
import gc
import json
import os
import sys

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
sys.path.insert(0, os.path.join(BASE, "backend"))
os.chdir(os.path.join(BASE, "backend"))

OUT = os.path.join(BASE, "backend", "tools", "_tmp", "o6_gate", "gate_a")

import psutil  # noqa: E402
import langchain_core  # noqa: E402
from langchain_core.language_models.chat_models import BaseChatModel  # noqa: E402
from langchain_core.messages import AIMessage  # noqa: E402

import engine_langgraph as EG  # noqa: E402
import routes.agent as AG  # noqa: E402

PROC = psutil.Process()


class LoopedChat(BaseChatModel):
    """循环脚本: [note+search, note+read, final] × N —— 12+ 轮复用同一序列"""
    idx: int = 0

    @property
    def _llm_type(self):
        return "looped-o6ram"

    def bind_tools(self, tools, **kwargs):
        return self

    def _build(self):
        step = self.idx % 3
        self.idx += 1
        if step == 0:
            return AIMessage(content="先检索定位相关章节。",
                             tool_calls=[{"name": "search_books",
                                          "args": {"query": f"言必有中 出处 {self.idx}"}, "id": f"c{self.idx}"}])
        if step == 1:
            return AIMessage(content="定位到《论语·先进篇》，读取原文核对。",
                             tool_calls=[{"name": "get_chapter",
                                          "args": {"book_id": "lunyu", "chapter_idx": 13}, "id": f"c{self.idx}"}])
        return AIMessage(content=("核验结论：「言必有中」出自《论语·先进篇》，孔子评价闵子骞之语"
                                  f"（第 {self.idx // 3} 轮）。"))

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        from langchain_core.outputs import ChatResult, ChatGeneration
        return ChatResult(generations=[ChatGeneration(message=self._build())])

    def _stream(self, messages, stop=None, run_manager=None, **kwargs):
        from langchain_core.messages import AIMessageChunk
        from langchain_core.outputs import ChatGenerationChunk
        msg = self._build()
        text = msg.content or ""
        for i in range(0, len(text), 12):
            yield ChatGenerationChunk(message=AIMessageChunk(content=text[i:i + 12]))
        for tc in (msg.tool_calls or []):
            yield ChatGenerationChunk(message=AIMessageChunk(
                content="",
                tool_call_chunks=[{"name": tc["name"],
                                   "args": json.dumps(tc.get("args") or {}, ensure_ascii=False),
                                   "id": tc.get("id"), "index": 0, "type": "tool_call_chunk"}]))


def rss_mb():
    gc.collect()
    m = PROC.memory_info()
    try:
        u = PROC.memory_full_info()
        uss = getattr(u, "uss", None)
    except Exception:
        uss = None
    return {"rss_mb": round(m.rss / 1048576, 1),
            "uss_mb": round(uss / 1048576, 1) if uss else None}


def run_turn(agent, question):
    chat = LoopedChat()

    async def _collect():
        evs = []
        async for ev in EG.stream_agent(question, [], agent=agent, language="zh"):
            evs.append(ev)
        return evs

    real_get_llm = EG.get_llm
    EG.get_llm = lambda: chat
    try:
        evs = asyncio.run(_collect())
    finally:
        EG.get_llm = real_get_llm
    done = [e for e in evs if e.get("type") == "done"]
    ans = "".join(e.get("content", "") for e in evs if e.get("type") == "token")
    return {"published": bool(ans.strip()),
            "ok": done[0]["validation"]["result"]["ok"] if done else None,
            "tools": sum(1 for e in evs if e.get("type") == "tool")}


def main():
    steps = []
    steps.append({"step": "00_imports_idle", **rss_mb()})
    r = run_turn("general", "言必有中是什么意思？出自哪里？")
    steps.append({"step": "01_general_first", **rss_mb(), "turn": r})
    r = run_turn("nietzsche", "言必有中是什么意思？出自哪里？")
    steps.append({"step": "02_nietzsche_first", **rss_mb(), "turn": r})
    rounds = []
    for i in range(12):
        agent = "general" if i % 2 == 0 else "nietzsche"
        r = run_turn(agent, f"言必有中出处核验（第 {i + 1} 轮）")
        m = rss_mb()
        rounds.append(m["rss_mb"])
        steps.append({"step": f"03_round_{i + 1:02d}_{agent}", **m, "turn": r})
    # 泄漏判定: 后 10 轮 RSS 线性斜率（MB/轮）与总漂移
    tail = rounds[-10:]
    n = len(tail)
    xs = list(range(n))
    mean_x = sum(xs) / n
    mean_y = sum(tail) / n
    slope = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, tail)) / \
        (sum((x - mean_x) ** 2 for x in xs) or 1)
    drift = tail[-1] - tail[0]
    out = {"steps": steps, "rounds_rss_mb": rounds,
           "leak_check": {"last10_slope_mb_per_round": round(slope, 3),
                          "last10_drift_mb": round(drift, 1),
                          "first_round": rounds[0], "last_round": rounds[-1],
                          "no_monotonic_leak": drift < 30},
           "note": "脚本化 LLM + 真实本地工具（search_books/get_chapter 走生产注册表）;"}
    with open(os.path.join(OUT, "ram_probe.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    for s in steps:
        print(s["step"], s["rss_mb"], "MB", str(s.get("turn", ""))[:80])
    print(json.dumps(out["leak_check"], ensure_ascii=False))


if __name__ == "__main__":
    main()
