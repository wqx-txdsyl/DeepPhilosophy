# -*- coding: utf-8 -*-
"""O1-RP1 — Public Thinking Safety（provider 私有推理绝不出现在用户可见 SSE）

架构契约（docs/PHIAGENT_O1_SINGLE_AGENT_CAUSAL_LOOP.md §4, RP1 修订）:
  ① provider reasoning_content（raw chain-of-thought）是 provider-private 数据——
     绝不进入用户可见 SSE。引擎对该通道一律内部丢弃（不转发 / 不累积 / 不落盘 /
     不摘要冒充）; thought_stream 不再由引擎发出。
  ② public Thinking 唯一事实来源 = thinking_summary(_delta), 内容只能来自:
     A. Main Agent 显式公开工作笔记（工具轮内容通道, 铁律 0）;
     B. Main Agent 显式 <rationale>…</rationale>。
  ③ 模型没写公开内容时: 不伪造 Thinking——用户只看机械活动注记（tool_note）
     与工具事件（允许只有 tool activity）。
  ④ runtime 不得摘要 raw CoT 冒充 Agent: _post_reasoning_summary（mini-LLM,
     _gen_summary 变体）与确定性 build_reasoning_summary 兜底均已删除,
     reasoning_summary 事件不再出现在生产流。

sentinel（PRIVATE_REASONING_SENTINEL_7F31）只用于测试注入, 不参与任何生产逻辑——
实现是结构性移除发射路径, 不是生产字符串 blacklist。

测试全部走 production path（真实 LangGraph 图 + 真实工具桩 + 脚本化假 LLM,
按 DeepSeek 思考模式流形在 AIMessageChunk.additional_kwargs 上注入 reasoning_content）,
断言对象是全部 SSE 事件的序列化整体——不是 grep 源码字符串。
"""
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import langchain_core
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, AIMessageChunk
from langchain_core.tools import StructuredTool
import pytest

import engine_langgraph as EG
import routes.agent as AG


SENTINEL = "PRIVATE_REASONING_SENTINEL_7F31"


# ═══════════════════════════════════════════════════════
# 脚本化假 LLM（DeepSeek 思考模式流形: reasoning 分片 → content 分片 → tool_call_chunk）
# ═══════════════════════════════════════════════════════
class ReasoningScriptedChat(BaseChatModel):
    """script 项: {"reasoning": str, "content": str, "tool_calls": [...]}（键均可省略）。"""
    script: list = []
    idx: int = 0

    @property
    def _llm_type(self):
        return "scripted-rp1"

    def bind_tools(self, tools, **kwargs):
        return self

    def _next_msg(self):
        if self.idx >= len(self.script):
            raise AssertionError("脚本耗尽: 引擎发起了脚本之外的 LLM invocation")
        msg = self.script[self.idx]
        self.idx += 1
        return msg

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        msg = self._next_msg()
        return langchain_core.outputs.ChatResult(
            generations=[langchain_core.outputs.ChatGeneration(
                message=AIMessage(content=msg.get("content") or "",
                                  tool_calls=msg.get("tool_calls") or []))])

    def _stream(self, messages, stop=None, run_manager=None, **kwargs):
        msg = self._next_msg()
        # 10 字符小片: sentinel 必然被切碎进多个 chunk（贴近真实 token 流形,
        # 也确保"整串计数"式断言抓不到——必须按用户阅读顺序拼接后再断言）
        for i in range(0, len(msg.get("reasoning") or ""), 10):
            yield langchain_core.outputs.ChatGenerationChunk(
                message=AIMessageChunk(
                    content="",
                    additional_kwargs={"reasoning_content": msg["reasoning"][i:i + 10]}))
        text = msg.get("content") or ""
        for i in range(0, len(text), 12):
            yield langchain_core.outputs.ChatGenerationChunk(
                message=AIMessageChunk(content=text[i:i + 12]))
        for tc in (msg.get("tool_calls") or []):
            yield langchain_core.outputs.ChatGenerationChunk(
                message=AIMessageChunk(
                    content="",
                    tool_call_chunks=[{"name": tc["name"],
                                       "args": json.dumps(tc.get("args") or {}, ensure_ascii=False),
                                       "id": tc.get("id"), "index": 0,
                                       "type": "tool_call_chunk"}]))


# ═══════════════════════════════════════════════════════
# 工具桩（离线确定性, 与 O1 causal loop 同源）
# ═══════════════════════════════════════════════════════
_LUNYU_PASSAGE = ("鲁人为长府，闵子骞曰：“仍旧贯如之何？何必改作？”"
                  "子曰：“夫人不言，言必有中。”")


def _stub_results():
    return {
        "search_books": lambda **a: (
            {"results": [{"book_title": "论语", "chapter_title": "先进篇", "book_id": "lunyu",
                          "chapter_idx": 13, "snippet": _LUNYU_PASSAGE, "score": 0.9}]}),
        "get_chapter": lambda **a: ({"book_id": a.get("book_id"), "chapter_idx": a.get("chapter_idx"),
                                     "title": "先进篇", "text": "先进篇正文……" + _LUNYU_PASSAGE}),
    }


def _fake_tools():
    return [StructuredTool.from_function(func=fn, name=name, description=f"{name} stub")
            for name, fn in _stub_results().items()]


# ═══════════════════════════════════════════════════════
# harness: 跑 production 图, 收集全部 SSE 事件
# ═══════════════════════════════════════════════════════
def _run_stream(question, script):
    real_get_llm, real_get_tools, real_llm_chat = EG.get_llm, EG.get_tools, AG.llm_chat
    _chat = ReasoningScriptedChat(script=list(script))
    EG.get_llm = lambda: _chat
    EG.get_tools = lambda agent: _fake_tools()
    # 收口路径不得调用隐藏 LLM（含被删的事后摘要通道——若复活会在此暴露）
    AG.llm_chat = lambda *a, **k: (_ for _ in ()).throw(AssertionError("隐藏 LLM 调用"))

    async def _collect():
        evs = []
        async for ev in EG.stream_agent(question, [], agent="general", language="zh"):
            evs.append(ev)
        return evs

    try:
        return asyncio.run(_collect())
    finally:
        EG.get_llm, EG.get_tools, AG.llm_chat = real_get_llm, real_get_tools, real_llm_chat


def _of(evs, *types):
    return [e for e in evs if e.get("type") in types]


def _visible_stream_text(evs):
    """用户在 Thinking/回答面板按事件顺序实际读到的文本拼接。
    逐片流式泄漏（sentinel 被切进多个事件）在拼接后会重新聚合——这正是断言语义。"""
    parts = []
    for e in evs:
        if e.get("type") in ("token", "thought_stream", "thinking_summary",
                             "thinking_summary_delta", "tool_note"):
            parts.append(str(e.get("content") or ""))
    return "".join(parts)


def _all_strings(evs):
    """每个事件所有字段中的全部字符串叶子（不保序的全集, 兜底捕获）。"""
    def _walk(v):
        if isinstance(v, str):
            yield v
        elif isinstance(v, dict):
            for x in v.values():
                yield from _walk(x)
        elif isinstance(v, (list, tuple)):
            for x in v:
                yield from _walk(x)
    out = []
    for e in evs:
        out.extend(_walk(e))
    return "".join(out)


def _assert_no_sentinel(evs):
    """sentinel 不得出现在用户可见 SSE 的任何位置（按序拼接 + 全字段两口径）。"""
    assert SENTINEL not in _visible_stream_text(evs), \
        "provider 私有推理泄漏进用户可见流（按序拼接口径）"
    assert SENTINEL not in _all_strings(evs), \
        "provider 私有推理泄漏进用户可见 SSE 事件字段"


# ═══════════════════════════════════════════════════════
# RP1-T1: 私有推理 + 公开工作笔记并存 → sentinel 不泄漏, 笔记照常进 thinking_summary
# ═══════════════════════════════════════════════════════
class TestRp1SentinelWithPublicNote:
    def test_raw_reasoning_never_public_note_still_flows(self):
        script = [
            {"reasoning": SENTINEL + " 第一轮私有推理链片段",
             "content": "先定位《论语》原典，再核对措辞。",
             "tool_calls": [{"name": "search_books", "args": {"query": "言必有中"}, "id": "c1"}]},
            {"reasoning": SENTINEL + " 第二轮私有推理链片段",
             "content": "已定位到先进篇，读取原文逐字核对。",
             "tool_calls": [{"name": "get_chapter", "args": {"book_id": "lunyu", "chapter_idx": 13},
                             "id": "c2"}]},
            {"reasoning": SENTINEL,
             "content": "「言必有中」出自《论语·先进篇》，孔子评价闵子骞之语。以上为最终核验回答。"},
        ]
        evs = _run_stream("言必有中出处", script)
        # ① sentinel 在整个用户可见 SSE 中出现次数 = 0（按序拼接 + 全字段两口径）
        _assert_no_sentinel(evs)
        # ② 公开工作笔记正常进入 thinking_summary（来源 A, provenance=main_agent）
        notes = _of(evs, "thinking_summary")
        joined = "".join(n.get("content", "") for n in notes)
        assert "先定位《论语》原典" in joined
        assert "已定位到先进篇" in joined
        assert all(n.get("initiated_by") == "main_agent" for n in notes)
        # ③ 结构性: 引擎不再发出任何 thought_stream（raw 通道已移除）
        assert _of(evs, "thought_stream") == []
        # ④ runtime 伪思考事件不存在
        assert _of(evs, "reasoning_summary") == []


# ═══════════════════════════════════════════════════════
# RP1-T2: 仅有 reasoning_content、没有任何公开笔记 → 不伪造 Thinking,
#         允许只有 tool activity（tool/tool_start/tool_note）
# ═══════════════════════════════════════════════════════
class TestRp1ReasoningOnlyNoFabrication:
    def test_reasoning_only_tool_round_emits_no_thinking(self):
        script = [
            {"reasoning": SENTINEL + " 只有私有推理, 不写公开笔记",
             "content": "",
             "tool_calls": [{"name": "search_books", "args": {"query": "言必有中"}, "id": "c1"}]},
            {"reasoning": SENTINEL,
             "content": "依据检索片段谨慎回答：该表述见于《论语·先进篇》。"},
        ]
        evs = _run_stream("言必有中出处", script)
        _assert_no_sentinel(evs)
        # 无任何伪造 Thinking（模型没写 → 一条都没有）
        assert _of(evs, "thinking_summary") == []
        assert _of(evs, "thinking_summary_delta") == []
        assert _of(evs, "reasoning_summary") == []
        assert _of(evs, "thought_stream") == []
        # 允许只有 tool activity: 工具事件 + 机械注记照常
        tools = _of(evs, "tool")
        assert [t["name"] for t in tools] == ["search_books"]
        assert all(t.get("initiated_by") == "main_agent" for t in tools)
        notes = _of(evs, "tool_note")
        assert notes and all(n.get("initiated_by") == "runtime_mechanical" for n in notes)
        # 回答正文照常流出
        answer = "".join(e.get("content", "") for e in _of(evs, "token"))
        assert "先进篇" in answer


# ═══════════════════════════════════════════════════════
# RP1-T3: <rationale> 公开摘要通道（来源 B）在私有推理并存时照常工作
# ═══════════════════════════════════════════════════════
class TestRp1RationaleChannelIntact:
    def test_rationale_flows_while_sentinel_suppressed(self):
        script = [
            {"reasoning": SENTINEL,
             "content": "<rationale>先检索定位原典，这是核验出处的必要步骤</rationale>",
             "tool_calls": [{"name": "search_books", "args": {"query": "言必有中"}, "id": "c1"}]},
            {"reasoning": SENTINEL,
             "content": "「言必有中」出自《论语·先进篇》。以上为最终核验回答。"},
        ]
        evs = _run_stream("言必有中出处", script)
        _assert_no_sentinel(evs)
        notes = _of(evs, "thinking_summary")
        assert any("先检索定位原典" in n.get("content", "") for n in notes)
        assert all(n.get("initiated_by") == "main_agent" for n in notes)
        # rationale 标签本身不得泄漏到任何用户可见事件
        assert "<rationale>" not in _all_strings(evs)


# ═══════════════════════════════════════════════════════
# RP1-T4 (U4 zero-tool): 无工具对话 → tools=0, 不凭空 Thinking, 私有推理不展示
# ═══════════════════════════════════════════════════════
class TestRp1ZeroToolConversation:
    def test_zero_tool_no_thinking_no_raw_reasoning(self):
        script = [
            {"reasoning": SENTINEL + " 零工具轮私有推理",
             "content": "这是不需要检索的直接回答：仁的核心是爱人。"},
        ]
        evs = _run_stream("什么是仁", script)
        _assert_no_sentinel(evs)
        done = [e for e in evs if e.get("type") == "done"][-1]
        assert done["causal"]["engine_cognitive_auto_tools"] == 0
        assert done["causal"]["main_agent_tool_decisions"] == 0
        assert _of(evs, "tool") == [] and _of(evs, "tool_start") == []
        # 无工具且无笔记/rationale → 不得凭空产生 Thinking
        assert _of(evs, "thinking_summary") == []
        assert _of(evs, "reasoning_summary") == []
        assert _of(evs, "thought_stream") == []
        # 回答完整流出
        answer = "".join(e.get("content", "") for e in _of(evs, "token"))
        assert "仁的核心是爱人" in answer
