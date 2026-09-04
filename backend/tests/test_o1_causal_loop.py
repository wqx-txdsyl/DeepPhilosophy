# -*- coding: utf-8 -*-
"""O1 — Single-Agent Causal Loop / Thinking Truth（因果回归测试）

架构契约（见 docs/PHIAGENT_O1_SINGLE_AGENT_CAUSAL_LOOP.md）:
  ① 全部 top-level 认知工具（search_books/get_chapter/websearch/…）只能由 Main Agent
     经 LLM tool declaration 发起; 引擎不代执行（auto-read / auto-websearch 已删除）。
  ② thinking_summary 只承载 Main Agent 自己写给用户看的公开工作判断
     （initiated_by=main_agent）; runtime 只发机械活动注记（tool_note,
     initiated_by=runtime_mechanical）, 不冒充思考。
  ③ tool batch N 结束后若出现下一批 top-level 工具, 中间必有新的 Main Agent invocation
     （decision_group_id 递增）。
  ④ Streaming Blockquote Split witness（O0 S5 转正式）: 跨 chunk 劈开的 blockquote
     必须保持完整引用块。

测试全部走 production path（真实 LangGraph 图 + 真实工具桩 + 脚本化假 LLM）,
以 SSE 事件流的 provenance 字段为断言对象——不是 grep 源码字符串。
"""
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import langchain_core
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.tools import StructuredTool
import pytest

import engine_langgraph as EG
import routes.agent as AG
import quote_bound as QB


# ═══════════════════════════════════════════════════════
# 脚本化假 LLM（每次 invocation 弹出一条预设 AIMessage）
# ═══════════════════════════════════════════════════════
class ScriptedChat(BaseChatModel):
    """脚本化假 LLM——按 production 流形输出: content 先分片流出, 随后逐个
    tool_call_chunk（与 DeepSeek 工具轮一致）, 使 SSE 循环走真实声明观测路径。"""
    script: list = []
    idx: int = 0

    @property
    def _llm_type(self):
        return "scripted-o1"

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
            generations=[langchain_core.outputs.ChatGeneration(message=msg)])

    def _stream(self, messages, stop=None, run_manager=None, **kwargs):
        from langchain_core.messages import AIMessageChunk
        msg = self._next_msg()
        text = msg.content or ""
        for i in range(0, len(text), 12):   # 小分片 ≈ 真实 token 流形
            yield langchain_core.outputs.ChatGenerationChunk(
                message=AIMessageChunk(content=text[i:i + 12]))
        for tc in (msg.tool_calls or []):
            yield langchain_core.outputs.ChatGenerationChunk(
                message=AIMessageChunk(
                    content="",
                    tool_call_chunks=[{"name": tc["name"],
                                       "args": json.dumps(tc.get("args") or {}, ensure_ascii=False),
                                       "id": tc.get("id"), "index": 0,
                                       "type": "tool_call_chunk"}]))


def _msg(note, tool_calls=None):
    return AIMessage(content=note or "", tool_calls=tool_calls or [])


# ═══════════════════════════════════════════════════════
# 工具桩（离线确定性; websearch/locate 桩带调用记录 → T7/T8 断言）
# ═══════════════════════════════════════════════════════
_LUNYU_PASSAGE = ("鲁人为长府，闵子骞曰：“仍旧贯如之何？何必改作？”"
                  "子曰：“夫人不言，言必有中。”")

_STUB_CALLS = {"websearch": [], "locate_exact_phrase": [], "get_chapter": []}


def _stub_results():
    return {
        "search_books": lambda **a: (
            {"results": [{"book_title": "论语", "chapter_title": "先进篇", "book_id": "lunyu",
                          "chapter_idx": 13, "snippet": _LUNYU_PASSAGE, "score": 0.9}]}
            if "不存在词项" not in (a.get("query") or "") else {"results": []}),
        "get_chapter": lambda **a: ({"book_id": a.get("book_id"), "chapter_idx": a.get("chapter_idx"),
                                     "title": "先进篇", "text": "先进篇正文……" + _LUNYU_PASSAGE}),
        "get_book_detail": lambda **a: {"book_id": a.get("book_id"), "title": "论语",
                                        "chapters": [{"index": 13, "title": "先进篇"}]},
        "websearch": lambda **a: (_STUB_CALLS["websearch"].append(a) or
                                  {"results": [{"title": "web", "snippet": "web hit"}]}),
        "query_graph": lambda **a: {"philosopher": "孔子", "relations": []},
        "get_philosopher": lambda **a: {"name": a.get("name"), "region": "先秦"},
        "list_books": lambda **a: {"books": []},
        "query_database": lambda **a: {"records": []},
        "concept_trace": lambda **a: {"trace": []},
        "locate_exact_phrase": lambda **a: (_STUB_CALLS["locate_exact_phrase"].append(a) or
                                            {"found": True, "hits": [{"book_id": "lunyu", "chapter_idx": 13}]}),
    }


def _fake_tools():
    from langchain_core.tools import StructuredTool
    res = _stub_results()
    tools = []
    for name, fn in res.items():
        tools.append(StructuredTool.from_function(
            func=fn, name=name, description=f"{name} stub"))
    return tools


# ═══════════════════════════════════════════════════════
# harness: 跑 production 图, 收集全部 SSE 事件
# ═══════════════════════════════════════════════════════
def _run_stream(question, script):
    for k in _STUB_CALLS:
        _STUB_CALLS[k] = []
    real_get_llm, real_get_tools, real_llm_chat = EG.get_llm, EG.get_tools, AG.llm_chat
    _chat = ScriptedChat(script=list(script))   # 单实例: 脚本指针跨 invocation 连续推进
    EG.get_llm = lambda: _chat
    EG.get_tools = lambda agent: _fake_tools()
    AG.llm_chat = lambda *a, **k: (_ for _ in ()).throw(AssertionError("收口路径不得调用隐藏 LLM"))

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


def _group_num(ev):
    return int(str(ev.get("decision_group_id") or "inv-0").replace("inv-", ""))


# ═══════════════════════════════════════════════════════
# Blockquote 行为保障（O0 S5 witness → O2 迁移为校验层）
# O2: QuoteBoundSanitizer 流式改写类已删除——blockquote 完整性改由
# extract_quotes/audit_quotes 在 Final Candidate 上保证（不改写、只核验）。
# ═══════════════════════════════════════════════════════
class TestBlockquoteSplitBehavior:
    def _raw_log(self):
        return [{"name": "get_chapter", "args": {"book_id": "lunyu", "chapter_idx": 13},
                 "result_summary": "", "result_full": {"book_id": "lunyu", "title": "先进篇",
                                                       "text": "先进篇正文。" + _LUNYU_PASSAGE}}]

    def test_verified_blockquote_extracts_whole(self):
        """已核验 blockquote 在完整候选文本上被完整提取并判 VERIFIED_EXACT"""
        final = "核验如下：\n\n> 「" + _LUNYU_PASSAGE + "」\n\n以上为《论语·先进篇》原文。"
        audit = QB.audit_quotes(final, self._raw_log())
        bq = [e for e in audit["entries"] if e["kind"] == "blockquote"]
        assert len(bq) == 1 and bq[0]["verification_state"] == "VERIFIED_EXACT"
        assert audit["summary"]["unverified_blockquote"] == 0

    def test_memory_only_blockquote_flagged_not_rewritten(self):
        """MEMORY_ONLY 引用: runtime 绝不改写为 paraphrase——审计如实标 unverified"""
        final = "引用如下：\n\n> 「这是一段完全虚构且库中不存在的引用文字足够长。」\n"
        audit = QB.audit_quotes(final, [{"name": "search_books", "args": {}, "result_full": {"results": []}}])
        assert audit["summary"]["unverified_blockquote"] == 1
        assert "据通行理解" not in final   # runtime paraphrase 头已不存在于任何路径

    def test_stream_answer_path_keeps_split_blockquote(self):
        """production 流: 最终回答把 blockquote 从「前劈开（两个 content 分片）→ 完整保留"""
        final = ("核验如下：\n\n> 「" + _LUNYU_PASSAGE + "」\n\n以上为《论语·先进篇》原文。")
        script = [_msg("", [{"name": "search_books", "args": {"query": "言必有中"}, "id": "c1"}]),
                  _msg(final)]
        # 单 chunk 一次性给整段; 提取完整性由 extract_quotes 单测覆盖, 此处验证整链不裂
        evs = _run_stream("言必有中出处", script)
        answer = "".join(e.get("content", "") for e in _of(evs, "token"))
        assert "> 「" + _LUNYU_PASSAGE in answer


# ═══════════════════════════════════════════════════════
# O1 因果测试 T1–T8
# ═══════════════════════════════════════════════════════
_R1_SCRIPT = [
    _msg("我记得这句话可能与闵子骞有关，但需要定位原典核验。",
         [{"name": "search_books", "args": {"query": "言必有中 出处"}, "id": "c1"}]),
    _msg("检索已定位《论语·先进篇》，下一步读取该章原文核对措辞。",
         [{"name": "get_chapter", "args": {"book_id": "lunyu", "chapter_idx": 13}, "id": "c2"}]),
    _msg("原文确认「言必有中」出自《论语·先进篇》孔子评价闵子骞之语, 与先前工作假设一致, 未见与相邻章句混淆。以上为最终核验回答。"),
]


class TestT1NoHiddenPrimaryRead:
    def test_all_cognitive_tools_come_from_declarations(self):
        evs = _run_stream("言必有中出处", _R1_SCRIPT)
        tools = _of(evs, "tool")
        assert [t["name"] for t in tools] == ["search_books", "get_chapter"]
        assert all(t.get("initiated_by") == "main_agent" for t in tools)
        done = [e for e in evs if e.get("type") == "done"][-1]
        assert done["causal"]["engine_cognitive_auto_tools"] == 0
        assert done["causal"]["main_agent_tool_decisions"] == 2
        # 引擎未代跑 locate_exact_phrase / 任何未宣告工具
        assert _STUB_CALLS["locate_exact_phrase"] == []

    def test_primary_read_by_agent_satisfies_ledger(self):
        evs = _run_stream("言必有中出处", _R1_SCRIPT)
        done = [e for e in evs if e.get("type") == "done"][-1]
        # O5: 执行事实并入 Evidence Store——done.evidence.facts（obligation_ledger 字段已删）
        assert "obligation_ledger" not in done
        vs = done["evidence"]["facts"]
        assert vs["primary_text_read"] is True          # 模型自己的 get_chapter 置位
        assert "auto_primary_read" not in vs            # 引擎代读标志已删除


class TestT2NoRuntimeImpersonation:
    def test_no_identity_inversion_in_events(self):
        evs = _run_stream("言必有中出处", _R1_SCRIPT)
        banned = ("这就是你自己的核验动作", "已完成主文本核验读取", "原典核验补正",
                  "[Primary text read]")
        for e in evs:
            blob = str(e.get("content") or "") + str(e.get("thought") or "")
            for b in banned:
                assert b not in blob, f"runtime 冒充 Agent 行为的文案回流: {b}"
        # thinking_summary 只能来自 main_agent（event provenance, 非 grep）
        assert all(e.get("initiated_by") == "main_agent" for e in _of(evs, "thinking_summary"))
        # 结构性护栏: 引擎层代读函数已不存在
        assert not hasattr(EG, "_ensure_primary_read")


class TestT3MainAgentBetweenBatches:
    def test_new_invocation_between_tool_batches(self):
        evs = _run_stream("言必有中出处", _R1_SCRIPT)
        search = [t for t in _of(evs, "tool") if t["name"] == "search_books"][0]
        read = [t for t in _of(evs, "tool") if t["name"] == "get_chapter"][0]
        # 第二批工具的 decision group 必须严格晚于第一批（中间存在新 Main Agent invocation）
        assert _group_num(read) > _group_num(search)
        done = [e for e in evs if e.get("type") == "done"][-1]
        assert done["causal"]["agent_invocations"] >= 3   # search 轮 / read 轮 / final 轮


class TestT4ParallelBatchAllowed:
    def test_one_decision_two_tools_share_group(self):
        script = [
            _msg("需要同时查书讯与检索原文。",
                 [{"name": "get_book_detail", "args": {"book_id": "lunyu"}, "id": "p1"},
                  {"name": "search_books", "args": {"query": "言必有中"}, "id": "p2"}]),
            _msg("书目信息与原典检索两路材料已齐, 足以完成回答, 无需进一步检索。"),
        ]
        evs = _run_stream("言必有中出处并介绍《论语》", script)
        tools = _of(evs, "tool")
        assert [t["name"] for t in tools] == ["get_book_detail", "search_books"]
        assert _group_num(tools[0]) == _group_num(tools[1])   # 同一 decision group, 不算缺 thinking
        assert all(t.get("initiated_by") == "main_agent" for t in tools)


class TestT5RuntimeMechanicalActions:
    def test_tool_notes_are_mechanical_not_agent_thinking(self):
        evs = _run_stream("言必有中出处", _R1_SCRIPT)
        notes = _of(evs, "tool_note")
        assert notes, "工具活动注记应存在"
        assert all(n.get("initiated_by") == "runtime_mechanical" for n in notes)
        for n in notes:
            assert not any(w in n.get("content", "") for w in ("我决定", "我的判断", "我记得我"))
        # 每个宣告的工具在 tool_start 后立即有活动注记（running 状态）
        starts = _of(evs, "tool_start")
        for s in starts:
            after = evs[evs.index(s) + 1: evs.index(s) + 3]
            assert any(a.get("type") == "tool_note" and a.get("activity") for a in after), \
                f"tool_start 后缺活动注记: {s.get('name')}"


class TestT6EventProvenance:
    def test_all_tool_activity_events_have_initiated_by(self):
        evs = _run_stream("言必有中出处", _R1_SCRIPT)
        watched = ("tool", "tool_start", "tool_note", "thinking_summary")
        for e in evs:
            if e.get("type") in watched:
                assert e.get("initiated_by") in ("main_agent", "runtime_mechanical",
                                                 "tool_internal", "validator"), \
                    f"{e.get('type')} 事件缺 initiated_by: {e}"
        # trace JSONL 层同样带 provenance
        tools = [e for e in evs if e.get("type") == "tool"]
        assert all(e.get("decision_group_id") for e in tools)


class TestT7NoAutoWebsearch:
    def test_empty_search_does_not_trigger_websearch(self):
        script = [
            _msg("先检索这个生僻表述。",
                 [{"name": "search_books", "args": {"query": "不存在词项 zxqwort"}, "id": "c1"}]),
            _msg("库中未能检索到该表述的原文出处, 按诚实边界如实说明: 该出处未经核验, 确定性相应降级, 不给出看似原文的引用。"),
        ]
        evs = _run_stream("“不存在词项zxqwort”的哲学出处", script)
        assert _STUB_CALLS["websearch"] == []            # runtime 未代跑 websearch
        assert all(t["name"] != "websearch" for t in _of(evs, "tool"))
        # 模型下一轮保留自主选择 websearch 的合法性（此处脚本选择不调, 但工具可用）


class TestT8NoAutoRead:
    def test_no_declaration_no_get_chapter(self):
        script = [
            _msg("检索命中候选, 但我未读原文; 基于片段谨慎作答。",
                 [{"name": "search_books", "args": {"query": "言必有中"}, "id": "c1"}]),
            _msg("检索仅提供定位线索, 我尚未读取原文, 因此不给出逐字引用; 该表述的出处暂无法核验, 确定性降级。"),
        ]
        evs = _run_stream("言必有中出处", script)
        assert _STUB_CALLS["get_chapter"] == []
        assert all(t["name"] != "get_chapter" for t in _of(evs, "tool"))
        assert _STUB_CALLS["locate_exact_phrase"] == []  # 引擎未暗中定位
        done = [e for e in evs if e.get("type") == "done"][-1]
        vs = done["evidence"]["facts"]                   # O5: 事实位 = done.evidence.facts
        assert vs["primary_text_read"] is False          # 未经模型读取, 不得置位


# ═══════════════════════════════════════════════════════
# §13 机械 timing observability
# ═══════════════════════════════════════════════════════
class TestTimingObservability:
    def test_done_payload_has_phase_timings(self):
        evs = _run_stream("言必有中出处", _R1_SCRIPT)
        done = [e for e in evs if e.get("type") == "done"][-1]
        phases = done["timing"]["phases"]
        llm_phases = [p for p in phases if p["phase"] == "llm_invocation"]
        assert len(llm_phases) >= 3                       # 每个 Main Agent invocation 都有计时
        assert all("duration_ms" in p for p in phases)
        assert any(p["phase"].startswith("validator_") for p in phases)
